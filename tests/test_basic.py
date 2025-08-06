#!/usr/bin/env python3
"""Simple test to verify parser functionality."""

from complex.parser import ComplexParser
from complex.models import QueryStmt

def test_basic_parsing():
    """Test basic parsing functionality."""
    parser = ComplexParser()
    
    # Test entity definition (existing functionality)
    entity_script = """
    ENTITY Employee {
        name: STRING,
        email: STRING
    };
    """
    
    try:
        result = parser.parse(entity_script)
        print("✅ Entity definition parsing works")
        assert len(result.statements) == 1
        print(f"   Statement type: {type(result.statements[0]).__name__}")
    except Exception as e:
        print(f"❌ Entity definition parsing failed: {e}")
        return False
    
    # Test query parsing (new functionality)
    query_script = "MATCH (e:Employee) WHERE e.active = TRUE RETURN e.name, e.email;"
    
    try:
        result = parser.parse(query_script)
        print("✅ Query parsing works")
        assert len(result.statements) == 1
        stmt = result.statements[0]
        assert isinstance(stmt, QueryStmt)
        print(f"   Statement type: {type(stmt).__name__}")
        print(f"   Return items: {len(stmt.return_items)}")
        print(f"   WHERE clause: {'Yes' if stmt.where else 'No'}")
    except Exception as e:
        print(f"❌ Query parsing failed: {e}")
        return False
    
    # Test the specific query from the user
    user_query = "MATCH (n) RETURN n;"
    
    try:
        result = parser.parse(user_query)
        print("✅ User query parsing works")
        assert len(result.statements) == 1
        stmt = result.statements[0]
        assert isinstance(stmt, QueryStmt)
        assert len(stmt.return_items) == 1
        assert stmt.return_items[0].alias == 'n'
        assert stmt.return_items[0].property is None
        print(f"   Returns: {stmt.return_items[0].alias}")
    except Exception as e:
        print(f"❌ User query parsing failed: {e}")
        return False
    
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    test_basic_parsing()
