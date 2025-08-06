"""Tests for the Complex DSL interpreter DML operations."""

import pytest
from complex.interpreter import ComplexInterpreter
from complex.errors import SemanticError, ExecutionError


class TestInterpreterDML:
    """Test cases for interpreter DML operations (INSERT, UPDATE, DELETE, CONNECT)."""
    
    def test_insert_entity(self, interpreter: ComplexInterpreter, sample_entities: str):
        """Test INSERT entity operation."""
        # First define the entities
        interpreter.execute(sample_entities)
        
        script = """
        INSERT Employee {
            name = "John Doe",
            email = "john@example.com",
            department = "Engineering"
        } AS emp1;
        """
        
        result = interpreter.execute(script)
        assert result == []  # INSERT returns no data
        
        # Check alias was stored
        assert "emp1" in interpreter.aliases
        assert isinstance(interpreter.aliases["emp1"], int)
    
    def test_insert_multiple_entities(self, interpreter: ComplexInterpreter, sample_entities: str):
        """Test multiple INSERT operations."""
        interpreter.execute(sample_entities)
        
        script = """
        INSERT Employee {
            name = "Alice Smith",
            email = "alice@example.com",
            department = "Marketing"
        } AS emp1;
        
        INSERT Employee {
            name = "Bob Johnson", 
            email = "bob@example.com",
            department = "Engineering"
        } AS emp2;
        
        INSERT Document {
            title = "Project Plan",
            content = "Detailed project planning document",
            author = emp1
        } AS doc1;
        """
        
        result = interpreter.execute(script)
        assert result == []
        
        # Check all aliases were stored
        assert "emp1" in interpreter.aliases
        assert "emp2" in interpreter.aliases
        assert "doc1" in interpreter.aliases
    
    def test_connect_relationship(self, interpreter: ComplexInterpreter, sample_entities: str, sample_relationships: str):
        """Test CONNECT relationship operation."""
        # Set up entities and relationships
        interpreter.execute(sample_entities + sample_relationships)
        
        script = """
        INSERT Employee {
            name = "Developer",
            email = "dev@example.com",
            department = "Engineering"
        } AS emp1;
        
        INSERT Epic {
            name = "User Authentication",
            description = "Implement user login system"
        } AS epic1;
        
        CONNECT emp1 - WORKS_ON -> epic1 {
            role = "Lead Developer",
            start_date = "2024-01-15"
        };
        """
        
        result = interpreter.execute(script)
        assert result == []
    
    def test_connect_with_numeric_ids(self, interpreter: ComplexInterpreter, sample_relationships: str):
        """Test CONNECT using numeric vertex IDs."""
        interpreter.execute(sample_relationships)
        
        script = """
        CONNECT 123 - WORKS_ON -> 456 {
            role = "Contributor"
        };
        """
        
        # This should not raise an error in parsing/semantic analysis
        # Actual execution might fail if vertices don't exist, but that's OK for this test
        try:
            result = interpreter.execute(script)
        except ExecutionError:
            # Expected if vertices with IDs 123, 456 don't exist
            pass
    
    def test_update_by_alias(self, interpreter: ComplexInterpreter, sample_entities: str):
        """Test UPDATE using alias reference."""
        interpreter.execute(sample_entities)
        
        script = """
        INSERT Employee {
            name = "John Doe",
            email = "john@example.com",
            department = "Engineering"
        } AS emp1;
        
        UPDATE emp1 SET 
            department = "Senior Engineering",
            email = "john.doe@example.com";
        """
        
        result = interpreter.execute(script)
        assert result == []
    
    def test_update_by_pattern(self, interpreter: ComplexInterpreter, sample_entities: str):
        """Test UPDATE using pattern matching."""
        interpreter.execute(sample_entities)
        
        script = """
        UPDATE Employee {department = "Engineering"} SET 
            department = "Software Engineering";
        """
        
        result = interpreter.execute(script)
        assert result == []
    
    def test_delete_by_alias(self, interpreter: ComplexInterpreter, sample_entities: str):
        """Test DELETE using alias reference."""
        interpreter.execute(sample_entities)
        
        script = """
        INSERT Employee {
            name = "Temp Employee",
            email = "temp@example.com",
            department = "Temporary"
        } AS temp_emp;
        
        DELETE temp_emp;
        """
        
        result = interpreter.execute(script)
        assert result == []
    
    def test_delete_by_pattern(self, interpreter: ComplexInterpreter, sample_entities: str):
        """Test DELETE using pattern matching."""
        interpreter.execute(sample_entities)
        
        script = """
        DELETE Employee {department = "Temporary"};
        """
        
        result = interpreter.execute(script)
        assert result == []
    
    def test_invalid_entity_type(self, interpreter: ComplexInterpreter):
        """Test error handling for undefined entity types."""
        script = """
        INSERT UnknownEntity {
            field = "value"
        };
        """
        
        with pytest.raises(SemanticError) as exc_info:
            interpreter.execute(script)
        
        assert "Unknown entity type" in str(exc_info.value)
    
    def test_invalid_relationship_type(self, interpreter: ComplexInterpreter, sample_entities: str):
        """Test error handling for undefined relationship types."""
        interpreter.execute(sample_entities)
        
        script = """
        INSERT Employee {
            name = "Test",
            email = "test@example.com", 
            department = "Test"
        } AS emp1;
        
        INSERT Employee {
            name = "Test2",
            email = "test2@example.com",
            department = "Test"
        } AS emp2;
        
        CONNECT emp1 - UNKNOWN_REL -> emp2;
        """
        
        with pytest.raises(SemanticError) as exc_info:
            interpreter.execute(script)
        
        assert "Unknown relationship type" in str(exc_info.value)
    
    def test_undefined_alias_reference(self, interpreter: ComplexInterpreter, sample_entities: str):
        """Test error handling for undefined alias references."""
        interpreter.execute(sample_entities)
        
        script = """
        UPDATE unknown_alias SET name = "New Name";
        """
        
        with pytest.raises(SemanticError) as exc_info:
            interpreter.execute(script)
        
        assert "Unknown alias" in str(exc_info.value)
    
    def test_literal_values(self, interpreter: ComplexInterpreter, sample_entities: str):
        """Test different literal value types."""
        interpreter.execute(sample_entities)
        
        script = """
        INSERT Employee {
            name = "Test Employee",
            email = "test@example.com",
            department = "Engineering"
        } AS emp1;
        """
        
        result = interpreter.execute(script)
        assert result == []
