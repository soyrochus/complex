"""Complex DSL - A domain-specific language for graph data manipulation.

This library provides parsing, interpretation, and execution of the Complex DSL
against PostgreSQL databases with the Apache AGE extension.
"""

from .parser import ComplexParser
from .interpreter import ComplexInterpreter, create_interpreter
from .errors import ComplexError, ParseError, SemanticError, ExecutionError, ConnectionError
from .env import get_connection_params, get_graph_name, get_edge_references_enabled
from .db import run, run_cypher, close_db

__version__ = "0.1.0"
__author__ = "Complex Library"

__all__ = [
    # Core classes
    "ComplexParser",
    "ComplexInterpreter",
    "create_interpreter",
    
    # Errors
    "ComplexError",
    "ParseError", 
    "SemanticError",
    "ExecutionError",
    "ConnectionError",
    
    # Environment
    "get_connection_params",
    "get_graph_name", 
    "get_edge_references_enabled",
    
    # Database
    "run",
    "run_cypher",
    "close_db",
]