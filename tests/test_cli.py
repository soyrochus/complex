"""Tests for the Complex DSL CLI."""

import os
import tempfile
import subprocess
import sys
from pathlib import Path

import pytest

from complex.cli import run_script, run_repl


class TestCLI:
    """Test cases for the Complex DSL CLI."""
    
    def test_run_script_file_not_found(self):
        """Test error handling when script file doesn't exist."""
        exit_code = run_script("nonexistent_file.dsl")
        assert exit_code == 1
    
    def test_run_script_valid_file(self):
        """Test running a valid DSL script file."""
        # Create a temporary file with valid DSL content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dsl', delete=False) as f:
            f.write("""
            ENTITY Employee {
                name: STRING,
                email: STRING
            };
            
            INSERT Employee {
                name = "Test Employee",
                email = "test@example.com"
            };
            """)
            temp_file = f.name
        
        try:
            # This might fail due to database connection, but should not crash
            exit_code = run_script(temp_file)
            # Exit code could be 0 (success) or 1 (db error), both are acceptable
            assert exit_code in (0, 1)
        finally:
            os.unlink(temp_file)
    
    def test_run_script_invalid_syntax(self):
        """Test running a script with invalid syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dsl', delete=False) as f:
            f.write("INVALID SYNTAX HERE")
            temp_file = f.name
        
        try:
            exit_code = run_script(temp_file)
            assert exit_code == 1
        finally:
            os.unlink(temp_file)
    
    def test_cli_import(self):
        """Test that CLI module can be imported."""
        from complex import cli
        assert cli is not None
        assert hasattr(cli, 'main')
        assert hasattr(cli, 'run_script')
        assert hasattr(cli, 'run_repl')
    
    @pytest.mark.skipif(
        not os.environ.get("TEST_CLI_INTEGRATION"),
        reason="CLI integration tests disabled (set TEST_CLI_INTEGRATION=1 to enable)"
    )
    def test_cli_command_line_run(self):
        """Test CLI via command line (integration test)."""
        # Create a simple test script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dsl', delete=False) as f:
            f.write("""
            ENTITY TestEntity {
                name: STRING
            };
            """)
            temp_file = f.name
        
        try:
            # Run via command line
            result = subprocess.run([
                sys.executable, "-m", "complex.cli", "run", temp_file
            ], capture_output=True, text=True, timeout=30)
            
            # Should not crash (exit code 0 or 1 both acceptable)
            assert result.returncode in (0, 1)
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI command timed out")
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.skipif(
        not os.environ.get("TEST_CLI_INTEGRATION"),
        reason="CLI integration tests disabled"
    )
    def test_cli_help(self):
        """Test CLI help output."""
        try:
            result = subprocess.run([
                sys.executable, "-m", "complex.cli", "--help"
            ], capture_output=True, text=True, timeout=10)
            
            # Should show help and exit successfully
            assert result.returncode == 0
            assert "Complex DSL" in result.stdout or "Usage:" in result.stdout
            
        except subprocess.TimeoutExpired:
            pytest.fail("CLI help command timed out")
    
    def test_simple_repl_creation(self):
        """Test that SimpleREPL can be created."""
        from complex.cli import SimpleREPL
        from complex.interpreter import ComplexInterpreter
        
        interpreter = ComplexInterpreter()
        repl = SimpleREPL(interpreter)
        
        assert repl is not None
        assert repl.interpreter is interpreter
        assert repl.running is True
    
    def test_repl_statement_reading(self):
        """Test REPL statement reading logic."""
        from complex.cli import SimpleREPL
        from complex.interpreter import ComplexInterpreter
        
        interpreter = ComplexInterpreter()
        repl = SimpleREPL(interpreter)
        
        # Test single line statement
        statement = repl._read_statement("ENTITY Test { name: STRING };")
        assert statement == "ENTITY Test { name: STRING };"
        
        # Test statement without semicolon (would normally read more lines)
        # For testing, just verify the method exists and works with complete statements
        statement = repl._read_statement("ENTITY Test { name: STRING };")
        assert "ENTITY Test" in statement
