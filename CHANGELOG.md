# Changelog

All notable changes to the Complex DSL library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-08-05

### Added

- Initial release of Complex DSL library
- Core DSL parser using Lark with comprehensive grammar support
- Entity and relationship schema definitions
- Complete CRUD operations (INSERT, UPDATE, DELETE, CONNECT)
- Advanced query capabilities with MATCH/WHERE/RETURN
- PostgreSQL + Apache AGE integration with Cypher generation
- Thread-safe database connection pooling
- Comprehensive error handling with domain-specific exceptions
- Command-line interface with script execution and interactive REPL
- Environment-based configuration management
- Support for both edge-mapped and scalar-ID reference strategies
- Full test suite with ≥85% coverage
- Production-ready code quality (mypy, ruff compliance)
- Comprehensive documentation and examples

### Features

#### Language Support
- Entity definitions with inheritance (EXTENDS)
- Relationship definitions with multiplicities
- All primitive data types (STRING, INT, FLOAT, BOOL, DATE, DATETIME, BLOB, UUID, JSON)
- Reference types (single and array)
- Pattern matching in queries and updates
- Multi-line statement support

#### Database Integration
- Apache AGE extension support for graph operations
- Automatic graph creation and management
- Transaction-wrapped operations with rollback on failure
- Connection pooling with graceful shutdown
- SQLSTATE error code mapping

#### Developer Experience
- Intuitive CLI with `complex run` and `complex repl` commands
- Rich error messages with source location information
- Type-safe Python API
- Comprehensive test fixtures and utilities
- Development-friendly configuration defaults

#### Quality Assurance
- Static type checking with mypy
- Code linting with ruff
- Test coverage monitoring
- CI/CD ready configuration
- Production deployment support

### Documentation

- Complete README with quick start guide
- Detailed language reference
- API documentation with examples
- Development setup instructions
- Testing and deployment guides

### Dependencies

- `psycopg2-binary>=2.9.0` - PostgreSQL adapter
- `lark-parser>=1.1.0` - Parser generator
- `python-dotenv>=1.0.0` - Environment configuration
- `click>=8.0.0` - CLI framework
- `pydantic>=2.0.0` - Data validation

### Development Dependencies

- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Coverage reporting
- `mypy>=1.0.0` - Static type checking
- `ruff>=0.1.0` - Linting and formatting
- `pexpect>=4.8.0` - CLI testing

### Compatibility

- Python 3.8+
- PostgreSQL 15+
- Apache AGE 1.3.0+

---

## Development Notes

This initial release establishes the foundation for the Complex DSL ecosystem. Future releases will focus on:

- Performance optimizations
- Extended query capabilities
- Advanced relationship modeling
- Integration with popular Python frameworks
- Enhanced developer tooling

For detailed technical specifications, see [AGENTS.md](AGENTS.md).
