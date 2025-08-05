"""Environment handling for the Complex DSL library.

This module provides configuration management using python-dotenv,
loading database connection parameters and other settings from environment variables.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_env_var(key: str, default: Optional[str] = None) -> str:
    """Get environment variable with optional default value.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        
    Returns:
        Environment variable value
        
    Raises:
        ValueError: If required variable is not found and no default provided
    """
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Required environment variable {key} not found")
    return value


def get_connection_params() -> Dict[str, Any]:
    """Get database connection parameters from environment variables.
    
    Returns:
        Dictionary ready for psycopg2.connect(**params)
        
    Environment variables (with defaults for local development):
        COMPLEX_DB_HOST (default: localhost)
        COMPLEX_DB_PORT (default: 5432)
        COMPLEX_DB_NAME (default: postgres)
        COMPLEX_DB_USER (default: postgres)
        COMPLEX_DB_PASSWORD (default: password)
    """
    return {
        "host": get_env_var("COMPLEX_DB_HOST", "localhost"),
        "port": int(get_env_var("COMPLEX_DB_PORT", "5432")),
        "database": get_env_var("COMPLEX_DB_NAME", "postgres"),
        "user": get_env_var("COMPLEX_DB_USER", "postgres"),
        "password": get_env_var("COMPLEX_DB_PASSWORD", "password"),
    }


def get_graph_name() -> str:
    """Get the Apache AGE graph name from environment.
    
    Returns:
        Graph name to use for AGE operations
    """
    return get_env_var("COMPLEX_GRAPH_NAME", "complex_graph")


def get_edge_references_enabled() -> bool:
    """Check if edge-mapped references are enabled.
    
    Returns:
        True if edge references are enabled, False for scalar-ID mode
    """
    return get_env_var("EDGE_REFERENCES", "true").lower() in ("true", "1", "yes", "on")
