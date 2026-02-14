# Help System Long Description Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Modify the help system to show only long descriptions (docstring without first line) for all `celebi-sh` commands.

**Architecture:** Update `_get_command_docstring()` function to skip first line of docstrings, and fix inconsistent command registration to use `help=full_doc` for all commands.

**Tech Stack:** Python, Click CLI framework, Celebi project structure

---

### Task 1: Modify _get_command_docstring() function

**Files:**
- Modify: `CelebiChrono/main.py:280-307`

**Step 1: Write the failing test**

First, create a test to verify the new behavior:

```python
# tests/test_help_system.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from CelebiChrono.main import _get_command_docstring

def test_get_command_docstring_skips_first_line():
    """Test that _get_command_docstring returns docstring without first line."""
    # Mock function with multi-line docstring
    class MockFunc:
        __doc__ = """Short description.

        Long description line 1.
        Long description line 2.

        Examples:
            Example 1
            Example 2
        """

    # Mock getattr to return our mock function
    import CelebiChrono.interface.shell as shell_module
    original_getattr = getattr

    def mock_getattr(obj, name):
        if obj == shell_module and name == "test_func":
            return MockFunc()
        return original_getattr(obj, name)

    # Temporarily patch getattr
    import builtins
    original_builtins_getattr = builtins.getattr
    builtins.getattr = mock_getattr

    try:
        result = _get_command_docstring("test_func")
        expected = """Long description line 1.
        Long description line 2.

        Examples:
            Example 1
            Example 2"""
        assert result.strip() == expected.strip(), f"Expected:\n{expected}\nGot:\n{result}"
    finally:
        builtins.getattr = original_builtins_getattr
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/zhaomr/workdir/Chern/Celebi && python -m pytest tests/test_help_system.py::test_get_command_docstring_skips_first_line -v`
Expected: FAIL with assertion error showing current function returns full docstring

**Step 3: Write minimal implementation**

Modify `_get_command_docstring()` in `CelebiChrono/main.py:280-307`:

```python
def _get_command_docstring(func_name: str) -> str:
    """Get long description from shell function (docstring without first line).

    Args:
        func_name: Name of the function in the shell module

    Returns:
        Docstring without first line, or empty string if not available
    """
    import sys
    try:
        from .interface import shell
        func = getattr(shell, func_name, None)
        if func is None:
            # print(f"DEBUG: Function {func_name} not found in shell module", file=sys.stderr)
            return ""

        docstring = func.__doc__
        if not docstring:
            result = ""
            # print(f"DEBUG: No docstring for {func_name}", file=sys.stderr)
            return result

        # Split docstring by lines
        lines = docstring.strip().split('\n')
        # Skip the first line (short description)
        if len(lines) > 1:
            # Rejoin remaining lines, preserving original formatting
            result = '\n'.join(lines[1:]).strip()
        else:
            # Single-line docstring - return empty string
            result = ""

        # print(f"DEBUG: Retrieved docstring for {func_name}, length: {len(result)}", file=sys.stderr)
        # if result: print(f"DEBUG: First 100 chars: {result[:100]}", file=sys.stderr)
        return result
    except Exception as e:
        # print(f"DEBUG: Error getting docstring for {func_name}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return ""
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/zhaomr/workdir/Chern/Celebi && python -m pytest tests/test_help_system.py::test_get_command_docstring_skips_first_line -v`
Expected: PASS

**Step 5: Commit**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
git add CelebiChrono/main.py tests/test_help_system.py
git commit -m "feat: modify _get_command_docstring to skip first line"
```

---

### Task 2: Fix command registration for variable arguments

**Files:**
- Modify: `CelebiChrono/main.py:543-572`

**Step 1: Write the failing test**

Add test for command registration consistency:

```python
# tests/test_help_system.py
def test_all_commands_use_full_doc():
    """Test that all command registrations use help=full_doc."""
    import CelebiChrono.main as main_module

    # Check that the else clause uses help=full_doc
    with open('CelebiChrono/main.py', 'r') as f:
        content = f.read()

    # Find the else clause for variable arguments
    import re
    else_clause_pattern = r'else:\s*\n(?:.*\n)*?\s*command_func = cli_sh\.command\(name=cname, help=desc\)\(command_func\)'
    match = re.search(else_clause_pattern, content, re.MULTILINE)

    assert match is None, "Found else clause using help=desc instead of help=full_doc"

    # Check that the correct pattern exists
    correct_pattern = r'command_func = cli_sh\.command\(name=cname, short_help=desc, help=full_doc\)\(command_func\)'
    assert re.search(correct_pattern, content) is not None, "Missing correct command registration pattern"
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/zhaomr/workdir/Chern/Celebi && python -m pytest tests/test_help_system.py::test_all_commands_use_full_doc -v`
Expected: FAIL with assertion error about else clause using `help=desc`

**Step 3: Write minimal implementation**

Modify the else clause in `CelebiChrono/main.py:543-572`:

Find line 572:
```python
            command_func = cli_sh.command(name=cname, help=desc)(command_func)
