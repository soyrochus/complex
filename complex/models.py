"""Data models for Complex DSL Abstract Syntax Tree.

This module defines Pydantic models representing the parsed AST nodes
for all Complex DSL statements and expressions.
"""

from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field


class DataType(BaseModel):
    """Represents a data type declaration."""
    name: str
    is_array: bool = False


class FieldDecl(BaseModel):
    """Represents a field declaration in an entity or relationship."""
    name: str
    data_type: DataType


class EntityDef(BaseModel):
    """Represents an ENTITY definition."""
    name: str
    fields: List[FieldDecl]
    extends: Optional[str] = None


class Multiplicity(BaseModel):
    """Represents relationship multiplicity."""
    value: str  # "1" or "*"


class RelationshipDef(BaseModel):
    """Represents a RELATIONSHIP definition."""
    name: str
    from_entity: str
    to_entity: str
    from_mult: Optional[Multiplicity] = None
    to_mult: Optional[Multiplicity] = None
    fields: List[FieldDecl] = Field(default_factory=list)


class Literal(BaseModel):
    """Represents a literal value."""
    value: Union[str, int, float, bool, None]
    type: str  # "string", "number", "boolean", "null"


class Assignment(BaseModel):
    """Represents a field assignment."""
    field: str
    value: Union[Literal, str, int, List[Literal]]  # literal, alias/id, or array literal


class InsertEntity(BaseModel):
    """Represents an INSERT statement."""
    entity_type: str
    assignments: List[Assignment]
    alias: Optional[str] = None


class ConnectRel(BaseModel):
    """Represents a CONNECT statement."""
    from_ref: Union[str, int]  # alias or id
    relationship: str
    to_ref: Union[str, int]  # alias or id
    properties: List[Assignment] = Field(default_factory=list)


class PropertyCondition(BaseModel):
    """Represents a property equality condition."""
    property: str
    value: Literal


class Condition(BaseModel):
    """Represents a complex condition with AND/OR."""
    conditions: List[PropertyCondition]
    operators: List[str] = Field(default_factory=list)  # "AND" or "OR"


class TargetRef(BaseModel):
    """Represents a target reference for UPDATE/DELETE."""
    type: str  # "alias", "id", or "pattern"
    value: Union[str, int]  # alias/id value
    entity_type: Optional[str] = None  # for pattern type
    condition: Optional[Condition] = None  # for pattern type


class UpdateStmt(BaseModel):
    """Represents an UPDATE statement."""
    target: TargetRef
    assignments: List[Assignment]


class DeleteStmt(BaseModel):
    """Represents a DELETE statement."""
    target: TargetRef


class NodePattern(BaseModel):
    """Represents a node pattern in MATCH."""
    alias: Optional[str] = None
    entity_type: str
    condition: Optional[Condition] = None


class EdgePattern(BaseModel):
    """Represents an edge pattern in MATCH."""
    relationship: Optional[str] = None
    condition: Optional[Condition] = None
    direction: str  # "->", "<-", or "-"


class Pattern(BaseModel):
    """Represents a complete pattern in MATCH."""
    nodes: List[NodePattern]
    edges: List[EdgePattern] = Field(default_factory=list)


class ReturnItem(BaseModel):
    """Represents a return item in RETURN clause."""
    alias: str
    property: Optional[str] = None


class QueryStmt(BaseModel):
    """Represents a MATCH/RETURN statement."""
    pattern: Pattern
    where: Optional[Condition] = None
    return_items: List[ReturnItem] = Field(default_factory=list)


# Union type for all statement types
Statement = Union[
    EntityDef,
    RelationshipDef,
    InsertEntity,
    ConnectRel,
    UpdateStmt,
    DeleteStmt,
    QueryStmt,
]


class Program(BaseModel):
    """Represents the complete parsed program."""
    statements: List[Statement]


def statement_type(stmt: Statement) -> str:
    """Get the statement type as a string.
    
    Args:
        stmt: Statement instance
        
    Returns:
        Statement type name
    """
    return type(stmt).__name__
