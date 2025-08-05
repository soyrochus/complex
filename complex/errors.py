"""Error handling for the Complex DSL library.

This module defines the exception hierarchy and provides mapping
from PostgreSQL/AGE SQLSTATE codes to domain-specific exceptions.
"""

from typing import Optional, Any, Union, Tuple


class ComplexError(Exception):
    """Root exception for all Complex DSL errors."""
    
    def __init__(self, message: str, code: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class ParseError(ComplexError):
    """Error during DSL parsing."""
    
    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        source: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.line = line
        self.column = column
        self.source = source
    
    def __str__(self) -> str:
        if self.line is not None and self.column is not None:
            return f"Parse error at line {self.line}, column {self.column}: {self.message}"
        return f"Parse error: {self.message}"


class SemanticError(ComplexError):
    """Error in DSL semantic analysis."""
    pass


class ExecutionError(ComplexError):
    """Error during DSL execution."""
    pass


class ConnectionError(ComplexError):
    """Database connection error."""
    pass


# PostgreSQL SQLSTATE code mapping
SQLSTATE_ERROR_MAP = {
    # Connection exceptions
    "08000": ConnectionError,  # connection_exception
    "08003": ConnectionError,  # connection_does_not_exist
    "08006": ConnectionError,  # connection_failure
    
    # Data exceptions
    "22000": ExecutionError,   # data_exception
    "22001": ExecutionError,   # string_data_right_truncation
    "22003": ExecutionError,   # numeric_value_out_of_range
    "22007": ExecutionError,   # invalid_datetime_format
    "22012": ExecutionError,   # division_by_zero
    "22P02": ExecutionError,   # invalid_text_representation
    
    # Integrity constraint violations
    "23000": ExecutionError,   # integrity_constraint_violation
    "23001": ExecutionError,   # restrict_violation
    "23502": ExecutionError,   # not_null_violation
    "23503": ExecutionError,   # foreign_key_violation
    "23505": ExecutionError,   # unique_violation
    "23514": ExecutionError,   # check_violation
    
    # Invalid catalog name (database/schema doesn't exist)
    "3D000": ExecutionError,   # invalid_catalog_name
    
    # Undefined object (table, column, etc.)
    "42000": SemanticError,    # syntax_error_or_access_rule_violation
    "42601": ParseError,       # syntax_error
    "42701": SemanticError,    # duplicate_column
    "42702": SemanticError,    # ambiguous_column
    "42703": SemanticError,    # undefined_column
    "42P01": SemanticError,    # undefined_table
    "42P02": SemanticError,    # undefined_parameter
}


def map_db_error(sqlstate: Optional[str], message: str) -> ComplexError:
    """Map a PostgreSQL SQLSTATE code to an appropriate Complex exception.
    
    Args:
        sqlstate: PostgreSQL SQLSTATE code
        message: Error message
        
    Returns:
        Appropriate Complex exception instance
    """
    if sqlstate and sqlstate in SQLSTATE_ERROR_MAP:
        error_class = SQLSTATE_ERROR_MAP[sqlstate]
        return error_class(message, code=sqlstate)
    
    # Default to ExecutionError for unknown codes
    return ExecutionError(message, code=sqlstate)


def result_ok(value: Any) -> Tuple[bool, Any]:
    """Return a success result tuple.
    
    Args:
        value: The successful result value
        
    Returns:
        Tuple of (True, value)
    """
    return (True, value)


def result_error(error: Union[ComplexError, str]) -> Tuple[bool, ComplexError]:
    """Return an error result tuple.
    
    Args:
        error: The error (exception or message string)
        
    Returns:
        Tuple of (False, error)
    """
    if isinstance(error, str):
        error = ComplexError(error)
    return (False, error)
