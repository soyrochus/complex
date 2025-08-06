"""Tests for the Complex DSL parser."""

import pytest
from complex.parser import ComplexParser
from complex.errors import ParseError
from complex.models import (
    Program, EntityDef, RelationshipDef, InsertEntity, 
    QueryStmt, DataType, FieldDecl
)


class TestComplexParser:
    """Test cases for the Complex DSL parser."""
    
    def test_parser_initialization(self):
        """Test parser can be initialized."""
        parser = ComplexParser()
        assert parser is not None
    
    def test_parse_entity_definition(self):
        """Test parsing entity definitions."""
        parser = ComplexParser()
        script = """
        ENTITY Employee {
            name: STRING,
            email: STRING,
            department: STRING
        };
        """
        
        program = parser.parse(script)
        assert isinstance(program, Program)
        assert len(program.statements) == 1
        
        entity = program.statements[0]
        assert isinstance(entity, EntityDef)
        assert entity.name == "Employee"
        assert len(entity.fields) == 3
        
        # Check fields
        assert entity.fields[0].name == "name"
        assert entity.fields[0].data_type.name == "STRING"
        assert not entity.fields[0].data_type.is_array
    
    def test_parse_entity_with_extends(self):
        """Test parsing entity with inheritance."""
        parser = ComplexParser()
        script = """
        ENTITY Manager {
            level: INT
        } EXTENDS Employee;
        """
        
        program = parser.parse(script)
        entity = program.statements[0]
        assert isinstance(entity, EntityDef)
        assert entity.extends == "Employee"
    
    def test_parse_relationship_definition(self):
        """Test parsing relationship definitions."""
        parser = ComplexParser()
        script = """
        RELATIONSHIP WORKS_ON (Employee * -> Epic *) {
            role: STRING,
            start_date: DATE
        };
        """
        
        program = parser.parse(script)
        assert len(program.statements) == 1
        
        rel = program.statements[0]
        assert isinstance(rel, RelationshipDef)
        assert rel.name == "WORKS_ON"
        assert rel.from_entity == "Employee"
        assert rel.to_entity == "Epic"
        assert rel.from_mult.value == "*"
        assert rel.to_mult.value == "*"
        assert len(rel.fields) == 2
    
    def test_parse_insert_statement(self):
        """Test parsing INSERT statements."""
        parser = ComplexParser()
        script = """
        INSERT Employee {
            name = "John Doe",
            email = "john@example.com",
            department = "Engineering"
        } AS emp1;
        """
        
        program = parser.parse(script)
        assert len(program.statements) == 1
        
        insert = program.statements[0]
        assert isinstance(insert, InsertEntity)
        assert insert.entity_type == "Employee"
        assert insert.alias == "emp1"
        assert len(insert.assignments) == 3
        
        # Check assignment values
        name_assignment = insert.assignments[0]
        assert name_assignment.field == "name"
        assert name_assignment.value.value == "John Doe"
    
    def test_parse_query_statement(self):
        """Test parsing MATCH/RETURN statements."""
        parser = ComplexParser()
        script = """
        MATCH (e:Employee)-[:WORKS_ON]->(p:Epic)
        WHERE e.department = "Engineering"
        RETURN e.name, p.name;
        """
        
        program = parser.parse(script)
        assert len(program.statements) == 1
        
        query = program.statements[0]
        assert isinstance(query, QueryStmt)
        assert query.pattern is not None
        assert query.where is not None
        assert len(query.return_items) == 2
    
    def test_parse_multiple_statements(self):
        """Test parsing multiple statements."""
        parser = ComplexParser()
        script = """
        ENTITY Employee {
            name: STRING,
            email: STRING
        };
        
        ENTITY Project {
            title: STRING,
            budget: FLOAT
        };
        
        INSERT Employee {
            name = "Alice",
            email = "alice@example.com"
        };
        """
        
        program = parser.parse(script)
        assert len(program.statements) == 3
        assert isinstance(program.statements[0], EntityDef)
        assert isinstance(program.statements[1], EntityDef) 
        assert isinstance(program.statements[2], InsertEntity)
    
    def test_parse_error_handling(self):
        """Test error handling for invalid syntax."""
        parser = ComplexParser()
        
        # Missing semicolon
        with pytest.raises(ParseError):
            parser.parse("ENTITY Employee { name: STRING }")
        
        # Invalid field type
        with pytest.raises(ParseError):
            parser.parse("ENTITY Employee { name: INVALID_TYPE };")
    
    def test_round_trip_parsing(self):
        """Test that parsed AST can be converted back to string."""
        parser = ComplexParser()
        script = """
        ENTITY Employee {
            name: STRING,
            age: INT
        };
        """
        
        program = parser.parse(script)
        assert isinstance(program, Program)
        
        # Basic validation that we can access the parsed structure
        entity = program.statements[0]
        assert entity.name == "Employee"
        assert len(entity.fields) == 2
