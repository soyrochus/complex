# Complex DSL Examples

This directory contains example DSL scripts that demonstrate the capabilities of the Complex DSL library.

## Files

- **`schema.dsl`** - Entity and relationship definitions
- **`data.dsl`** - Sample data insertion and connections
- **`queries.dsl`** - Various query examples
- **`updates.dsl`** - Update and delete operations

## Usage

Run the examples in order:

```bash
# 1. Define the schema
complex run examples/schema.dsl

# 2. Insert sample data
complex run examples/data.dsl

# 3. Run queries
complex run examples/queries.dsl

# 4. Perform updates (optional)
complex run examples/updates.dsl
```

## Example Scenarios

The examples model a software development organization with:

- **Employees** in different departments (Engineering, Product, Design, QA)
- **Projects** and **Epics** representing work items
- **Documents** authored by employees
- **Relationships** showing work assignments, management hierarchy, and project structure

## Key Features Demonstrated

### Entity Definitions
- Primitive data types (STRING, INT, FLOAT, BOOL, DATE, DATETIME)
- Reference types (single and array)
- Entity inheritance with EXTENDS

### Relationship Definitions
- Many-to-many relationships with properties
- One-to-many relationships
- Multiplicities and constraints

### Data Operations
- INSERT with alias assignment
- CONNECT for creating relationships with properties
- UPDATE with pattern matching and field assignments
- DELETE with conditional targeting

### Queries
- Pattern matching with node and edge patterns
- WHERE clauses with multiple conditions
- RETURN projections with specific fields
- Complex multi-hop relationship traversals
- Graph exploration queries (`MATCH (n) RETURN n;` to get all nodes)

## Environment Setup

Before running the examples, ensure you have:

1. PostgreSQL with Apache AGE extension installed
2. Environment variables configured (see main README.md)
3. Complex DSL library installed using `uv`:

```bash
# Install dependencies and sync the environment
uv sync
```

## Interactive Exploration

You can also explore these examples interactively:

```bash
complex repl
```

Then copy and paste statements from the example files to see immediate results.

### Quick Start Queries

After running the schema and data examples, try these exploration queries:

```bash
# Get all nodes in the graph
MATCH (n) RETURN n;

# Get all employees
MATCH (e:Employee) RETURN e;

# Get all relationships
MATCH (a)-[r]->(b) RETURN a, r, b;

# Find specific employees
MATCH (e:Employee) WHERE e.department = "Engineering" RETURN e.name;
```
