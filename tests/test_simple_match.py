#!/usr/bin/env python3
"""Test if Complex DSL can parse simple MATCH (n) RETURN n; syntax."""

from complex.parser import ComplexParser

def test_simple_match():
    """Test parsing of MATCH (n) RETURN n; syntax."""
    parser = ComplexParser()
    
    # Test cases
    test_cases = [
        "MATCH (n) RETURN n;",
        "MATCH (n:Person) RETURN n;", 
        "MATCH (n:Person) RETURN n.name;",
        "MATCH (n) WHERE n.name = \"John\" RETURN n;",
        "MATCH (n);",  # Without RETURN clause
    ]
    
    for test_query in test_cases:
        print(f"\n🧪 Testing: {test_query}")
        try:
            result = parser.parse(test_query)
            print("✅ Successfully parsed")
            
            # Check the statement details
            if result.statements:
                stmt = result.statements[0]
                print("Statement type:", type(stmt).__name__)
                
                # Check if it's a QueryStmt
                from complex.models import QueryStmt
                if isinstance(stmt, QueryStmt):
                    print("Pattern nodes:", len(stmt.pattern.nodes))
                    print("Pattern edges:", len(stmt.pattern.edges))
                    if stmt.pattern.nodes:
                        node = stmt.pattern.nodes[0]
                        print(f"First node - alias: {node.alias}, entity_type: '{node.entity_type}'")
                    print("Return items:", len(stmt.return_items) if stmt.return_items else 0)
                    if stmt.return_items:
                        for item in stmt.return_items:
                            print(f"  - alias: '{item.alias}', property: {item.property}")
                    
                    # Check WHERE clause
                    if stmt.where:
                        print("WHERE clause present:", True)
                    else:
                        print("WHERE clause present:", False)
                
        except Exception as e:
            print("❌ Failed to parse")
            print("Error:", e)

if __name__ == "__main__":
    test_simple_match()