```

Change to:
```python
            command_func = cli_sh.command(name=cname, short_help=desc, help=full_doc)(command_func)
```

Also need to ensure `full_doc` is defined in this scope. Looking at the code structure, `full_doc` is already defined on line 566:
```python
            full_doc = _get_command_docstring(fname)
```

So the change is just updating line 572.

**Step 4: Run test to verify it passes**

Run: `cd /Users/zhaomr/workdir/Chern/Celebi && python -m pytest tests/test_help_system.py::test_all_commands_use_full_doc -v`
Expected: PASS

**Step 5: Commit**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
git add CelebiChrono/main.py
git commit -m "fix: standardize command registration to use help=full_doc"
```

---

### Task 3: Test help output for mv command

**Files:**
- Test: Run actual command to verify output

**Step 1: Write test script**

Create test script to verify help output:

```python
# tests/test_help_output.py
import subprocess
import sys

def test_mv_help_shows_only_long_description():
    """Test that celebi-sh mv --help shows only long description."""
    try:
        result = subprocess.run(
            ['celebi-sh', 'mv', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = result.stdout

        # Check that short description is NOT present
        short_desc = "Move or rename objects within the current project."
        assert short_desc not in output, f"Short description should not appear in help output:\n{output}"

        # Check that long description IS present
        long_desc_parts = [
            "Moves or renames Celebi objects",
            "while preserving their relationships and metadata",
            "Args:",
            "source (str): Path to the object to move or rename",
            "Examples:",
            "mv old_name new_name",
            "Note:",
            "Preserves link relationships and object metadata"
        ]

        for part in long_desc_parts:
            assert part in output, f"Long description part missing: {part}\nOutput:\n{output}"

        print("✓ mv help output shows only long description")

    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        print(f"stderr: {e.stderr}")
        raise
    except FileNotFoundError:
        print("celebi-sh command not found. Make sure Celebi is installed.")
        raise

if __name__ == "__main__":
    test_mv_help_shows_only_long_description()
```

**Step 2: Run test to verify current behavior**

Run: `cd /Users/zhaomr/workdir/Chern/Celebi && python tests/test_help_output.py`
Expected: FAIL because short description is still in output

**Step 3: Verify implementation works**

The implementation from Tasks 1-2 should handle this. Run test again:

Run: `cd /Users/zhaomr/workdir/Chern/Celebi && python tests/test_help_output.py`
Expected: PASS

**Step 4: Test ls command help output**

Add test for ls command:

```python
# tests/test_help_output.py
def test_ls_help_shows_long_description():
    """Test that celebi-sh ls --help shows long description."""
    try:
        result = subprocess.run(
            ['celebi-sh', 'ls', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = result.stdout

        # Check that long description IS present (previously was missing)
        long_desc_parts = [
            "Displays the object's structure",
            "sub-objects (projects, tasks, algorithms, data objects)",
            "Arguments:",
            "*args: Variable length argument list",
            "Examples:",
            "ls                    # List current object",
            "ls /path/to/object    # List specific object"
        ]

        for part in long_desc_parts:
            assert part in output, f"Long description part missing: {part}\nOutput:\n{output}"

        print("✓ ls help output shows long description")

    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        print(f"stderr: {e.stderr}")
        raise
    except FileNotFoundError:
        print("celebi-sh command not found. Make sure Celebi is installed.")
        raise

if __name__ == "__main__":
    test_mv_help_shows_only_long_description()
    test_ls_help_shows_long_description()
```

