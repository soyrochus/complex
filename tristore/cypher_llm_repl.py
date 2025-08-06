import os
import argparse
import re
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

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

def execute_cypher_with_smart_columns(cur, conn, query):
    """Execute a Cypher query with intelligent column detection"""
    try:
        # First, try with intelligent column detection
        col_def = parse_return_clause(query)
        sql = f"SELECT * FROM cypher('{GRAPH_NAME}', $$ {query} $$) AS {col_def};"
        
        try:
            cur.execute(sql)
            rows = cur.fetchall()
            conn.commit()
            return True, rows
        except Exception as e:
            # If smart columns fail, try with default
            if col_def != DEFAULT_COLS:
                conn.rollback()
                sql = f"SELECT * FROM cypher('{GRAPH_NAME}', $$ {query} $$) AS {DEFAULT_COLS};"
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

    def build_send_cypher():
        @tool
        def send_cypher(query: str) -> str:
            """Execute a Cypher query against the AGE/PostgreSQL database."""
            success, result = execute_cypher_with_smart_columns(cur, conn, query)
            if success:
                return format_rows(result)
            else:
                return result  # result contains the error message

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
        print("Type \\q to quit.\n")

        session = PromptSession(
            history=FileHistory(HISTORY_FILE),
            multiline=True,
        )

        chat_history = []
        while True:
            try:
                text = session.prompt("cypher> ")
                if text.strip() == "\\q":
                    break
                if not text.strip():
                    continue
                result = agent_executor.invoke(
                    {"input": text, "chat_history": chat_history}
                )
                output = result.get("output", "")
                if output:
                    print(output)
                chat_history.extend(
                    [HumanMessage(content=text), AIMessage(content=output)]
                )
            except KeyboardInterrupt:
                print("\n(Use Ctrl+D or \\q to quit.)")
            except EOFError:
                print("\nExiting REPL.")
                break
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()

