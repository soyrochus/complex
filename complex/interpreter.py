"""Interpreter for the Complex DSL.

This module provides the ComplexInterpreter class that executes
Complex DSL statements against a PostgreSQL database with Apache AGE.
"""

import json
from typing import List, Dict, Any, Optional, Union, Tuple
from uuid import uuid4

from .parser import ComplexParser
from .models import (
    Program, Statement, EntityDef, RelationshipDef, InsertEntity, ConnectRel,
    UpdateStmt, DeleteStmt, QueryStmt, Assignment, Literal, Condition,
    PropertyCondition, TargetRef, Pattern, NodePattern, EdgePattern, ReturnItem
)
from .db import get_db_manager, run_cypher, run
from .env import get_edge_references_enabled
from .errors import SemanticError, ExecutionError


class ComplexInterpreter:
    """Interpreter for Complex DSL scripts."""
    
    def __init__(self) -> None:
        """Initialize the interpreter."""
        self.parser = ComplexParser()
        self.db = get_db_manager()
        self.edge_references = get_edge_references_enabled()
        
        # Track entity and relationship schemas
        self.entities: Dict[str, EntityDef] = {}
        self.relationships: Dict[str, RelationshipDef] = {}
        
        # Track aliases to IDs for current script execution
        self.aliases: Dict[str, int] = {}
    
    def execute(self, script: str) -> List[Dict[str, Any]]:
        """Execute a Complex DSL script.
        
        Args:
            script: The DSL script to execute
            
        Returns:
            List of result dictionaries from query statements
            
        Raises:
            ParseError: If script parsing fails
            SemanticError: If semantic validation fails
            ExecutionError: If execution fails
        """
        # Parse the script
        program = self.parser.parse(script)
        
        # Reset aliases for this execution
        self.aliases.clear()
        
        results = []
        
        try:
            # Execute each statement
            for statement in program.statements:
                result = self._execute_statement(statement)
                if result is not None:
                    results.extend(result)
            
            return results
            
        except Exception as e:
            if not isinstance(e, (SemanticError, ExecutionError)):
                raise ExecutionError(f"Unexpected execution error: {e}") from e
            raise
    
    def _execute_statement(self, statement: Statement) -> Optional[List[Dict[str, Any]]]:
        """Execute a single statement.
        
        Args:
            statement: Statement to execute
            
        Returns:
            Query results if statement returns data, None otherwise
        """
        if isinstance(statement, EntityDef):
            return self._execute_entity_def(statement)
        elif isinstance(statement, RelationshipDef):
            return self._execute_relationship_def(statement)
        elif isinstance(statement, InsertEntity):
            return self._execute_insert_entity(statement)
        elif isinstance(statement, ConnectRel):
            return self._execute_connect_rel(statement)
        elif isinstance(statement, UpdateStmt):
            return self._execute_update_stmt(statement)
        elif isinstance(statement, DeleteStmt):
            return self._execute_delete_stmt(statement)
        elif isinstance(statement, QueryStmt):
            return self._execute_query_stmt(statement)
        else:
            raise SemanticError(f"Unknown statement type: {type(statement)}")
    
    def _execute_entity_def(self, statement: EntityDef) -> None:
        """Execute an ENTITY definition."""
        # Store entity schema for validation
        self.entities[statement.name] = statement
        
        # Create vertex label in AGE (if not exists)
        cypher_query = f"CREATE (:{statement.name})"
        try:
            run_cypher(cypher_query)
        except ExecutionError:
            # Label might already exist, which is fine
            pass
        
        return None
    
    def _execute_relationship_def(self, statement: RelationshipDef) -> None:
        """Execute a RELATIONSHIP definition."""
        # Store relationship schema for validation
        self.relationships[statement.name] = statement
        
        # AGE doesn't require explicit relationship type creation
        return None
    
    def _execute_insert_entity(self, statement: InsertEntity) -> None:
        """Execute an INSERT statement."""
        # Validate entity type exists
        if statement.entity_type not in self.entities:
            raise SemanticError(f"Unknown entity type: {statement.entity_type}")
        
        entity_def = self.entities[statement.entity_type]
        
        # Build properties JSON
        properties = {}
        for assignment in statement.assignments:
            value = self._resolve_assignment_value(assignment, entity_def)
            properties[assignment.field] = value
        
        # Generate unique ID
        vertex_id = str(uuid4())
        properties['id'] = vertex_id
        
        # Create Cypher query
        props_json = json.dumps(properties)
        cypher_query = f"CREATE (n:{statement.entity_type} {props_json}) RETURN id(n)"
        
        result = run_cypher(cypher_query)
        if result:
            vertex_db_id = result[0].get('id(n)', result[0].get('result'))
            
            # Store alias mapping if provided
            if statement.alias:
                self.aliases[statement.alias] = vertex_db_id
        
        return None
    
    def _execute_connect_rel(self, statement: ConnectRel) -> None:
        """Execute a CONNECT statement."""
        # Validate relationship type exists
        if statement.relationship not in self.relationships:
            raise SemanticError(f"Unknown relationship type: {statement.relationship}")
        
        # Resolve source and target references
        from_id = self._resolve_reference(statement.from_ref)
        to_id = self._resolve_reference(statement.to_ref)
        
        # Build relationship properties
        properties = {}
        for assignment in statement.properties:
            # For relationships, we don't have a specific entity def to validate against
            value = self._resolve_literal_value(assignment.value)
            properties[assignment.field] = value
        
        # Create Cypher query
        if properties:
            props_json = json.dumps(properties)
            cypher_query = f"""
            MATCH (a), (b) 
            WHERE id(a) = {from_id} AND id(b) = {to_id}
            CREATE (a)-[r:{statement.relationship} {props_json}]->(b)
            RETURN r
            """
        else:
            cypher_query = f"""
            MATCH (a), (b) 
            WHERE id(a) = {from_id} AND id(b) = {to_id}
            CREATE (a)-[r:{statement.relationship}]->(b)
            RETURN r
            """
        
        run_cypher(cypher_query)
        return None
    
    def _execute_update_stmt(self, statement: UpdateStmt) -> None:
        """Execute an UPDATE statement."""
        # Build SET clause
        set_clauses = []
        for assignment in statement.assignments:
            value = self._resolve_literal_value(assignment.value)
            if isinstance(value, str):
                set_clauses.append(f"n.{assignment.field} = '{value}'")
            else:
                set_clauses.append(f"n.{assignment.field} = {json.dumps(value)}")
        
        set_clause = ", ".join(set_clauses)
        
        # Build WHERE clause based on target type
        if statement.target.type == "alias":
            vertex_id = self.aliases.get(statement.target.value)
            if vertex_id is None:
                raise SemanticError(f"Unknown alias: {statement.target.value}")
            where_clause = f"id(n) = {vertex_id}"
        elif statement.target.type == "id":
            where_clause = f"id(n) = {statement.target.value}"
        elif statement.target.type == "pattern":
            where_clause = self._build_condition_clause(
                statement.target.condition, "n"
            )
        else:
            raise SemanticError(f"Invalid target type: {statement.target.type}")
        
        # Create Cypher query
        cypher_query = f"""
        MATCH (n:{statement.target.entity_type or ''})
        WHERE {where_clause}
        SET {set_clause}
        RETURN n
        """
        
        run_cypher(cypher_query)
        return None
    
    def _execute_delete_stmt(self, statement: DeleteStmt) -> None:
        """Execute a DELETE statement."""
        # Build WHERE clause based on target type
        if statement.target.type == "alias":
            vertex_id = self.aliases.get(statement.target.value)
            if vertex_id is None:
                raise SemanticError(f"Unknown alias: {statement.target.value}")
            where_clause = f"id(n) = {vertex_id}"
        elif statement.target.type == "id":
            where_clause = f"id(n) = {statement.target.value}"
        elif statement.target.type == "pattern":
            where_clause = self._build_condition_clause(
                statement.target.condition, "n"
            )
        else:
            raise SemanticError(f"Invalid target type: {statement.target.type}")
        
        # Create Cypher query
        cypher_query = f"""
        MATCH (n:{statement.target.entity_type or ''})
        WHERE {where_clause}
        DETACH DELETE n
        """
        
        run_cypher(cypher_query)
        return None
    
    def _execute_query_stmt(self, statement: QueryStmt) -> List[Dict[str, Any]]:
        """Execute a MATCH/RETURN statement."""
        # Build MATCH clause
        match_clause = self._build_match_clause(statement.pattern)
        
        # Build WHERE clause
        where_clause = ""
        if statement.where:
            where_conditions = []
            for i, condition in enumerate(statement.where.conditions):
                # Determine which node alias to use
                node_alias = "n"  # Default, should be improved
                condition_str = self._build_property_condition(condition, node_alias)
                where_conditions.append(condition_str)
            
            if where_conditions:
                where_clause = f"WHERE {' AND '.join(where_conditions)}"
        
        # Build RETURN clause
        return_clause = "RETURN *"  # Default
        if statement.return_items:
            return_items = []
            for item in statement.return_items:
                if item.property:
                    return_items.append(f"{item.alias}.{item.property}")
                else:
                    return_items.append(item.alias)
            return_clause = f"RETURN {', '.join(return_items)}"
        
        # Create Cypher query
        cypher_query = f"{match_clause} {where_clause} {return_clause}".strip()
        
        results = run_cypher(cypher_query)
        return results or []
    
    def _build_match_clause(self, pattern: Pattern) -> str:
        """Build a MATCH clause from a pattern."""
        if not pattern.nodes:
            raise SemanticError("Pattern must have at least one node")
        
        clause_parts = []
        
        # Build pattern string
        pattern_str = ""
        
        for i, node in enumerate(pattern.nodes):
            # Add node pattern
            node_str = f"({node.alias or 'n'}:{node.entity_type}"
            if node.condition:
                condition_str = self._build_condition_for_node(node.condition)
                node_str += f" {condition_str}"
            node_str += ")"
            pattern_str += node_str
            
            # Add edge pattern if not the last node
            if i < len(pattern.edges):
                edge = pattern.edges[i]
                edge_str = "-"
                if edge.relationship:
                    edge_str += f"[:{edge.relationship}"
                    if edge.condition:
                        condition_str = self._build_condition_for_node(edge.condition)
                        edge_str += f" {condition_str}"
                    edge_str += "]"
                else:
                    edge_str += "[]"
                
                if edge.direction == "->":
                    edge_str += "->"
                elif edge.direction == "<-":
                    edge_str = "<-" + edge_str[1:]
                else:
                    edge_str += "-"
                
                pattern_str += edge_str
        
        return f"MATCH {pattern_str}"
    
    def _build_condition_clause(
        self, condition: Optional[Condition], node_alias: str
    ) -> str:
        """Build a WHERE condition clause."""
        if not condition:
            return "true"
        
        condition_parts = []
        for prop_condition in condition.conditions:
            condition_str = self._build_property_condition(prop_condition, node_alias)
            condition_parts.append(condition_str)
        
        # Join with operators
        if condition.operators:
            result = condition_parts[0]
            for i, operator in enumerate(condition.operators):
                if i + 1 < len(condition_parts):
                    result += f" {operator} {condition_parts[i + 1]}"
            return result
        
        return " AND ".join(condition_parts)
    
    def _build_condition_for_node(self, condition: Condition) -> str:
        """Build a condition string for use within a node pattern."""
        conditions = []
        for prop_condition in condition.conditions:
            value = self._format_literal_for_cypher(prop_condition.value)
            conditions.append(f"{prop_condition.property}: {value}")
        
        return "{" + ", ".join(conditions) + "}"
    
    def _build_property_condition(
        self, condition: PropertyCondition, node_alias: str
    ) -> str:
        """Build a property condition string."""
        value = self._format_literal_for_cypher(condition.value)
        return f"{node_alias}.{condition.property} = {value}"
    
    def _format_literal_for_cypher(self, literal: Literal) -> str:
        """Format a literal value for Cypher query."""
        if literal.type == "string":
            return f"'{literal.value}'"
        elif literal.type == "null":
            return "null"
        elif literal.type == "boolean":
            return "true" if literal.value else "false"
        else:
            return str(literal.value)
    
    def _resolve_assignment_value(
        self, assignment: Assignment, entity_def: EntityDef
    ) -> Any:
        """Resolve the value of an assignment."""
        return self._resolve_literal_value(assignment.value)
    
    def _resolve_literal_value(self, value: Any) -> Any:
        """Resolve a literal or reference value."""
        if isinstance(value, Literal):
            return value.value
        elif isinstance(value, str):
            # Could be an alias
            if value in self.aliases:
                return self.aliases[value]
            return value
        elif isinstance(value, int):
            return value
        else:
            return value
    
    def _resolve_reference(self, ref: Union[str, int]) -> int:
        """Resolve a reference to a vertex ID."""
        if isinstance(ref, int):
            return ref
        elif isinstance(ref, str):
            if ref in self.aliases:
                return self.aliases[ref]
            else:
                raise SemanticError(f"Unknown alias: {ref}")
        else:
            raise SemanticError(f"Invalid reference type: {type(ref)}")


def create_interpreter() -> ComplexInterpreter:
    """Create a new interpreter instance.
    
    Returns:
        ComplexInterpreter instance
    """
    return ComplexInterpreter()
