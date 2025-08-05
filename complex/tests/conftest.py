"""Pytest configuration and fixtures for Complex DSL tests."""

import os
import pytest
from uuid import uuid4
from typing import Generator

from complex.env import get_connection_params, get_graph_name
from complex.db import get_db_manager, close_db
from complex.interpreter import ComplexInterpreter


@pytest.fixture(scope="session")
def test_graph_name() -> str:
    """Provide a unique graph name for testing."""
    return f"test_complex_{str(uuid4()).replace('-', '_')}"


@pytest.fixture(scope="session")
def setup_test_env(test_graph_name: str) -> Generator[str, None, None]:
    """Set up test environment variables."""
    # Store original value
    original_graph_name = os.environ.get("COMPLEX_GRAPH_NAME")
    
    # Set test graph name
    os.environ["COMPLEX_GRAPH_NAME"] = test_graph_name
    
    yield test_graph_name
    
    # Restore original value
    if original_graph_name is not None:
        os.environ["COMPLEX_GRAPH_NAME"] = original_graph_name
    elif "COMPLEX_GRAPH_NAME" in os.environ:
        del os.environ["COMPLEX_GRAPH_NAME"]


@pytest.fixture(scope="session")
def db_connection(setup_test_env: str):
    """Set up database connection for tests."""
    try:
        # Test database connectivity
        db = get_db_manager()
        
        # Ensure test graph is created
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT create_graph(%s)",
                    (setup_test_env,)
                )
                conn.commit()
        
        yield db
        
    finally:
        # Clean up test graph
        try:
            with db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT drop_graph(%s, true)",
                        (setup_test_env,)
                    )
                    conn.commit()
        except Exception:
            # Ignore cleanup errors
            pass
        
        close_db()


@pytest.fixture
def interpreter(db_connection) -> ComplexInterpreter:
    """Provide a fresh interpreter instance for each test."""
    return ComplexInterpreter()


@pytest.fixture
def sample_entities() -> str:
    """Provide sample entity definitions."""
    return """
    ENTITY Employee {
        name: STRING,
        email: STRING,
        department: STRING
    };
    
    ENTITY Document {
        title: STRING,
        content: STRING,
        author: Employee
    };
    
    ENTITY Epic {
        name: STRING,
        description: STRING
    };
    """


@pytest.fixture
def sample_relationships() -> str:
    """Provide sample relationship definitions."""
    return """
    RELATIONSHIP WORKS_ON (Employee * -> Epic *) {
        role: STRING,
        start_date: DATE
    };
    
    RELATIONSHIP IN_DOCUMENT (Employee 1 -> Document *) {
        page_number: INT
    };
    """
