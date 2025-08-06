# How to Use Complex DSL

## Overview

Complex DSL is a domain-specific language for defining and manipulating graph data structures against PostgreSQL with Apache AGE extension. It provides an intuitive syntax for schema definition, data operations, and graph queries.

## Table of Contents

1. [Basic Syntax Rules](#basic-syntax-rules)
2. [Comments](#comments)
3. [Schema Definition](#schema-definition)
4. [Data Operations](#data-operations)
5. [Graph Queries](#graph-queries)
6. [Data Types](#data-types)
7. [Complete Examples](#complete-examples)
8. [AI Integration Guide](#ai-integration-guide)

## Basic Syntax Rules

### Statement Structure
- All statements end with semicolons (`;`)
- Identifiers use `CNAME` format (alphanumeric + underscore, starting with letter)
- String literals use double quotes: `"example"`
- Numbers can be integers or floats: `42`, `3.14`
- Booleans: `TRUE`, `FALSE`
- Null values: `NULL`

### Comments
```dsl
// C-style single line comments
-- SQL-style single line comments

// Both styles are supported throughout the DSL
```

## Schema Definition

### Entity Definition

Basic entity syntax:
```dsl
ENTITY EntityName {
    field_name: DATA_TYPE,
    another_field: DATA_TYPE
};
```

Entity with inheritance:
```dsl
// Inheritance can be specified before or after field block
ENTITY Child EXTENDS Parent {
    child_field: STRING
};

// Or alternatively:
ENTITY Child {
    child_field: STRING
} EXTENDS Parent;
```

### Relationship Definition

```dsl
RELATIONSHIP RelationshipName (FromEntity mult? -> ToEntity mult?) {
    relationship_field: DATA_TYPE
};
```

Where `mult` is multiplicity:
- `1` - exactly one
- `*` - zero or more
- If omitted, defaults to `1`

Examples:
```dsl
// One-to-many relationship
RELATIONSHIP WORKS_ON (Employee * -> Project 1);

// Many-to-many with properties
RELATIONSHIP COLLABORATES (Employee * -> Employee *) {
    role: STRING,
    start_date: DATE
};
```

## Data Operations

### INSERT Operations

Basic insert:
```dsl
INSERT EntityName {
    field1 = "value",
    field2 = 42,
    field3 = TRUE
};
```

Insert with alias (for later reference):
```dsl
INSERT Employee {
    name = "Alice",
    email = "alice@company.com"
} AS alice;
```

Array literals:
```dsl
INSERT Document {
    title = "API Guide",
    tags = ["api", "documentation", "backend"]
};
```

### CONNECT Operations

Connect entities through relationships:
```dsl
CONNECT alias1 - RELATIONSHIP_NAME -> alias2;

// With relationship properties
CONNECT alice - WORKS_ON -> project1 {
    role = "Developer",
    start_date = "2024-01-15"
};
```

### UPDATE Operations

```dsl
UPDATE target_reference SET field1 = "new_value", field2 = 100;
```

Target reference can be:
- Alias: `alice`
- ID: `123`
- Pattern: `Employee { name = "Alice" }`

### DELETE Operations

```dsl
DELETE target_reference;
```

## Graph Queries

### Basic Query Structure

```dsl
MATCH pattern
WHERE condition?
RETURN return_list;
```

The simplest query to get all nodes in the graph:
```dsl
MATCH (n) RETURN n;
```

### Pattern Syntax

Node patterns:
```dsl
(alias:EntityType)           // Node with alias and type
(alias:EntityType {condition}) // Node with condition
(:EntityType)                // Node without alias
(alias)                      // Node with alias, any type
```

Edge patterns:
```dsl
-[alias:RELATIONSHIP_TYPE]->  // Directed edge with alias and type
-[:RELATIONSHIP_TYPE]->       // Directed edge without alias
<-[alias:REL_TYPE]-          // Reverse direction
-[alias:REL_TYPE]-           // Bidirectional
```

Complete patterns:
```dsl
(e:Employee)-[w:WORKS_ON]->(p:Project)
(a:Person)<-[:MANAGES]-(b:Person)-[:LEADS]->(t:Team)
```

### WHERE Conditions

Property comparisons:
```dsl
WHERE alias.property = "value"
WHERE alias.property > 1000
WHERE alias.property <= "2024-12-31"
```

Comparison operators: `=`, `!=`, `<`, `<=`, `>`, `>=`

Complex conditions:
```dsl
WHERE e.department = "Engineering" AND e.salary > 90000
WHERE p.status = "Active" OR p.priority = "High"
```

### RETURN Clauses

```dsl
RETURN alias                    // Return entire entity
RETURN alias.property           // Return specific property
RETURN alias1.name, alias2.title // Multiple properties
```

### Graph Exploration Queries

For exploring and understanding your graph data:

```dsl
// Get all nodes in the graph (useful for initial exploration)
MATCH (n) RETURN n;

// Get all nodes of a specific type
MATCH (n:Employee) RETURN n;

// Get all relationships between any nodes
MATCH (a)-[r]->(b) RETURN a, r, b;

// Count all nodes by type
MATCH (n:Employee) RETURN COUNT(n);
```

## Data Types

### Primitive Types
- `STRING` - Text data
- `INT` - Integer numbers
- `FLOAT` - Floating-point numbers
- `BOOL` - Boolean (TRUE/FALSE)
- `DATE` - Date values
- `DATETIME` - Date and time values
- `BLOB` - Binary data
- `UUID` - Unique identifiers
- `JSON` - JSON objects

### Complex Types
- `EntityName` - Reference to another entity
- `EntityName[]` - Array of entity references

### Literal Values
- Strings: `"Hello World"`
- Numbers: `42`, `3.14`, `-100`
- Booleans: `TRUE`, `FALSE`
- Null: `NULL`
- Arrays: `["item1", "item2", "item3"]`

## Complete Examples

### Schema Definition Example

```dsl
// Define base entity
ENTITY Person {
    name: STRING,
    email: STRING,
    birth_date: DATE
};

// Entity with inheritance
ENTITY Employee EXTENDS Person {
    employee_id: STRING,
    department: STRING,
    salary: FLOAT,
    hire_date: DATE
};

// Relationship with multiplicity
RELATIONSHIP MANAGES (Employee 1 -> Employee *) {
    start_date: DATE,
    management_type: STRING
};
```

### Data Operations Example

```dsl
// Insert entities with aliases
INSERT Employee {
    name = "Alice Johnson",
    email = "alice@company.com",
    department = "Engineering",
    salary = 95000.0,
    hire_date = "2023-01-15"
} AS alice;

INSERT Employee {
    name = "Bob Smith", 
    email = "bob@company.com",
    department = "Engineering",
    salary = 85000.0,
    hire_date = "2023-03-01"
} AS bob;

// Connect entities
CONNECT alice - MANAGES -> bob {
    start_date = "2023-06-01",
    management_type = "Direct"
};
```

### Query Examples

```dsl
// Get all nodes in the graph
MATCH (n) RETURN n;

// Get all nodes of a specific type
MATCH (e:Employee) RETURN e;

// Find all employees in Engineering
MATCH (e:Employee)
WHERE e.department = "Engineering"
RETURN e.name, e.salary;

// Find management relationships
MATCH (manager:Employee)-[m:MANAGES]->(employee:Employee)
WHERE m.management_type = "Direct"
RETURN manager.name, employee.name, m.start_date;

// Complex query with multiple conditions
MATCH (e:Employee)-[:WORKS_ON]->(p:Project)
WHERE e.salary > 80000 AND p.status = "Active"
RETURN e.name, p.title, e.department;
```

## AI Integration Guide

### For AI Systems Processing Complex DSL

#### 1. Parsing Strategy
- Use the grammar rules as a formal specification
- All statements end with semicolons - use this for statement boundary detection
- Comments (both `//` and `--` styles) should be ignored during parsing
- Identifiers follow CNAME pattern: `[a-zA-Z_][a-zA-Z0-9_]*`

#### 2. Statement Types Recognition
```
Entity Definition:    ENTITY <name> [EXTENDS <parent>] { <fields> } [EXTENDS <parent>];
Relationship:         RELATIONSHIP <name> (<from> <mult?> -> <to> <mult?>) [{ <fields> }];
Insert:              INSERT <type> { <assignments> } [AS <alias>];
Connect:             CONNECT <from> - <rel> -> <to> [{ <properties> }];
Update:              UPDATE <target> SET <assignments>;
Delete:              DELETE <target>;
Query:               MATCH <pattern> [WHERE <condition>] [RETURN <list>];
```

#### 3. Pattern Matching for Queries
- Node pattern: `(alias:Type {condition})` - all parts optional except parentheses
- Edge pattern: `-[alias:Type {condition}]->` - direction matters (`->`, `<-`, `-`)
- Conditions use property references: `alias.property operator value`

#### 4. Data Type Handling
- Primitive types are keywords: STRING, INT, FLOAT, BOOL, DATE, DATETIME, BLOB, UUID, JSON
- Custom types reference entity names
- Array types append `[]`: `EntityName[]`
- Literal arrays use bracket notation: `["item1", "item2"]`

#### 5. Common Patterns for AI Generation
```dsl
// Schema first, then data, then queries
// 1. Define entities and relationships
ENTITY Person { name: STRING, age: INT };
RELATIONSHIP KNOWS (Person * -> Person *);

// 2. Insert data with aliases
INSERT Person { name = "Alice", age = 30 } AS alice;
INSERT Person { name = "Bob", age = 25 } AS bob;

// 3. Connect relationships  
CONNECT alice - KNOWS -> bob;

// 4. Query the data
// Get all nodes
MATCH (n) RETURN n;

// Get specific relationships
MATCH (p1:Person)-[:KNOWS]->(p2:Person)
RETURN p1.name, p2.name;
```

#### 6. Error Prevention
- Always end statements with semicolons
- Use double quotes for strings
- Reference aliases consistently
- Ensure entities are defined before being used in relationships
- Insert entities before connecting them
- Use proper multiplicity syntax in relationships

#### 7. Semantic Validation
- Entity names should be referenced consistently
- Aliases defined in INSERT can be used in CONNECT
- Property names in WHERE clauses should match entity definitions
- Data types in assignments should match field definitions

This DSL is designed for clarity and consistency, making it suitable for both human authoring and AI generation of graph database schemas and operations.
