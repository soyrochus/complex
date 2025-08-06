import argparse
import os
import re
from typing import Optional

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
import psycopg2
from psycopg2.extras import RealDictCursor

# Load .env if present
load_dotenv()

def getenv(key, default):
    return os.environ.get(key, default)

DB_PARAMS = {
    "host": getenv("PGHOST", "localhost"),
    "port": int(getenv("PGPORT", 5432)),
    "dbname": getenv("PGDATABASE", "postgres"),
    "user": getenv("PGUSER", "postgres"),
    "password": getenv("PGPASSWORD", ""),
}
GRAPH_NAME = getenv("AGE_GRAPH", "demo")
DEFAULT_COLS = "(result agtype)"
HISTORY_FILE = os.path.expanduser("~/.cypher_repl_history")
DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful assistant that can query a PostgreSQL database with AGE "
    "extensions using Cypher. Use the send_cypher tool to run queries. "
    "When returning multiple items in a query (like nodes and relationships), "
    "use proper column names in the RETURN clause for better formatting. "
    "For example: 'RETURN n as node, r as relationship, m as target' instead of just 'RETURN n, r, m'."
)

OPENAI_API_KEY = getenv("OPENAI_API_KEY", None)
OPENAI_MODEL_NAME = getenv("OPENAI_MODEL_NAME", "gpt-4.1")
OPENAI_TEMPERATURE = float(getenv("OPENAI_TEMPERATURE", "0"))

INIT_STATEMENTS = [
    "CREATE EXTENSION IF NOT EXISTS age;",
    "LOAD 'age';",
    "SET search_path = ag_catalog, \"$user\", public;",
    f"SELECT create_graph('{GRAPH_NAME}');"
]

def parse_return_clause(query):
    """
    Parse the RETURN clause from a Cypher query to determine column definitions.
    Returns appropriate column definition string for AGE.
    """
    query = query.strip()
    
    # Look for RETURN clause (case insensitive)
    return_match = re.search(r'\bRETURN\s+(.+?)(?:\s+(?:ORDER|LIMIT|SKIP|UNION)|$)', query, re.IGNORECASE | re.DOTALL)
    
    if not return_match:
        # No RETURN clause, use default
        return DEFAULT_COLS
    
    return_clause = return_match.group(1).strip()
    
    # Split by comma and analyze each item
    items = [item.strip() for item in return_clause.split(',')]
    
    if len(items) == 1:
        # Single item, use default
        return DEFAULT_COLS
    
    # Multiple items - create column definitions
    cols = []
    for i, item in enumerate(items):
        # Check if item has an alias (AS keyword)
        alias_match = re.search(r'\s+AS\s+(\w+)', item, re.IGNORECASE)
        if alias_match:
            col_name = alias_match.group(1)
        else:
            # Try to extract variable name or use default
            var_match = re.search(r'(\w+)', item)
            if var_match:
                col_name = var_match.group(1)
            else:
                col_name = f"col{i+1}"
        
        cols.append(f"{col_name} agtype")
    
    return f"({', '.join(cols)})"

def preprocess_cypher_query(query):
    """
    Preprocess a Cypher query to make it compatible with AGE.
    Removes trailing semicolons which are not supported by AGE's cypher() function.
    """
    return query.strip().rstrip(';')

def split_cypher_statements(query):
    """
    Split a query string into individual Cypher statements.
    Returns a list of individual statements.
    """
    # Split by semicolons and filter out empty statements
    statements = [stmt.strip() for stmt in query.split(';') if stmt.strip()]
    return statements

def execute_cypher_with_smart_columns(cur, conn, query):
    """Execute a Cypher query with intelligent column detection"""
    # Split query into individual statements
    statements = split_cypher_statements(query)
    
    if len(statements) == 0:
        return True, []
    
    if len(statements) == 1:
        # Single statement - execute normally
        return execute_single_cypher_statement(cur, conn, statements[0])
    
    # Multiple statements - execute each one and collect results
    all_results = []
    for i, stmt in enumerate(statements):
        print(f"\n--- Statement {i+1} ---")
        success, result = execute_single_cypher_statement(cur, conn, stmt)
        if not success:
            return False, result  # Return error from first failed statement
        
        if result:  # Only add non-empty results
            all_results.extend(result)
        
        # Print result for each statement
        if result:
            print_result(result)
        else:
            print("(no results)")
    
    return True, all_results

