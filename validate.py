#!/usr/bin/env python3
"""
Simple validation script for the Complex DSL library.

This script tests basic functionality without requiring a database connection.
It validates parsing, AST generation, and basic semantic analysis.
"""

import sys
import traceback
from pathlib import Path

# Add the complex package to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_parser():
    """Test the parser functionality."""
    print("Testing parser...")
    
    try:
        from complex.parser import ComplexParser
        from complex.models import Program, EntityDef, InsertEntity
        
        parser = ComplexParser()
        
        # Test entity definition parsing
        entity_script = """
        ENTITY Employee {
            name: STRING,
            email: STRING,
            department: STRING
        };
        """.strip()
        
        program = parser.parse(entity_script)
        assert isinstance(program, Program)
        assert len(program.statements) == 1
        assert isinstance(program.statements[0], EntityDef)
        
        entity = program.statements[0]
        assert entity.name == "Employee"
        assert len(entity.fields) == 3
        
        print("✓ Entity definition parsing works")
        
        # Test insert statement parsing
        insert_script = """
        INSERT Employee {
            name = "John Doe",
            email = "john@example.com",
            department = "Engineering"
        } AS emp1;
        """.strip()
        
        program = parser.parse(insert_script)
        assert isinstance(program.statements[0], InsertEntity)
        
        insert = program.statements[0]
        assert insert.entity_type == "Employee"
        assert insert.alias == "emp1"
        assert len(insert.assignments) == 3
        
        print("✓ Insert statement parsing works")
        
        # Test complex script
        complex_script = """
        ENTITY Employee {
            name: STRING,
            email: STRING
        };
        
        ENTITY Project {
            title: STRING,
            budget: FLOAT
        };
        
        RELATIONSHIP WORKS_ON (Employee * -> Project *) {
            role: STRING
        };
        
        INSERT Employee {
            name = "Alice",
            email = "alice@example.com"
        } AS alice;
        
        INSERT Project {
            title = "Web App",
            budget = 50000.0
        } AS project1;
        
        CONNECT alice - WORKS_ON -> project1 {
            role = "Developer"
        };
        
        MATCH (e:Employee)-[:WORKS_ON]->(p:Project)
        RETURN e.name, p.title;
        """.strip()
        
        program = parser.parse(complex_script)
        assert len(program.statements) == 7  # 2 entities, 1 relationship, 2 inserts, 1 connect, 1 query
        
        print("✓ Complex script parsing works")
        print("✓ Parser tests passed!")
        
    except Exception as e:
        print(f"✗ Parser test failed: {e}")
        traceback.print_exc()
        return False
    
    return True


def test_error_handling():
    """Test error handling."""
    print("\nTesting error handling...")
    
    try:
        from complex.parser import ComplexParser
        from complex.errors import ParseError
        
        parser = ComplexParser()
        
        # Test syntax error
        try:
            parser.parse("INVALID SYNTAX HERE")
            print("✗ Should have raised ParseError")
            return False
        except ParseError:
            print("✓ ParseError correctly raised for invalid syntax")
        
        # Test missing semicolon
        try:
            parser.parse("ENTITY Employee { name: STRING }")
            print("✗ Should have raised ParseError for missing semicolon")
            return False
        except ParseError:
            print("✓ ParseError correctly raised for missing semicolon")
        
        print("✓ Error handling tests passed!")
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        traceback.print_exc()
        return False
    
    return True


def test_imports():
    """Test that all modules can be imported."""
    print("\nTesting imports...")
    
    try:
        import complex
        from complex import ComplexParser, ComplexInterpreter, create_interpreter
        from complex.errors import ComplexError, ParseError, SemanticError
        from complex.models import Program, EntityDef
        
        print("✓ All core imports work")
        
        # Test that we can create instances
        parser = ComplexParser()
        assert parser is not None
        
        print("✓ Parser instantiation works")
        
        # Note: Don't test interpreter instantiation here as it requires DB
        print("✓ Import tests passed!")
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        traceback.print_exc()
        return False
    
    return True


def test_cli_import():
    """Test CLI module import."""
    print("\nTesting CLI import...")
    
    try:
        from complex.cli import main, run_script, run_repl
        print("✓ CLI imports work")
        
    except Exception as e:
        print(f"✗ CLI import failed: {e}")
        traceback.print_exc()
        return False
    
    return True


def main():
    """Run all validation tests."""
    print("Complex DSL Library Validation")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_parser,
        test_error_handling,
        test_cli_import,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation tests passed!")
        print("\nNext steps:")
        print("1. Set up PostgreSQL with Apache AGE extension")
        print("2. Configure environment variables in .env file")
        print("3. Run: complex run examples/schema.dsl")
        print("4. Run: complex run examples/data.dsl")
        print("5. Run: complex run examples/queries.dsl")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
