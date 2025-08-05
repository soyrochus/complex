"""Parser for the Complex DSL.

This module provides the ComplexParser class that uses Lark to parse
Complex DSL scripts into Abstract Syntax Trees.
"""

import os
from typing import Any, Union, List, Optional
from pathlib import Path

try:
    from lark import Lark, Transformer, Tree, Token
    from lark.exceptions import LarkError, UnexpectedInput
except ImportError:
    # Handle case where lark is not installed
    Lark = None
    Transformer = None
    Tree = None
    Token = None
    LarkError = Exception
    UnexpectedInput = Exception

from .errors import ParseError
from .models import (
    Program, Statement, EntityDef, RelationshipDef, InsertEntity, ConnectRel,
    UpdateStmt, DeleteStmt, QueryStmt, DataType, FieldDecl, Multiplicity,
    Assignment, Literal, Condition, PropertyCondition, TargetRef,
    NodePattern, EdgePattern, Pattern, ReturnItem
)


class ComplexTransformer(Transformer):
    """Transformer to convert Lark parse tree to AST models."""
    
    def start(self, statements: List[Statement]) -> Program:
        """Transform the start rule to Program."""
        return Program(statements=statements)
    
    def statement(self, stmt_list: List[Statement]) -> Statement:
        """Transform statement rule."""
        return stmt_list[0]
    
    def entity_def(self, items: List[Any]) -> EntityDef:
        """Transform entity definition."""
        name = str(items[0])
        fields = items[1]
        extends = str(items[2]) if len(items) > 2 and items[2] is not None else None
        return EntityDef(name=name, fields=fields, extends=extends)
    
    def field_list(self, fields: List[FieldDecl]) -> List[FieldDecl]:
        """Transform field list."""
        return fields
    
    def field_decl(self, items: List[Any]) -> FieldDecl:
        """Transform field declaration."""
        name = str(items[0])
        data_type = items[1]
        return FieldDecl(name=name, data_type=data_type)
    
    def data_type(self, items: List[Any]) -> DataType:
        """Transform data type."""
        if len(items) == 1:
            # Simple type or reference
            if isinstance(items[0], str):
                return DataType(name=items[0], is_array=False)
            else:
                return items[0]  # Already a DataType
        return DataType(name=str(items[0]), is_array=False)
    
    def array_ref(self, items: List[Any]) -> DataType:
        """Transform array reference type."""
        return DataType(name=str(items[0]), is_array=True)
    
    def primitive_type(self, items: List[Any]) -> str:
        """Transform primitive type."""
        if items:
            return str(items[0])
        return "STRING"  # Default fallback
    
    def relationship_def(self, items: List[Any]) -> RelationshipDef:
        """Transform relationship definition."""
        name = str(items[0])
        from_entity = str(items[1])
        from_mult = items[2] if isinstance(items[2], Multiplicity) else Multiplicity(value="1")
        to_entity = str(items[3])
        to_mult = items[4] if isinstance(items[4], Multiplicity) else Multiplicity(value="1")
        
        # Find fields - could be None or a field_block (list of FieldDecl)
        fields = []
        for item in items[5:]:
            if isinstance(item, list) and item:
                # Flatten if it's a nested list
                for field in item:
                    if isinstance(field, FieldDecl):
                        fields.append(field)
                    elif isinstance(field, list):
                        fields.extend(field)
            elif isinstance(item, FieldDecl):
                fields.append(item)
        
        return RelationshipDef(
            name=name,
            from_entity=from_entity,
            from_mult=from_mult,
            to_entity=to_entity,
            to_mult=to_mult,
            fields=fields
        )
    
    def properties(self, items: List[Any]) -> List[Assignment]:
        """Transform properties."""
        return items

    def field_block(self, items: List[Any]) -> List[FieldDecl]:
        """Transform field block."""
        # Flatten the list if needed
        fields = []
        for item in items:
            if isinstance(item, list):
                fields.extend(item)
            elif isinstance(item, FieldDecl):
                fields.append(item)
        return fields

    def mult(self, items: List[Any]) -> Multiplicity:
        """Transform multiplicity."""
        if not items:
            return Multiplicity(value="1")  # default multiplicity
        return Multiplicity(value=str(items[0]))
    
    def insert_entity(self, items: List[Any]) -> InsertEntity:
        """Transform INSERT statement."""
        entity_type = str(items[0])
        assignments = items[1]
        alias = items[2] if len(items) > 2 and items[2] is not None else None
        return InsertEntity(entity_type=entity_type, assignments=assignments, alias=alias)
    
    def alias_clause(self, items: List[Any]) -> str:
        """Transform alias clause."""
        return str(items[0])
    
    def alias(self, items: List[Any]) -> str:
        """Transform alias."""
        return str(items[0])
    
    def assign_list(self, assignments: List[Assignment]) -> List[Assignment]:
        """Transform assignment list."""
        return assignments
    
    def assign(self, items: List[Any]) -> Assignment:
        """Transform assignment."""
        field = str(items[0])
        value = items[1]
        return Assignment(field=field, value=value)
    
    def literal_or_ref(self, items: List[Any]) -> Any:
        """Transform literal or reference."""
        return items[0]
    
    def literal(self, items: List[Any]) -> Literal:
        """Transform literal value."""
        if not items:
            return Literal(value=None, type="null")
        
        token = items[0]
        token_str = str(token)
        
        if hasattr(token, 'type'):
            token_type = token.type
        else:
            # Try to infer type from string content
            if token_str.startswith('"') and token_str.endswith('"'):
                token_type = "STRING"
            elif token_str in ("TRUE", "FALSE"):
                token_type = "BOOL"
            elif token_str == "NULL":
                token_type = "NULL"
            elif "." in token_str:
                token_type = "SIGNED_NUMBER"
            else:
                token_type = "SIGNED_NUMBER"
        
        if token_type == "STRING":
            # Remove quotes
            value = token_str[1:-1] if token_str.startswith('"') else token_str
            return Literal(value=value, type="string")
        elif token_type == "SIGNED_NUMBER":
            if "." in token_str:
                return Literal(value=float(token_str), type="number")
            else:
                return Literal(value=int(token_str), type="number")
        elif token_str == "TRUE":
            return Literal(value=True, type="boolean")
        elif token_str == "FALSE":
            return Literal(value=False, type="boolean")
        elif token_str == "NULL":
            return Literal(value=None, type="null")
        else:
            return Literal(value=token_str, type="string")
    
    def alias_or_id(self, items: List[Any]) -> Union[str, int]:
        """Transform alias or ID."""
        if not items:
            return ""
        
        item = items[0]
        if hasattr(item, 'type') and item.type == "SIGNED_NUMBER":
            return int(str(item))
        return str(item)
    
    def connect_rel(self, items: List[Any]) -> ConnectRel:
        """Transform CONNECT statement."""
        from_ref = items[0]
        relationship = str(items[1])
        to_ref = items[2]
        
        # Find properties - could be None or transformed properties
        properties = []
        for item in items[3:]:
            if isinstance(item, list):
                properties = item
            elif hasattr(item, 'children'):  # Tree object
                # This is likely a properties block that wasn't transformed
                properties = []
        
        return ConnectRel(
            from_ref=from_ref,
            relationship=relationship,
            to_ref=to_ref,
            properties=properties
        )
    
    def update_stmt(self, items: List[Any]) -> UpdateStmt:
        """Transform UPDATE statement."""
        target = items[0]
        assignments = items[1]
        return UpdateStmt(target=target, assignments=assignments)
    
    def delete_stmt(self, items: List[Any]) -> DeleteStmt:
        """Transform DELETE statement."""
        target = items[0]
        return DeleteStmt(target=target)
    
    def target_ref(self, items: List[Any]) -> TargetRef:
        """Transform target reference."""
        if len(items) == 1:
            # Simple alias or ID
            ref = items[0]
            if isinstance(ref, int):
                return TargetRef(type="id", value=ref)
            else:
                return TargetRef(type="alias", value=ref)
        else:
            # Pattern with condition
            entity_type = str(items[0])
            condition = items[1]
            return TargetRef(
                type="pattern",
                value="",
                entity_type=entity_type,
                condition=condition
            )
    
    def condition(self, items: List[Any]) -> Condition:
        """Transform condition."""
        conditions = []
        operators = []
        
        conditions.append(items[0])
        for i in range(1, len(items), 2):
            operators.append(str(items[i]))
            conditions.append(items[i + 1])
        
        return Condition(conditions=conditions, operators=operators)
    
    def prop_eq(self, items: List[Any]) -> PropertyCondition:
        """Transform property equality."""
        prop = str(items[0])
        value = items[1]
        return PropertyCondition(property=prop, value=value)
    
    def query_stmt(self, items: List[Any]) -> QueryStmt:
        """Transform MATCH/RETURN statement."""
        pattern = items[0]
        where = None
        return_items = []
        
        for item in items[1:]:
            if isinstance(item, Condition):
                where = item
            elif isinstance(item, list):
                return_items = item
        
        return QueryStmt(pattern=pattern, where=where, return_items=return_items)
    
    def pattern(self, items: List[Any]) -> Pattern:
        """Transform pattern."""
        nodes = []
        edges = []
        
        # Filter out only properly transformed items
        valid_items = []
        for item in items:
            if isinstance(item, (NodePattern, EdgePattern)):
                valid_items.append(item)
            elif hasattr(item, 'children'):  # Tree object - skip for now
                pass
        
        # First valid item should be a node
        if valid_items and isinstance(valid_items[0], NodePattern):
            nodes.append(valid_items[0])
            
        # Remaining valid items alternate between edges and nodes
        for i in range(1, len(valid_items), 2):
            if i < len(valid_items) and isinstance(valid_items[i], EdgePattern):
                edges.append(valid_items[i])
            if i + 1 < len(valid_items) and isinstance(valid_items[i + 1], NodePattern):
                nodes.append(valid_items[i + 1])
        
        return Pattern(nodes=nodes, edges=edges)
    
    def node_pat(self, items: List[Any]) -> NodePattern:
        """Transform node pattern."""
        alias = None
        entity_type = ""
        condition = None
        
        for item in items:
            if isinstance(item, str):
                if not entity_type:
                    entity_type = item
                else:
                    alias = entity_type
                    entity_type = item
            elif isinstance(item, Condition):
                condition = item
        
        return NodePattern(alias=alias, entity_type=entity_type, condition=condition)
    
    def edge_pat(self, items: List[Any]) -> EdgePattern:
        """Transform edge pattern."""
        relationship = None
        condition = None
        direction = "bidirectional"
        
        # First item should be edge_spec, second should be direction
        if items:
            edge_spec = items[0]
            if isinstance(edge_spec, list):
                for spec_item in edge_spec:
                    if isinstance(spec_item, str):
                        relationship = spec_item
                    else:
                        condition = spec_item
            
            if len(items) > 1:
                direction = str(items[1]) if items[1] else "bidirectional"
        
        return EdgePattern(relationship=relationship, condition=condition, direction=direction)
    
    def edge_node_sequence(self, items: List[Any]) -> List[Any]:
        """Transform edge-node sequence."""
        return items  # Return both edge and node

    def edge_spec(self, items: List[Any]) -> List[Any]:
        """Transform edge specification."""
        return items  # Pass through edge type and condition

    def edge_type(self, items: List[Any]) -> str:
        """Transform edge type."""
        return str(items[0]) if items else ""

    def edge_condition(self, items: List[Any]) -> Any:
        """Transform edge condition."""
        return items[0] if items else None

    def direction(self, items: List[Any]) -> str:
        """Transform direction."""
        if not items:
            return "bidirectional"  # default direction
        return str(items[0])
    
    def return_list(self, items: List[ReturnItem]) -> List[ReturnItem]:
        """Transform return list."""
        return items
    
    def return_item(self, items: List[Any]) -> ReturnItem:
        """Transform return item."""
        alias = str(items[0])
        prop = str(items[1]) if len(items) > 1 else None
        return ReturnItem(alias=alias, property=prop)


