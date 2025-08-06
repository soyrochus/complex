# Complex DSL

A domain-specific language for graph data manipulation against PostgreSQL databases with the Apache AGE extension.

## Features

- **Declarative Syntax**: Define entities, relationships, and queries using an intuitive DSL
- **Graph Database Support**: Built for PostgreSQL with Apache AGE (Cypher-compatible)
- **Type Safety**: Strong typing with validation and error reporting
- **Python Integration**: Full Python library with CLI and REPL
- **Production Ready**: Thread-safe connection pooling, transaction support, comprehensive testing

## Installation

```bash
pip install complex
```

### Prerequisites

- PostgreSQL 15+ with Apache AGE extension (≥ 1.3.0)
- Python 3.8+

## Quick Start

### 1. Environment Setup

Create a `.env` file with your database configuration:

```env
COMPLEX_DB_HOST=localhost
COMPLEX_DB_PORT=5432
COMPLEX_DB_NAME=postgres
COMPLEX_DB_USER=postgres
COMPLEX_DB_PASSWORD=your_password
COMPLEX_GRAPH_NAME=my_graph
EDGE_REFERENCES=true
```

### 2. Define Your Schema

Create a file `schema.dsl`:

```dsl
ENTITY Employee {
    name: STRING,
    email: STRING,
    department: STRING
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

RELATIONSHIP WORKS_ON (Employee * -> Epic *) {
    role: STRING,
    start_date: DATE
};

RELATIONSHIP IN_DOCUMENT (Employee 1 -> Document *) {
    page_number: INT
};
```

### 3. Insert Data

Create `data.dsl`:

```dsl
INSERT Employee {
    name = "Alice Johnson",
    email = "alice@company.com",
    department = "Engineering"
} AS alice;

INSERT Employee {
    name = "Bob Smith",
    email = "bob@company.com", 
    department = "Product"
} AS bob;

INSERT Epic {
    name = "User Authentication",
    description = "Implement secure login system"
} AS auth_epic;

INSERT Document {
    title = "API Specification",
    content = "Detailed REST API documentation",
    author = alice
} AS api_doc;

CONNECT alice - WORKS_ON -> auth_epic {
    role = "Lead Developer",
    start_date = "2024-01-15"
};

CONNECT bob - IN_DOCUMENT -> api_doc {
    page_number = 1
};
```

### 4. Query Data

Create `queries.dsl`:

```dsl
MATCH (e:Employee)-[:WORKS_ON]->(p:Epic)
WHERE e.department = "Engineering"
RETURN e.name, e.email, p.name;

MATCH (e:Employee)-[:IN_DOCUMENT {page_number: 1}]->(d:Document)
RETURN e.name, d.title;
```

### 5. Run Scripts

```bash
# Execute schema, data, and queries
complex run schema.dsl
complex run data.dsl
complex run queries.dsl

# Start interactive REPL
complex repl
```

## Python API

```python
import complex

# Create interpreter
interpreter = complex.create_interpreter()

# Execute DSL script
script = """
ENTITY User {
    name: STRING,
    email: STRING
};

INSERT User {
    name = "John Doe",
    email = "john@example.com"
} AS user1;

MATCH (u:User) RETURN u.name, u.email;
"""

results = interpreter.execute(script)
print(results)
```

## Language Reference

### Entity Definitions

```dsl
ENTITY EntityName {
    field1: STRING,
    field2: INT,
    field3: OtherEntity,
    field4: AnotherEntity[]
} [EXTENDS ParentEntity];
```

**Supported Types:**
- Primitives: `STRING`, `INT`, `FLOAT`, `BOOL`, `DATE`, `DATETIME`, `BLOB`, `UUID`, `JSON`
- References: `EntityName` (single), `EntityName[]` (array)

### Relationship Definitions

```dsl
RELATIONSHIP RelationshipName (FromEntity mult -> ToEntity mult) {
    property1: STRING,
    property2: INT
};
```

**Multiplicities:** `1` (one), `*` (many)

### Data Manipulation

#### Insert
```dsl
INSERT EntityName {
    field1 = "value",
    field2 = 42,
    field3 = other_alias
} [AS alias];
```

#### Connect
```dsl
CONNECT source_ref - RelationshipName -> target_ref {
    property = "value"
};
```

#### Update
```dsl
UPDATE target_ref SET field1 = "new_value", field2 = 100;
```

#### Delete
```dsl
DELETE target_ref;
```

**Target References:**
- Alias: `alias_name`
- ID: `123` (numeric)
- Pattern: `EntityName {field = "value"}`

### Queries

```dsl
MATCH pattern
[WHERE condition]
[RETURN items];
```

**Pattern Examples:**
```dsl
(e:Employee)
(e:Employee)-[:WORKS_ON]->(p:Project)
(a:User)<-[:CREATED]-(d:Document)-[:IN_PROJECT]->(p:Project)
```

**Conditions:**
```dsl
e.department = "Engineering" AND e.level > 5
```

**Return Items:**
```dsl
e.name, e.email, p.title
```

## Configuration

All configuration is handled through environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `COMPLEX_DB_HOST` | `localhost` | PostgreSQL host |
| `COMPLEX_DB_PORT` | `5432` | PostgreSQL port |
| `COMPLEX_DB_NAME` | `postgres` | Database name |
| `COMPLEX_DB_USER` | `postgres` | Database user |
| `COMPLEX_DB_PASSWORD` | `password` | Database password |
| `COMPLEX_GRAPH_NAME` | `complex_graph` | AGE graph name |
| `EDGE_REFERENCES` | `true` | Use edge-mapped references |

## Testing

```bash
# Install development dependencies
pip install complex[dev]

# Run tests
pytest

# Run with coverage
pytest --cov=complex

# Run specific test categories
pytest complex/tests/test_parser.py
pytest complex/tests/test_interpreter_schema.py
pytest complex/tests/test_interpreter_dml.py
```

## Development

```bash
# Clone repository
git clone https://github.com/soyrochus/complex.git
cd complex

# Install in development mode
pip install -e .[dev]

# Run linting
ruff check complex/
mypy complex/

# Format code
ruff format complex/
```

## Error Handling

The library provides specific exception types:

- `ParseError`: DSL syntax errors
- `SemanticError`: Semantic validation errors
- `ExecutionError`: Database execution errors
- `ConnectionError`: Database connection errors

All errors include detailed messages and, where applicable, source location information.

## Architecture

- **Parser**: Uses Lark (Earley) for robust DSL parsing
- **Interpreter**: Executes statements against Apache AGE via Cypher
- **Database**: Thread-safe connection pooling with psycopg2
- **CLI**: Click-based command interface with REPL support


## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass and code is properly formatted
5. Submit a pull request

## Support

- **Documentation**: [Full specification](AGENTS.md)
- **Issues**: [GitHub Issues](https://github.com/soyrochus/complex/issues)
- **Discussions**: [GitHub Discussions](https://github.com/soyrochus/complex/discussions)

## License and Copyright

Copyright (c) 2025, Iwan van der Kleijn

This project is licensed under the MIT License. See the [LICENSE](LICENSE.txt) file for details.