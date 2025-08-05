"""Database helper for the Complex DSL library.

This module provides a thin wrapper around psycopg2 with connection pooling
and convenience methods for executing queries.
"""

import threading
from typing import List, Dict, Any, Optional, Iterator, Tuple, Union
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2 import pool, sql
    from psycopg2.extras import RealDictCursor
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    # Handle case where psycopg2 is not installed
    psycopg2 = None
    pool = None
    sql = None
    RealDictCursor = None
    ISOLATION_LEVEL_AUTOCOMMIT = None

from .env import get_connection_params, get_graph_name
from .errors import ConnectionError as ComplexConnectionError, map_db_error


class DatabaseManager:
    """Thread-safe database connection manager with pooling."""
    
    def __init__(self, min_connections: int = 1, max_connections: int = 10) -> None:
        """Initialize the database manager.
        
        Args:
            min_connections: Minimum number of connections in pool
            max_connections: Maximum number of connections in pool
        """
        if psycopg2 is None:
            raise ImportError("psycopg2-binary is required but not installed")
        
        self._pool: Optional[pool.SimpleConnectionPool] = None
        self._lock = threading.Lock()
        self._min_connections = min_connections
        self._max_connections = max_connections
        self._graph_name = get_graph_name()
    
    def _ensure_pool(self) -> None:
        """Ensure the connection pool is initialized."""
        if self._pool is None:
            with self._lock:
                if self._pool is None:
                    try:
                        conn_params = get_connection_params()
                        self._pool = pool.SimpleConnectionPool(
                            self._min_connections,
                            self._max_connections,
                            **conn_params
                        )
                        
                        # Test the connection and ensure AGE extension is available
                        self._test_connection()
                        
                    except Exception as e:
                        raise ComplexConnectionError(
                            f"Failed to create connection pool: {e}"
                        ) from e
    
    def _test_connection(self) -> None:
        """Test the database connection and AGE extension."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if AGE extension is installed
                cursor.execute(
                    "SELECT 1 FROM pg_extension WHERE extname = 'age'"
                )
                if not cursor.fetchone():
                    raise ComplexConnectionError(
                        "Apache AGE extension is not installed in the database"
                    )
                
                # Create graph if it doesn't exist
                cursor.execute(
                    f"SELECT 1 FROM ag_catalog.ag_graph WHERE name = %s",
                    (self._graph_name,)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        f"SELECT create_graph(%s)",
                        (self._graph_name,)
                    )
                    conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool.
        
        Yields:
            Database connection
            
        Raises:
            ComplexConnectionError: If unable to get connection
        """
        self._ensure_pool()
        
        if self._pool is None:
            raise ComplexConnectionError("Connection pool not initialized")
        
        conn = None
        try:
            conn = self._pool.getconn()
            if conn is None:
                raise ComplexConnectionError("Unable to get connection from pool")
            
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn and self._pool:
                self._pool.putconn(conn)
    
    def run(
        self,
        query: str,
        params: Tuple[Any, ...] = (),
        fetch: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """Execute a query and return results.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: Whether to fetch and return results
            
        Returns:
            List of result rows as dictionaries, or None if fetch=False
            
        Raises:
            ComplexConnectionError: If database operation fails
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    
                    if fetch:
                        results = cursor.fetchall()
                        return [dict(row) for row in results]
                    else:
                        conn.commit()
                        return None
                        
        except Exception as e:
            # Map database errors to Complex errors
            sqlstate = getattr(e, 'pgcode', None)
            error = map_db_error(sqlstate, str(e))
            raise error from e
    
    def run_cypher(
        self,
        cypher_query: str,
        params: Tuple[Any, ...] = ()
    ) -> List[Dict[str, Any]]:
        """Execute a Cypher query via Apache AGE.
        
        Args:
            cypher_query: Cypher query to execute
            params: Query parameters
            
        Returns:
            List of result rows as dictionaries
        """
        # Escape dollar signs in cypher query for PostgreSQL
        escaped_query = cypher_query.replace('$', '$$')
        
        sql_query = f"""
        SELECT * FROM cypher(%s, $${escaped_query}$$) AS (result agtype)
        """
        
        return self.run(sql_query, (self._graph_name,) + params) or []
    
    def execute_transaction(
        self,
        queries: List[Tuple[str, Tuple[Any, ...]]]
    ) -> List[Optional[List[Dict[str, Any]]]]:
        """Execute multiple queries in a transaction.
        
        Args:
            queries: List of (query, params) tuples
            
        Returns:
            List of results for each query
            
        Raises:
            ComplexConnectionError: If transaction fails
        """
        results = []
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    for query, params in queries:
                        cursor.execute(query, params)
                        
                        # Try to fetch results, but not all queries return data
                        try:
                            result = cursor.fetchall()
                            results.append([dict(row) for row in result])
                        except psycopg2.ProgrammingError:
                            # Query didn't return results (e.g., INSERT, UPDATE, DELETE)
                            results.append(None)
                    
                    conn.commit()
                    
        except Exception as e:
            sqlstate = getattr(e, 'pgcode', None)
            error = map_db_error(sqlstate, str(e))
            raise error from e
        
        return results
    
    def close(self) -> None:
        """Close all connections in the pool."""
        if self._pool:
            with self._lock:
                if self._pool:
                    self._pool.closeall()
                    self._pool = None


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None
_db_lock = threading.Lock()


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance.
    
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    
    if _db_manager is None:
        with _db_lock:
            if _db_manager is None:
                _db_manager = DatabaseManager()
    
    return _db_manager


def run(
    query: str,
    params: Tuple[Any, ...] = (),
    fetch: bool = True
) -> Optional[List[Dict[str, Any]]]:
    """Convenience function to execute a query.
    
    Args:
        query: SQL query to execute
        params: Query parameters
        fetch: Whether to fetch and return results
        
    Returns:
        List of result rows as dictionaries, or None if fetch=False
    """
    return get_db_manager().run(query, params, fetch)


def run_cypher(
    cypher_query: str,
    params: Tuple[Any, ...] = ()
) -> List[Dict[str, Any]]:
    """Convenience function to execute a Cypher query.
    
    Args:
        cypher_query: Cypher query to execute
        params: Query parameters
        
    Returns:
        List of result rows as dictionaries
    """
    return get_db_manager().run_cypher(cypher_query, params)


def close_db() -> None:
    """Close the database connection pool."""
    global _db_manager
    
    if _db_manager:
        with _db_lock:
            if _db_manager:
                _db_manager.close()
                _db_manager = None
