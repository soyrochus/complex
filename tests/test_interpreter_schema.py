"""Tests for the Complex DSL interpreter schema operations."""

import pytest
from complex.interpreter import ComplexInterpreter
from complex.errors import SemanticError, ExecutionError


class TestInterpreterSchema:
    """Test cases for interpreter schema operations."""
    
    def test_entity_definition(self, interpreter: ComplexInterpreter):
        """Test entity definition execution."""
        script = """
        ENTITY Employee {
            name: STRING,
            email: STRING,
            department: STRING
        };
        """
        
        result = interpreter.execute(script)
        assert result == []  # Schema definitions return no data
        
        # Check that entity is stored in interpreter
        assert "Employee" in interpreter.entities
        entity_def = interpreter.entities["Employee"]
        assert entity_def.name == "Employee"
        assert len(entity_def.fields) == 3
    
    def test_relationship_definition(self, interpreter: ComplexInterpreter):
        """Test relationship definition execution."""
        script = """
        RELATIONSHIP WORKS_ON (Employee * -> Epic *) {
            role: STRING,
            start_date: DATE
        };
        """
        
        result = interpreter.execute(script)
        assert result == []
        
        # Check that relationship is stored
        assert "WORKS_ON" in interpreter.relationships
        rel_def = interpreter.relationships["WORKS_ON"]
        assert rel_def.name == "WORKS_ON"
        assert rel_def.from_entity == "Employee"
        assert rel_def.to_entity == "Epic"
    
    def test_entity_inheritance(self, interpreter: ComplexInterpreter):
        """Test entity inheritance."""
        script = """
        ENTITY Person {
            name: STRING,
            email: STRING
        };
        
        ENTITY Employee {
            department: STRING,
            salary: FLOAT
        } EXTENDS Person;
        """
        
        result = interpreter.execute(script)
        assert result == []
        
        # Check both entities are defined
        assert "Person" in interpreter.entities
        assert "Employee" in interpreter.entities
        
        employee_def = interpreter.entities["Employee"]
        assert employee_def.extends == "Person"
    
    def test_multiple_entity_definitions(self, interpreter: ComplexInterpreter):
        """Test multiple entity definitions in one script."""
        script = """
        ENTITY Employee {
            name: STRING,
            email: STRING
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
        
        result = interpreter.execute(script)
        assert result == []
        
        # Check all entities are defined
        assert len(interpreter.entities) == 3
        assert "Employee" in interpreter.entities
        assert "Document" in interpreter.entities
        assert "Epic" in interpreter.entities
    
    def test_reference_field_types(self, interpreter: ComplexInterpreter):
        """Test entity fields with reference types."""
        script = """
        ENTITY Department {
            name: STRING,
            budget: FLOAT
        };
        
        ENTITY Employee {
            name: STRING,
            department: Department,
            projects: Epic[]
        };
        """
        
        result = interpreter.execute(script)
        assert result == []
        
        employee_def = interpreter.entities["Employee"]
        
        # Check field types
        dept_field = next(f for f in employee_def.fields if f.name == "department")
        assert dept_field.data_type.name == "Department"
        assert not dept_field.data_type.is_array
        
        projects_field = next(f for f in employee_def.fields if f.name == "projects")
        assert projects_field.data_type.name == "Epic"
        assert projects_field.data_type.is_array
    
    def test_primitive_data_types(self, interpreter: ComplexInterpreter):
        """Test all primitive data types."""
        script = """
        ENTITY TestEntity {
            str_field: STRING,
            int_field: INT,
            float_field: FLOAT,
            bool_field: BOOL,
            date_field: DATE,
            datetime_field: DATETIME,
            blob_field: BLOB,
            uuid_field: UUID,
            json_field: JSON
        };
        """
        
        result = interpreter.execute(script)
        assert result == []
        
        entity_def = interpreter.entities["TestEntity"]
        assert len(entity_def.fields) == 9
        
        # Check all field types are preserved
        field_types = {f.name: f.data_type.name for f in entity_def.fields}
        expected_types = {
            "str_field": "STRING",
            "int_field": "INT", 
            "float_field": "FLOAT",
            "bool_field": "BOOL",
            "date_field": "DATE",
            "datetime_field": "DATETIME",
            "blob_field": "BLOB",
            "uuid_field": "UUID",
            "json_field": "JSON"
        }
        assert field_types == expected_types
