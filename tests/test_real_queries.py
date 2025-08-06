#!/usr/bin/env python3
"""Test Complex DSL MATCH queries with actual entity types."""

from complex.parser import ComplexParser

def test_real_entities():
    """Test MATCH queries with real entity types from the schema."""
    parser = ComplexParser()
    
    # Test cases with real entity types
    test_cases = [
        "MATCH (n) RETURN n;",
        "MATCH (e:Employee) RETURN e;",
        "MATCH (d:Document) RETURN d;",
        "MATCH (p:Epic) RETURN p;",
        "MATCH (e:Employee) RETURN e.name;",
        "MATCH (e:Employee) RETURN e.name, e.email;",
        "MATCH (e:Employee) WHERE e.active = TRUE RETURN e;",
    ]
    
    print("Testing MATCH queries with real entity types:\n")
    
    for test_query in test_cases:
        print(f"🧪 Testing: {test_query}")
        try:
            result = parser.parse(test_query)
            print("✅ Successfully parsed")
            
            # Show query details
            if result.statements:
                stmt = result.statements[0]
                from complex.models import QueryStmt
                if isinstance(stmt, QueryStmt):
                    # Show pattern
                    if stmt.pattern.nodes:
                        node = stmt.pattern.nodes[0]
                        print(f"   Node: alias='{node.alias}', type='{node.entity_type}'")
                    
                    # Show return items
                    if stmt.return_items:
                        returns = []
                        for item in stmt.return_items:
                            if item.property:
                                returns.append(f"{item.alias}.{item.property}")
                            else:
                                returns.append(item.alias)
                        print(f"   Returns: {', '.join(returns)}")
                    else:
                        print("   Returns: (nothing)")
                        
                    # Show where clause
                    if stmt.where:
                        print("   WHERE clause: present")
                    
        except Exception as e:
            print(f"❌ Failed to parse")
            print(f"   Error: {e}")
        
        print()

if __name__ == "__main__":
    test_real_entities()