**Step 5: Run both tests**

Run: `cd /Users/zhaomr/workdir/Chern/Celebi && python tests/test_help_output.py`
Expected: Both tests PASS

**Step 6: Commit**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
git add tests/test_help_output.py
git commit -m "test: add help output verification tests"
```

---

### Task 4: Edge case handling

**Files:**
- Modify: `CelebiChrono/main.py:280-307` (update edge case handling)

**Step 1: Write edge case tests**

Add tests for edge cases:

```python
# tests/test_help_system.py
def test_get_command_docstring_single_line():
    """Test _get_command_docstring with single-line docstring."""
    class MockFunc:
        __doc__ = "Single line description."

    import CelebiChrono.interface.shell as shell_module
    import builtins

    original_getattr = builtins.getattr
    def mock_getattr(obj, name):
        if obj == shell_module and name == "single_line_func":
            return MockFunc()
        return original_getattr(obj, name)

    builtins.getattr = mock_getattr

    try:
        result = _get_command_docstring("single_line_func")
        assert result == "", f"Expected empty string for single-line docstring, got: {result}"
    finally:
        builtins.getattr = original_getattr

def test_get_command_docstring_empty():
    """Test _get_command_docstring with empty docstring."""
    class MockFunc:
        __doc__ = None

    import CelebiChrono.interface.shell as shell_module
    import builtins

    original_getattr = builtins.getattr
    def mock_getattr(obj, name):
        if obj == shell_module and name == "empty_func":
            return MockFunc()
        return original_getattr(obj, name)

    builtins.getattr = mock_getattr

    try:
        result = _get_command_docstring("empty_func")
        assert result == "", f"Expected empty string for None docstring, got: {result}"
    finally:
        builtins.getattr = original_getattr

def test_get_command_docstring_whitespace():
    """Test _get_command_docstring with whitespace-only lines."""
    class MockFunc:
        __doc__ = """Short.

        Long line 1.

        Long line 2.
        """

    import CelebiChrono.interface.shell as shell_module
    import builtins

    original_getattr = builtins.getattr
    def mock_getattr(obj, name):
        if obj == shell_module and name == "whitespace_func":
            return MockFunc()
        return original_getattr(obj, name)

    builtins.getattr = mock_getattr

    try:
        result = _get_command_docstring("whitespace_func")
        expected = "Long line 1.\n\nLong line 2."
        assert result.strip() == expected, f"Expected:\n{expected}\nGot:\n{result}"
    finally:
        builtins.getattr = original_getattr
```

**Step 2: Run edge case tests**

Run: `cd /Users/zhaomr/workdir/Chern/Celebi && python -m pytest tests/test_help_system.py::test_get_command_docstring_single_line tests/test_help_system.py::test_get_command_docstring_empty tests/test_help_system.py::test_get_command_docstring_whitespace -v`
Expected: Some may fail if edge cases not handled properly

**Step 3: Update implementation for edge cases**

Update `_get_command_docstring()` to better handle edge cases:

```python
def _get_command_docstring(func_name: str) -> str:
    """Get long description from shell function (docstring without first line).

    Args:
        func_name: Name of the function in the shell module

    Returns:
        Docstring without first line, or empty string if not available
    """
    import sys
    try:
        from .interface import shell
        func = getattr(shell, func_name, None)
        if func is None:
            return ""

        docstring = func.__doc__
        if not docstring:
            return ""

        # Split docstring by lines
        lines = docstring.strip().split('\n')

        # Skip the first line (short description)
        if len(lines) > 1:
            # Get remaining lines
            remaining_lines = lines[1:]
            # Remove leading empty lines
            while remaining_lines and not remaining_lines[0].strip():
                remaining_lines.pop(0)

            if remaining_lines:
                # Rejoin remaining lines
                result = '\n'.join(remaining_lines).strip()
                return result

        # Single-line docstring or only whitespace after first line
        return ""
    except Exception:
        return ""
```

**Step 4: Run edge case tests again**

Run: `cd /Users/zhaomr/workdir/Chern/Celebi && python -m pytest tests/test_help_system.py::test_get_command_docstring_single_line tests/test_help_system.py::test_get_command_docstring_empty tests/test_help_system.py::test_get_command_docstring_whitespace -v`
Expected: All PASS

**Step 5: Commit**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
git add CelebiChrono/main.py tests/test_help_system.py
git commit -m "fix: improve edge case handling in _get_command_docstring"
```

