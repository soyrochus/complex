"""Command-line interface for the Complex DSL library.

This module provides a CLI with commands to run scripts and start an interactive REPL.
"""

import sys
import os
from pathlib import Path
from typing import Optional

try:
    import click
except ImportError:
    click = None

from .interpreter import ComplexInterpreter
from .errors import ComplexError
from .db import close_db


class SimpleREPL:
    """Simple REPL implementation when advanced features are not available."""
    
    def __init__(self, interpreter: ComplexInterpreter) -> None:
        self.interpreter = interpreter
        self.running = True
    
    def run(self) -> None:
        """Run the REPL."""
        print("Complex DSL REPL")
        print("Type '.exit' to quit, '.help' for help")
        print()
        
        while self.running:
            try:
                # Read input (could be multi-line)
                line = input("complex> ")
                
                if not line.strip():
                    continue
                
                if line.strip() == ".exit":
                    self.running = False
                    break
                elif line.strip() == ".help":
                    self._show_help()
                    continue
                
                # Check if this looks like a multi-line statement
                script = self._read_statement(line)
                
                if script.strip():
                    results = self.interpreter.execute(script)
                    if results:
                        for result in results:
                            print(result)
                    else:
                        print("OK")
                
            except EOFError:
                self.running = False
                break
            except KeyboardInterrupt:
                print("\nUse '.exit' to quit")
                continue
            except ComplexError as e:
                print(f"Error: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")
    
    def _read_statement(self, first_line: str) -> str:
        """Read a complete statement, handling multi-line input."""
        lines = [first_line]
        
        # Simple heuristic: if line doesn't end with semicolon, read more
        while not first_line.rstrip().endswith(";"):
            try:
                line = input("     ... ")
                lines.append(line)
                if line.rstrip().endswith(";"):
                    break
            except (EOFError, KeyboardInterrupt):
                break
        
        return "\n".join(lines)
    
    def _show_help(self) -> None:
        """Show help information."""
        print("Complex DSL REPL Help")
        print("Commands:")
        print("  .exit    - Exit the REPL")
        print("  .help    - Show this help")
        print()
        print("Enter DSL statements followed by semicolons.")
        print("Multi-line statements are supported.")
        print()


def run_script(file_path: str) -> int:
    """Run a Complex DSL script from a file.
    
    Args:
        file_path: Path to the script file
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            return 1
        
        # Read script content
        with open(file_path, "r", encoding="utf-8") as f:
            script = f.read()
        
        # Create interpreter and execute
        interpreter = ComplexInterpreter()
        results = interpreter.execute(script)
        
        # Print results
        if results:
            for result in results:
                print(result)
        
        return 0
        
    except ComplexError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1
    finally:
        close_db()


def run_repl() -> int:
    """Run the interactive REPL.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        interpreter = ComplexInterpreter()
        repl = SimpleREPL(interpreter)
        repl.run()
        return 0
        
    except ComplexError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1
    finally:
        close_db()


# Click-based CLI (if click is available)
if click is not None:
    @click.group()
    def cli() -> None:
        """Complex DSL - A domain-specific language for graph data manipulation."""
        pass
    
    @cli.command()
    @click.argument("file_path", type=click.Path(exists=True))
    def run(file_path: str) -> None:
        """Run a Complex DSL script from a file."""
        exit_code = run_script(file_path)
        if exit_code != 0:
            sys.exit(exit_code)
    
    @cli.command()
    def repl() -> None:
        """Start an interactive REPL."""
        exit_code = run_repl()
        if exit_code != 0:
            sys.exit(exit_code)
    
    def main() -> None:
        """Main entry point for the CLI."""
        cli()

else:
    # Fallback CLI without click
    def main() -> None:
        """Main entry point for the CLI without click."""
        if len(sys.argv) < 2:
            print("Usage: complex <command> [args...]")
            print("Commands:")
            print("  run <file>  - Run a DSL script")
            print("  repl        - Start interactive REPL")
            sys.exit(1)
        
        command = sys.argv[1]
        
        if command == "run":
            if len(sys.argv) < 3:
                print("Error: 'run' command requires a file argument")
                sys.exit(1)
            file_path = sys.argv[2]
            exit_code = run_script(file_path)
            sys.exit(exit_code)
        
        elif command == "repl":
            exit_code = run_repl()
            sys.exit(exit_code)
        
        else:
            print(f"Error: Unknown command '{command}'")
            print("Available commands: run, repl")
            sys.exit(1)


if __name__ == "__main__":
    main()