class ComplexParser:
    """Parser for Complex DSL scripts."""
    
    def __init__(self) -> None:
        """Initialize the parser with the grammar."""
        if Lark is None:
            raise ImportError("lark-parser is required but not installed")
        
        # Load grammar from file
        grammar_path = Path(__file__).parent / "grammar.lark"
        if not grammar_path.exists():
            raise FileNotFoundError(f"Grammar file not found: {grammar_path}")
        
        with open(grammar_path, "r", encoding="utf-8") as f:
            grammar = f.read()
        
        self.parser = Lark(
            grammar,
            parser="earley",
            maybe_placeholders=True
        )
        self.transformer = ComplexTransformer()
    
    def parse(self, script: str) -> Program:
        """Parse a Complex DSL script into an AST.
        
        Args:
            script: The DSL script to parse
            
        Returns:
            Program AST representing the parsed script
            
        Raises:
            ParseError: If parsing fails
        """
        try:
            tree = self.parser.parse(script)
            result = self.transformer.transform(tree)
            
            if isinstance(result, Program):
                return result
            else:
                raise ParseError("Unexpected parse result type")
        
        except (LarkError, UnexpectedInput) as e:
            # Try to extract line/column information
            line = None
            column = None
            
            if hasattr(e, "line"):
                line = e.line
            if hasattr(e, "column"):
                column = e.column
            
            raise ParseError(
                message=str(e),
                line=line,
                column=column,
                source=script
            ) from e