def execute_single_cypher_statement(cur, conn, query):
    """Execute a single Cypher statement with intelligent column detection"""
    try:
        # Preprocess the query to remove trailing semicolons
        clean_query = preprocess_cypher_query(query)
        
        if not clean_query:  # Empty query after preprocessing
            return True, []
        
        # First, try with intelligent column detection
        col_def = parse_return_clause(clean_query)
        sql = f"SELECT * FROM cypher('{GRAPH_NAME}', $$ {clean_query} $$) AS {col_def};"
        
        try:
            cur.execute(sql)
            rows = cur.fetchall()
            conn.commit()
            return True, rows
        except Exception as e:
            # If smart columns fail, try with default
            if col_def != DEFAULT_COLS:
                conn.rollback()
                sql = f"SELECT * FROM cypher('{GRAPH_NAME}', $$ {clean_query} $$) AS {DEFAULT_COLS};"
                cur.execute(sql)
                rows = cur.fetchall()
                conn.commit()
                return True, rows
            else:
                raise e
                
    except Exception as e:
        conn.rollback()
        msg = str(e).split('\n')[0]
        return False, f"Cypher error: {msg}"

def format_rows(rows):
    if not rows:
        return "(no results)"
    keys = rows[0].keys()
    lines = ["\t".join(str(k) for k in keys)]
    for row in rows:
        lines.append("\t".join(str(row[k]) for k in keys))
    return "\n".join(lines)


def print_result(rows):
    print(format_rows(rows))


def log_print(prefix: str, text: str) -> None:
    for line in text.splitlines():
        print(f"[{prefix}] {line}")

def execute_cypher(cur, conn, query):
    """Execute a Cypher query and return success status"""
    success, result = execute_cypher_with_smart_columns(cur, conn, query)
    if success:
        print_result(result)
        return True
    else:
        print(result)  # result contains the error message
        return False

def load_and_execute_files(cur, conn, files):
    """Load and execute Cypher statements from files"""
    for file_path in files:
        print(f"\n--- Executing file: {file_path} ---")
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Split on semicolons and execute each statement
            statements = [stmt.strip() for stmt in content.split(';') if stmt.strip()]
            
            for i, stmt in enumerate(statements, 1):
                print(f"\nStatement {i}:")
                print(f"cypher> {stmt}")
                execute_cypher(cur, conn, stmt)
                
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found")
        except Exception as e:
            print(f"Error reading file '{file_path}': {e}")

