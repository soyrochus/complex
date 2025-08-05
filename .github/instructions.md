## Prompt for the coding agent

> **System / high‑level role**
> You are an expert Python architect and database engineer. Generate production‑quality, idiomatic, well‑tested code.
>
> **Task**
> Create a distributable Python library named **`complex`** (importable as `import complex`).
> The purpose of this library is to parse, interpret, and execute the *Complex DSL* against a live PostgreSQL instance running the **Apache AGE** extension (which provides Cypher support).
> Follow every requirement and design detail below.
>
> ---
>
> ### 1  Project layout
>
> ```
> complex/
> ├─ __init__.py
> ├─ env.py              # load & expose .env variables via python‑dotenv
> ├─ errors.py           # domain‑specific exception hierarchy + error ↔︎ SDL mapping
> ├─ grammar.lark        # EBNF grammar for Lark
> ├─ parser.py           # ComplexParser class
> ├─ interpreter.py      # ComplexInterpreter class
> ├─ db.py               # thin psycopg2 wrapper, connection pool, query helpers
> ├─ cli.py              # minimal CLI / REPL
> ├─ models.py           # dataclasses / pydantic helpers for AST nodes
> └─ tests/
>    ├─ conftest.py      # pytest fixtures: temp DB, AGE graph, env setup
>    ├─ test_parser.py
>    ├─ test_interpreter_schema.py
>    ├─ test_interpreter_dml.py
>    └─ test_cli.py
> pyproject.toml         # build metadata, deps (psycopg2‑binary, lark‑parser, python‑dotenv, click, pytest)
> README.md              # usage & install
> CHANGELOG.md           # semantic‑versioned release notes
> ```
>
> *Feel free to add helper modules if it improves clarity, but keep the public surface confined to*
> `complex.parser`, `complex.interpreter`, `complex.cli`, `complex.errors`, `complex.env`.
>
> ---
>
> ### 2  Environment handling (`complex.env`)
>
> * Use **python‑dotenv**.
> * Required variables (with sensible defaults for local dev):
>   `COMPLEX_DB_HOST`, `COMPLEX_DB_PORT`, `COMPLEX_DB_NAME`, `COMPLEX_DB_USER`,
>   `COMPLEX_DB_PASSWORD`, `COMPLEX_GRAPH_NAME`
> * Provide `get_connection_params()` that returns a dict ready for `psycopg2.connect(**params)`.
>
> ---
>
> ### 3  Error model (`complex.errors`)
>
> * Define a root `ComplexError(Exception)`.
> * Sub‑classes: `ParseError`, `SemanticError`, `ExecutionError`, `ConnectionError`.
> * Map PostgreSQL / AGE SQLSTATE codes to these errors where possible.
> * Ensure all public APIs return `(ok: bool, value | error)` or raise the typed error.
>
> ---
>
> ### 4  Parser (`complex.parser`)
>
> * Use **Lark** (Earley mode) with the exact grammar given below in § 11 (copy verbatim into *grammar.lark*).
> * Expose `ComplexParser.parse(script: str) -> models.Program` (AST root).
> * Provide helpful source‑position information in `ParseError`.
>
> ---
>
> ### 5  Interpreter (`complex.interpreter`)
>
> * Accept an AST or raw script.
> * For each statement type, generate and execute either
>
>   * **Cypher** (preferred for graph operations) via `SELECT * FROM cypher('<graph>', $$ … $$) AS (v agtype)`; **or**
>   * regular SQL for schema metadata tables if needed.
> * Implement both reference‑field strategies:
>
>   1. **Edge‑mapped**: on `INSERT`, create AGE edges when a field’s type matches another ENTITY.
>   2. **Scalar‑ID**: store reference as vertex ID inside the vertex JSON.
>      Use a feature flag (`EDGE_REFERENCES=bool`) in `.env`.
> * Support **INSERT, CONNECT, UPDATE, DELETE, MATCH/RETURN** exactly as in spec.
> * Provide `execute(script: str) -> list[dict]` returning query results or `None`.
> * Wrap all DB calls in transactions; auto‑rollback on exceptions.
>
> ---
>
> ### 6  Database helper (`complex.db`)
>
> * Single psycopg2 connection pool (thread‑safe).
> * Convenience method `run(sql: str, params: tuple = ())` that returns cursor‑like iterator of dict rows.
>
> ---
>
> ### 7  CLI (`complex.cli`)
>
> * Use **click**.
> * Commands:
>
>   * `complex run FILE.dsl` – run a script.
>   * `complex repl` – interactive prompt with multi‑line support, history, and `.exit`.
> * Exit with non‑zero code on any `ComplexError`.
>
> ---
>
> ### 8  Testing (`pytest` under `complex/tests`)
>
> * Spin up a disposable PostgreSQL + AGE (can assume it’s already running and reachable via env vars; use unique `COMPLEX_GRAPH_NAME` per test run).
> * Cover:
>
>   * Grammar round‑trip parse → AST → stringify.
>   * Insert/update/delete using the **“Employee / Document / Epic”** example.
>   * Relationship with edge property (`IN_DOCUMENT page_number`).
>   * MATCH queries including WHERE & RETURN projections.
>   * CLI smoke test (`complex run`, `complex repl` via `pexpect`).
> * Aim for ≥ 85 % coverage.
>
> ---
>
> ### 9  Documentation
>
> * Docstrings for every public function & class.
> * `README.md` must include: installation (`pip install complex`), env setup example (`.env`), quick start, and link to full spec.
> * Provide usage examples mirroring § 9 “Full script template”.
>
> ---
>
> ### 10  CI / packaging (bonus)
>
> * Include a GitHub Actions workflow (`.github/workflows/test.yml`) that installs Postgres+AGE via Docker, sets env vars, and runs `pytest`.
> * `pyproject.toml` should enable `build` & `twine` for publishing.
>
> ---
>
> ### 11  **Grammar definition (copy as‑is into `grammar.lark`)**
>
> ```ebnf
> // ----------------------------------------------
> // 0. Lexical tokens
> %import common.CNAME
> %import common.ESCAPED_STRING -> STRING
> %import common.SIGNED_NUMBER
> %import common.WS_INLINE
> %ignore WS_INLINE
>
> // ----------------------------------------------
> start             : statement+
> statement         : entity_def
>                   | relationship_def
>                   | insert_entity
>                   | connect_rel
>                   | update_stmt
>                   | delete_stmt
>                   | query_stmt
>
> // 1. Schema definition
> entity_def        : "ENTITY" CNAME "{" field_list "}" ["EXTENDS" CNAME] ";"
> field_list        : field_decl ("," field_decl)*
> field_decl        : CNAME ":" data_type
> data_type         : primitive_type
>                   | CNAME
>                   | CNAME "[]"          -> multi_ref
> primitive_type    : "STRING" | "INT" | "FLOAT" | "BOOL"
>                   | "DATE" | "DATETIME" | "BLOB" | "UUID" | "JSON"
>
> relationship_def  : "RELATIONSHIP" CNAME "(" CNAME mult? "->" CNAME mult? ")"
>                     ["{" field_list "}"] ";"
> mult              : "1" | "*"
>
> // 2. Data insertion
> insert_entity     : "INSERT" CNAME "{" assign_list "}" ["AS" alias] ";"
> alias             : CNAME
> assign_list       : assign ("," assign)*
> assign            : CNAME "=" literal_or_ref
> literal_or_ref    : literal | alias_or_id
> literal           : STRING | SIGNED_NUMBER | "TRUE" | "FALSE" | "NULL"
>
> connect_rel       : "CONNECT" alias_or_id "-" CNAME "->" alias_or_id
>                     ["{" assign_list "}"] ";"
>
> // 3. Updates / Deletes
> update_stmt       : "UPDATE" target_ref "SET" assign_list ";"
> delete_stmt       : "DELETE" target_ref ";"
> target_ref        : alias_or_id
>                   | CNAME "{" condition "}"
>
> condition         : prop_eq (("AND" | "OR") prop_eq)*
> prop_eq           : CNAME "=" literal
>
> // 4. Query
> query_stmt        : "MATCH" pattern ["WHERE" condition] ["RETURN" return_list] ";"
> pattern           : "(" node_pat ")" (edge_pat "(" node_pat ")")*
> node_pat          : [alias ":"] CNAME ["{" condition "}"]
> edge_pat          : "-" "[" [":" CNAME] [ "{" condition "}" ] "]" direction
> direction         : "->" | "<-" | "-"
> return_list       : return_item ("," return_item)*
> return_item       : CNAME ["." CNAME]
>
> // 5. Auxiliary
> alias_or_id       : alias | SIGNED_NUMBER
> ```
>
> ---
>
> ### 12  Quality checklist (the agent **must** ensure)
>
> 1. All source files pass `ruff` / `flake8` linting and `mypy` type checks.
> 2. `pytest -q` runs clean with PostgreSQL 15 + AGE ≥ 1.3.0.
> 3. No hard‑coded credentials; everything comes from `.env`.
> 4. Connections are closed gracefully on program exit.
> 5. Clear, human‑readable error messages propagate to CLI.
>
> ---
>
> **Deliverable**
> Output all files as concatenated code blocks, each preceded by a comment header of the form
> `# ===== file: path/to/file.py =====`.
> The first block must be `pyproject.toml`.
> Follow with instructions for the user to run tests and example scripts.
>
> **Begin now.**