---

### Task 5: Verify all commands work

**Files:**
- Test: Run help for multiple commands

**Step 1: Create comprehensive test**

```python
# tests/test_all_commands_help.py
import subprocess
import sys

def test_command_help(command_name):
    """Test that a command's help shows only long description."""
    try:
        result = subprocess.run(
            ['celebi-sh', command_name, '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            print(f"✗ {command_name}: Command failed with return code {result.returncode}")
            print(f"stderr: {result.stderr}")
            return False

        output = result.stdout

        # Basic check: output should not be just the short description
        lines = output.strip().split('\n')
        help_lines = [line for line in lines if line.strip() and not line.startswith('Usage:') and not line.startswith('Options:')]

        if len(help_lines) < 2:
            print(f"✗ {command_name}: Help output too short (may be showing only short description)")
            print(f"Output:\n{output}")
            return False

        print(f"✓ {command_name}: Help output looks good ({len(help_lines)} lines of help text)")
        return True

    except subprocess.CalledProcessError as e:
        print(f"✗ {command_name}: Command failed: {e}")
        return False
    except FileNotFoundError:
        print("✗ celebi-sh command not found")
        return False
    except Exception as e:
        print(f"✗ {command_name}: Unexpected error: {e}")
        return False

def main():
    # Test a subset of commands that should have detailed help
    commands_to_test = [
        'mv', 'cp', 'cd', 'ls', 'tree', 'status',
        'rm', 'jobs', 'create-algorithm', 'create-task'
    ]

    print("Testing help output for commands...")
    print("=" * 50)

    passed = 0
    failed = 0

    for cmd in commands_to_test:
        if test_command_help(cmd):
            passed += 1
        else:
            failed += 1

    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Step 2: Run comprehensive test**

Run: `cd /Users/zhaomr/workdir/Chern/Celebi && python tests/test_all_commands_help.py`
Expected: Most commands PASS, some may fail if they have minimal docstrings

**Step 3: Check specific failing commands**

If any commands fail, check their docstrings in `shell.py` and update if needed. For example, check `tree` command:

Run: `cd /Users/zhaomr/workdir/Chern/Celebi && celebi-sh tree --help`
Check output. If it's minimal, the docstring may need updating.

**Step 4: Update minimal docstrings if necessary**

For commands with very short docstrings, consider updating them in `shell.py` to provide more detail. But this is optional - the goal is to show whatever long description exists.

**Step 5: Final verification**

Run the comprehensive test again:

Run: `cd /Users/zhaomr/workdir/Chern/Celebi && python tests/test_all_commands_help.py`
Expected: All commands that have multi-line docstrings should PASS

**Step 6: Commit**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
git add tests/test_all_commands_help.py
git commit -m "test: add comprehensive command help verification"
```

---

### Task 6: Clean up and final verification

**Files:**
- All modified files

**Step 1: Run all tests**

Run: `cd /Users/zhaomr/workdir/Chern/Celebi && python -m pytest tests/ -v`
Expected: All tests PASS

**Step 2: Manual verification**

Manually test a few commands:

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
celebi-sh mv --help
celebi-sh ls --help
celebi-sh cp --help
celebi-sh cd --help
```

Verify that:
1. Short description (first line) is NOT shown
2. Long description (rest of docstring) IS shown
3. Output looks clean and properly formatted

**Step 3: Check git status**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
git status
```

Should show only the test files and modified `main.py`.

**Step 4: Create final commit with all changes**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
git add -A
git commit -m "feat: standardize help system to show only long descriptions

- Modified _get_command_docstring() to skip first line of docstrings
- Fixed command registration to use help=full_doc for all commands
- Added comprehensive tests for help output verification
- All celebi-sh commands now show consistent long description format"
```

**Step 5: Summary**

Implementation complete. The help system now:
1. Shows only long descriptions (docstring without first line) for all commands
2. Has consistent behavior across all command types
3. Properly handles edge cases (empty, single-line, multi-line docstrings)
4. Includes comprehensive test coverage