def main():
    parser = argparse.ArgumentParser(description="Cypher REPL for AGE/PostgreSQL")
    parser.add_argument("files", nargs="*", help="Cypher files to load and execute")
    parser.add_argument(
        "-e",
        "--execute",
        action="store_true",
        help="Execute files and exit (do not start REPL)",
    )
    parser.add_argument(
        "-s",
        "--system-prompt",
        help="Path to a file containing a system prompt for the LLM",
    )

    args = parser.parse_args()

    print(f"Cypher REPL for AGE/PostgreSQL - graph: {GRAPH_NAME}")

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Initialization block
    for stmt in INIT_STATEMENTS:
        try:
            cur.execute(stmt)
            conn.commit()
        except Exception:
            conn.rollback()

    # Optional system prompt
    system_prompt = DEFAULT_SYSTEM_PROMPT
    if args.system_prompt:
        try:
            with open(args.system_prompt, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except OSError as e:
            print(f"Error reading system prompt file: {e}")

    log_enabled = False
    llm_enabled = True

    def parse_toggle(value: str) -> Optional[bool]:
        val = value.lower()
        if val in {"on", "true"}:
            return True
        if val in {"off", "false"}:
            return False
        return None

    def build_send_cypher():
        @tool
        def send_cypher(query: str) -> str:
            """Execute a Cypher query against the AGE/PostgreSQL database."""
            if log_enabled:
                log_print("TOOL", query)
            success, result = execute_cypher_with_smart_columns(cur, conn, query)
            if success:
                formatted = format_rows(result)
                if log_enabled:
                    log_print("DB", formatted)
                return formatted
            else:
                error_msg = str(result) if not isinstance(result, str) else result
                if log_enabled:
                    log_print("DB", error_msg)
                return error_msg

        return send_cypher

    def build_agent():
        send_cypher_tool = build_send_cypher()
        llm = ChatOpenAI(
            model=OPENAI_MODEL_NAME,
            temperature=OPENAI_TEMPERATURE,
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )
        agent = create_tool_calling_agent(llm, [send_cypher_tool], prompt)
        return AgentExecutor(agent=agent, tools=[send_cypher_tool])

    try:
        # Execute files if provided
        if args.files:
            load_and_execute_files(cur, conn, args.files)

        # Exit if --execute flag is set
        if args.execute:
            print("\nExecution complete.")
            return

        agent_executor = build_agent()

        # Start REPL (either after file execution or if no files provided)
        if not args.files:
            print("Enter adds a new line. Esc+Enter executes your Cypher query.")
        print("Use Ctrl+D or \\q to quit. \\h for list of commands.\n")

        session = PromptSession(
            history=FileHistory(HISTORY_FILE),
            multiline=True,
        )

        chat_history = []
        while True:
            try:
                text = session.prompt("cypher> ")
                stripped = text.strip()
                if not stripped:
                    continue
                if stripped == "\\q":
                    break
                if stripped == "\\h":
                    print("Available commands:")
                    print("  \\q              Quit the REPL")
                    print(
                        "  \\log [on|off]   Toggle logging of LLM and DB interactions"
                    )
                    print(
                        "  \\llm [on|off]   Toggle LLM usage (off executes Cypher directly)"
                    )
                    print("  \\h              Show this help message")
                    continue
                if stripped.startswith("\\log"):
                    parts = stripped.split(maxsplit=1)
                    if len(parts) == 2:
                        val = parse_toggle(parts[1])
                        if val is None:
                            print("Usage: \\log [on|off|true|false]")
                        else:
                            log_enabled = val
                            state = "enabled" if log_enabled else "disabled"
                            print(f"Logging {state}.")
                    else:
                        print("Usage: \\log [on|off|true|false]")
                    continue
                if stripped.startswith("\\llm"):
                    parts = stripped.split(maxsplit=1)
                    if len(parts) == 2:
                        val = parse_toggle(parts[1])
                        if val is None:
                            print("Usage: \\llm [on|off|true|false]")
                        else:
                            llm_enabled = val
                            state = "enabled" if llm_enabled else "disabled"
                            print(f"LLM {state}.")
                    else:
                        print("Usage: \\llm [on|off|true|false]")
                    continue

                if llm_enabled:
                    result = agent_executor.invoke(
                        {"input": text, "chat_history": chat_history}
                    )
                    output = result.get("output", "")
                    if output:
                        if log_enabled:
                            log_print("LLM", output)
                        else:
                            print(output)
                    chat_history.extend(
                        [HumanMessage(content=text), AIMessage(content=output)]
                    )
                else:
                    if log_enabled:
                        log_print("TOOL", text)
                    success, result = execute_cypher_with_smart_columns(
                        cur, conn, text
                    )
                    if success:
                        formatted = format_rows(result)
                        if log_enabled:
                            log_print("DB", formatted)
                        else:
                            print_result(result)
                    else:
                        error_msg = str(result) if not isinstance(result, str) else result
                        if log_enabled:
                            log_print("DB", error_msg)
                        else:
                            print(error_msg)
            except KeyboardInterrupt:
                print("\n(Use Ctrl+D or \\q to quit. \\h for list of commands)")
            except EOFError:
                print("\nExiting REPL.")
                break
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()

