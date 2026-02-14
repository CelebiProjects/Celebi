# Design: Improved Help Text for `celebi-cli ls` Command

## Date
2026-02-13

## Author
Claude Code (via Claude Code CLI)

## Overview
This document outlines the improvements made to the help text for the `celebi-cli ls` command in the Celebi data analysis management toolkit.

## Problem Statement
The current help output for `celebi-cli ls --help` is minimal and lacks detail:
```
Usage: celebi-cli ls [OPTIONS]

  List contents

Options:
  --help  Show this message and exit.
```

Users need more comprehensive documentation to understand:
- What the command does in the Celebi context
- What information is displayed by default
- How to use the command effectively

## Solution Approach
**Enhanced with Path Argument Support** - Updated the help text and added functionality to accept an optional path argument for listing specific objects within the current project.

### Changes Made

1. **Updated command registration in `CelebiChrono/main.py`**:
   - Changed from: `('ls', 'ls', -1, 'List contents')`
   - Changed to: `('ls', 'ls', 999, 'List the contents of a Celebi object. Without a path, lists the current object; with a path, lists the specified object within the current project.')`
   - Changed `arg_count` from `-1` to `999` to enable variable arguments support

2. **Enhanced function implementation in `CelebiChrono/interface/shell.py`**:
   - Updated function signature from `ls(_: str)` to `ls(*args)` to accept variable arguments
   - Added path resolution and validation logic
   - Ensures paths are within the current project boundary
   - Added error handling for invalid paths and objects
   - Enhanced docstring with detailed documentation and examples

3. **Added import for `create_object_instance`** to properly instantiate Celebi objects

### New Help Text Output
```
Usage: celebi-cli ls [OPTIONS] [ARGS]...

  List the contents of a Celebi object. Without a path, lists the current
  object; with a path, lists the specified object within the current project.

Options:
  --help  Show this message and exit.
```

### New Functionality
- `ls` - Lists current object (backward compatible)
- `ls /path/to/object` - Lists specified object within current project
- `ls @/subdir` - Lists object using project-relative path
- Validates that path is within current project boundary
- Properly instantiates Celebi objects using `create_object_instance`

## Implementation Details

### Files Modified
1. `CelebiChrono/main.py` (line 222)
   - Updated the description in the `_shell_commands` list
   - Changed `arg_count` from `-1` to `999` to trigger variable arguments handler

2. `CelebiChrono/interface/shell.py` (function `ls`)
   - Updated function signature to accept variable arguments `(*args)`
   - Added path resolution using `csys.special_path_string()`
   - Added project boundary validation using `os.path.relpath()`
   - Added error handling for invalid paths and objects
   - Enhanced docstring with detailed documentation and examples
   - Added import for `create_object_instance`

3. `CelebiChrono/interface/shell.py` (imports)
   - Added `create_object_instance` import from `..interface.ChernManager`

### Key Implementation Points
- **Path Resolution**: Follows same pattern as `_cd_by_path` function
- **Project Boundary Check**: Ensures users can only list objects within current project
- **Object Instantiation**: Uses `create_object_instance` for proper Celebi object creation
- **Backward Compatibility**: `ls` without arguments still lists current object
- **Error Handling**: Provides clear error messages for invalid paths/objects

## Testing
The updated functionality was verified using test scripts that:

1. **Help Text Verification**:
   - Invokes `celebi-cli ls --help` programmatically
   - Confirms updated description and `[ARGS]...` parameter indication
   - Verifies backward compatibility of other commands (`short-ls`, `jobs`)

2. **Argument Handling Tests**:
   - `ls` without arguments: maintains existing behavior
   - `ls` with one argument: accepts path parameter
   - `ls` with multiple arguments: shows appropriate error message

3. **Path Validation Tests**:
   - Path resolution with `csys.special_path_string()`
   - Project-relative path handling (`@/` prefix)
   - Project boundary validation
   - Error handling for non-existent paths

4. **Integration Verification**:
   - Command registration with `arg_count = 999` triggers variable arguments handler
   - Proper object instantiation via `create_object_instance`
   - Exception handling for invalid Celebi objects

## Future Considerations
While basic path argument support has been added, further enhancements could include:

1. **Command-Line Options**: Add options corresponding to `LsParameters` fields (readme, predecessors, status, etc.) to give users more control over output format

2. **Recursive Listing**: Add `-R` flag for recursive listing of subdirectories

3. **Filtering Options**: Add pattern matching or type filtering (e.g., list only tasks or algorithms)

4. **Sorting Options**: Add sorting by name, modification time, or object type

5. **Output Format Control**: Add options for JSON, YAML, or machine-readable output formats

Any future enhancements should maintain backward compatibility with the current implementation.

## Conclusion
The enhanced `ls` command now provides both improved documentation and extended functionality:

1. **Better Documentation**: Clear, detailed help text explaining the command's purpose and usage
2. **Path Argument Support**: Ability to list specific objects within the current project
3. **Project Boundary Safety**: Validation ensures users can only access objects within the current project
4. **Backward Compatibility**: Existing usage (`ls` without arguments) continues to work unchanged
5. **Robust Error Handling**: Clear error messages for invalid paths, missing objects, and boundary violations

The implementation follows Celebi's existing patterns for path resolution and object instantiation, ensuring consistency with other commands while providing users with more flexible listing capabilities.