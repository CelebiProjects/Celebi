# Design: Help System Long Description Modification

## Date
2026-02-13

## Author
Claude Code (via Claude Code CLI)

## Overview
This document outlines the modifications to standardize help text output for all `celebi-cli` commands to show only the long description (docstring without first line) instead of both short and long descriptions.

## Problem Statement
The current help system for `celebi-cli` commands has inconsistent behavior:

1. **Most commands** (`mv`, `cp`, `cd`, etc.) show both short and long descriptions:
   ```
   Usage: celebi-cli mv [OPTIONS] ARG1 ARG2

     Move or rename objects within the current project.

     Moves or renames Celebi objects (files, directories, tasks, algorithms, etc.)
     while preserving their relationships and metadata...
   ```

2. **Some commands** (`ls`, `tree`, etc.) show only the short description:
   ```
   Usage: celebi-cli ls [OPTIONS] [ARGS]...

     List the contents of a Celebi object.

   Options:
     --help  Show this message and exit.
   ```

This inconsistency occurs because:
- Commands with `expected_args` values 0-4 use `help=full_doc` (full docstring)
- Commands with other `expected_args` values (like `ls` with 999) use `help=desc` (short description only)

## Solution Approach
**Standardize all commands to show only the long description** by modifying the help text generation to exclude the first line of docstrings.

### Changes Required

1. **Modify `_get_command_docstring()` in `CelebiChrono/main.py`**:
   - Update the function to skip the first line when extracting docstrings
   - Preserve the rest of the docstring for detailed help text
   - Handle edge cases: empty docstrings, single-line docstrings

2. **Fix inconsistent command registration in `CelebiChrono/main.py`**:
   - Update the `else` clause (lines 543-572) to use `help=full_doc` instead of `help=desc`
   - Ensure all commands use the same help text generation logic

3. **Optional**: Update all command registrations to use `short_help=desc` and `help=full_doc` consistently

## Implementation Details

### Files to Modify

1. **`CelebiChrono/main.py`**:
   - Lines 280-307: `_get_command_docstring()` function
     - Current: Returns full docstring
     - New: Split by newline, skip first line, rejoin remaining lines
   - Lines 543-572: `else` clause for variable arguments
     - Current: `command_func = cli_sh.command(name=cname, help=desc)(command_func)`
     - New: Use `help=full_doc` or let Click use `__doc__` attribute

### Code Changes

**`_get_command_docstring()` modification**:
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
            # Rejoin remaining lines, preserving original formatting
            return '\n'.join(lines[1:]).strip()
        else:
            # Single-line docstring - return empty string
            return ""
    except Exception as e:
        return ""
```

**Command registration fix**:
```python
# Current line 572:
command_func = cli_sh.command(name=cname, help=desc)(command_func)

# New line 572:
command_func = cli_sh.command(name=cname, short_help=desc, help=full_doc)(command_func)
# OR remove help parameter to use __doc__ attribute:
# command_func = cli_sh.command(name=cname, help=desc)(command_func)  # Click will use __doc__
```

## Expected Behavior After Changes

**Before** (`mv` command):
```
Usage: celebi-cli mv [OPTIONS] ARG1 ARG2

  Move or rename objects within the current project.

  Moves or renames Celebi objects (files, directories, tasks, algorithms, etc.)
  while preserving their relationships and metadata...
```

**After** (`mv` command):
```
Usage: celebi-cli mv [OPTIONS] ARG1 ARG2

  Moves or renames Celebi objects (files, directories, tasks, algorithms, etc.)
  while preserving their relationships and metadata...
```

**Before** (`ls` command):
```
Usage: celebi-cli ls [OPTIONS] [ARGS]...

  List the contents of a Celebi object.

Options:
  --help  Show this message and exit.
```

**After** (`ls` command):
```
Usage: celebi-cli ls [OPTIONS] [ARGS]...

  Displays the object's structure including sub-objects (projects, tasks,
  algorithms, data objects). Shows README, sub-objects, and task information
  by default.

  Arguments:
      *args: Variable length argument list. Accepts 0 or 1 argument:
          - If no arguments: lists the current object
          - If one argument: treats it as a path to list (must be within
            the current project)

  Examples:
      ls                    # List current object
      ls /path/to/object    # List specific object within project
      ls @/subdir           # List object using project-relative path

Options:
  --help  Show this message and exit.
```

## Testing Strategy

1. **Verify all commands show consistent help format**:
   - Test commands with different `expected_args` values (0,1,2,3,4,999)
   - Ensure all show only long description (without first line)

2. **Edge case testing**:
   - Commands with single-line docstrings
   - Commands with empty docstrings
   - Commands with multi-paragraph docstrings

3. **Regression testing**:
   - Verify command functionality remains unchanged
   - Test interactive shell commands still work

## Future Considerations

1. **Documentation updates**: If the short descriptions are needed elsewhere, consider:
   - Keeping them in docstrings but marking them differently
   - Creating a separate metadata system for short descriptions

2. **User preferences**: Some users might prefer the short+long format
   - Could add configuration option for help format
   - Or make it command-line switch for `--help` vs `--help-long`

## Conclusion
Standardizing the help output to show only long descriptions improves consistency across all `celebi-cli` commands. The implementation modifies the docstring extraction logic and fixes inconsistent command registration, ensuring all commands use the same help text generation approach.