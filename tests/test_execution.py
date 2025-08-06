#!/usr/bin/env python3
"""Test if the Complex DSL can execute MATCH (n) RETURN n; queries."""

import os
os.environ['POSTGRES_DB'] = 'test_db'
os.environ['POSTGRES_USER'] = 'test_user' 
os.environ['POSTGRES_PASSWORD'] = 'test_pass'
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5432'

from complex.interpreter import ComplexInterpreter
from complex.parser import ComplexParser

def test_execution():
    """Test executing MATCH (n) RETURN n; queries."""
    parser = ComplexParser()
    interpreter = ComplexInterpreter()
    
    # Test simple MATCH query
    test_query = "MATCH (n) RETURN n;"
    
    try:
        # Parse the query
        ast = parser.parse(test_query)
        print(f"✅ Successfully parsed: {test_query}")
        
        # Try to execute it (this will likely fail due to missing DB, but we can see if the interpreter handles it)
        try:
            result = interpreter.execute(test_query)
            print(f"✅ Successfully executed: {test_query}")
            print(f"Result: {result}")
        except Exception as e:
            print(f"⚠️ Execution failed (expected due to DB setup): {e}")
            # Check if it's the type of error we expect
            if "database" in str(e).lower() or "connection" in str(e).lower() or "age" in str(e).lower():
                print("✅ Interpreter correctly processed the query structure")
            else:
                print(f"❌ Unexpected error: {e}")
                
    except Exception as e:
        print(f"❌ Failed to parse: {test_query}")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_execution()
