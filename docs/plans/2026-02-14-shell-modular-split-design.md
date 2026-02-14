# Design: Shell Module Modular Split

## Objective
Split the monolithic `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py` (2079 lines, 62 functions) into smaller, logically organized modules while maintaining 100% backward compatibility.

## Current State Analysis
- **File**: `interface/shell.py` with 62 functions
- **Usage Patterns**:
  1. `main.py` uses `getattr(shell, func_name)` dynamically for CLI commands
  2. `commands_*.py` files use direct calls like `shell.mktask(obj)`
  3. Both relative (`from .interface import shell`) and absolute (`from CelebiChrono.interface import shell`) imports exist
- **Global Variable**: `MANAGER = get_manager()` used by all functions
- **Dependencies**: Functions depend on imports from `..utils`, `..kernel`, etc.

## Architecture Overview
The design splits the monolithic `shell.py` into 8 logically organized modules within a `shell_modules/` directory. The original `shell.py` becomes a forwarding stub for backward compatibility.

## Module Structure

### Core Modules (in `interface/shell_modules/` directory)

1. **`_manager.py`** - Shared manager instance
   ```python
   from ..interface.ChernManager import get_manager
   MANAGER = get_manager()
   ```

2. **`navigation.py`** (6 functions) - **Already implemented**
   - `cd_project`, `shell_cd_project`, `cd`, `_cd_by_index`, `_cd_by_path`, `navigate`

3. **`file_operations.py`** (14 functions)
   - `mv`, `cp`, `ls`, `successors`, `short_ls`, `rm`, `rm_file`, `mv_file`, `import_file`, `add_source`, `send`
   - Helper functions: `_normalize_paths`, `_validate_copy_operation`, `_adjust_destination_path`

4. **`object_creation.py`** (4 functions)
   - `mkalgorithm`, `mktask`, `mkdata`, `mkdir`

5. **`task_configuration.py`** (13 functions)
   - `add_source`, `jobs`, `status`, `add_input`, `add_algorithm`, `add_parameter`, `add_parameter_subtask`, `set_environment`, `set_memory_limit`, `rm_parameter`, `remove_input`, `get_script_path`, `config`

6. **`execution_management.py`** (6 functions)
   - `submit`, `purge`, `purge_old_impressions`, `collect`, `collect_outputs`, `collect_logs`

7. **`communication.py`** (9 functions)
   - `add_host`, `hosts`, `dite`, `set_dite`, `runners`, `register_runner`, `remove_runner`, `request_runner`, `search_impression`

8. **`visualization.py`** (4 functions)
   - `view`, `viewurl`, `impress`, `trace`

9. **`utilities.py`** (12 functions)
   - `workaround_preshell`, `workaround_postshell`, `history`, `watermark`, `changes`, `doctor`, `bookkeep`, `bookkeep_url`, `tree`, `error_log`, `danger_call`

### Export Modules

10. **`shell_modules/__init__.py`** - Package export
    ```python
    """
    Shell interface modules package.
    """
    # Re-export all functions from submodules
    from .navigation import *
    from .file_operations import *
    from .object_creation import *
    from .task_configuration import *
    from .execution_management import *
    from .communication import *
    from .visualization import *
    from .utilities import *

    # Export MANAGER for backward compatibility
    from ._manager import MANAGER
    ```

11. **Main `shell.py`** (at original `interface/shell.py`) - Forwarding stub
    ```python
    """
    Shell interface module for Chern project management.
    This module provides command-line interface functions.
    Maintains backward compatibility - forwards to modular implementation.
    """
    # Forward all imports to modular implementation
    from .shell_modules import *
    ```

## Export and Compatibility Strategy

### Export Structure
- `shell_modules/__init__.py` - Re-exports all functions from all 8 modules
- `shell.py` (original location) - Forwarding stub: `from .shell_modules import *`
- `_manager.py` - Shared `MANAGER = get_manager()` instance

### Backward Compatibility Guarantees
1. All 62 functions remain accessible via `shell.function_name`
2. Existing imports (`from .interface import shell` and `from CelebiChrono.interface import shell`) continue to work
3. Dynamic access via `getattr(shell, func_name)` in `main.py` continues to work
4. Direct calls in `commands_*.py` files continue to work
5. `shell.MANAGER` remains accessible

## Implementation Details

### Key Technical Details
1. Each module imports `MANAGER` from `._manager` instead of calling `get_manager()` directly
2. Each module preserves necessary imports from original `shell.py` (e.g., `from ..utils import csys`, `from ..kernel.vobject import VObject`)
3. Helper functions stay with their parent functions in the same module
4. The `send` function goes in `file_operations.py` (resolved from duplicate listing in plan)

### Risk Mitigations
- **Circular imports**: Use absolute imports within `shell/` directory
- **Dynamic function access**: Ensure `__init__.py` exports all 62 functions
- **MANAGER access**: Import from `._manager` in all modules
- **Import path changes**: Keep legacy `shell.py` stub at original location
- **Private helper functions**: Move helper functions with their parent functions

## Testing and Validation Plan

### Verification Steps
1. **Import Testing** - Test both relative and absolute imports work
2. **Function Coverage** - Verify all 62 functions accessible via `shell.function_name`
3. **MANAGER Access** - Ensure `shell.MANAGER` is not None
4. **Command Files Test** - Run each `commands_*.py` file
5. **Main Application Test** - Test CLI command loading and help system

### Success Criteria
- All 62 functions remain accessible
- Existing code runs without modification
- Both import styles continue to work
- `MANAGER` global remains accessible
- No regression in functionality

## Implementation Steps

### Phase 1: Preparation ✓ **COMPLETED**
1. **Backup**: Created backup of current `shell.py` as `shell.py.backup` ✓
2. **Create directory**: Created `interface/shell_modules/` ✓
3. **Create `_manager.py`**: In `shell_modules/` with `MANAGER = get_manager()` ✓

### Phase 2: Create Split Modules
4. **Copy functions**: For each module, create file in `shell_modules/` and copy relevant functions from original `shell.py`
5. **Update imports**: In each module, replace `MANAGER` reference with `from ._manager import MANAGER`
6. **Preserve original imports**: Copy necessary imports from original `shell.py` to each module

### Phase 3: Set Up Export Structure
7. **Create `shell_modules/__init__.py`**: Re-export all functions from submodules
8. **Update main `shell.py`**: Replace original with forwarding stub that imports from `.shell_modules`
9. **Update `interface/__init__.py`**: Ensure it re-exports the shell module correctly (if needed)

### Phase 4: Testing and Validation
10. **Test imports**: Verify both relative and absolute imports work
11. **Test dynamic access**: Ensure `getattr(shell, func_name)` works for all 62 functions
12. **Test direct calls**: Test `commands_*.py` files still work
13. **Test MANAGER access**: Verify `shell.MANAGER` is accessible
14. **Run existing tests**: Execute any test suite to ensure no regressions

## Critical Files to Modify
1. `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py` → Replace with forwarding stub
2. `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/__init__.py` → May need update for re-export
3. New files in `interface/shell_modules/` directory (10 files total)
   - `_manager.py` ✓ **COMPLETED**
   - `navigation.py` ✓ **COMPLETED**
   - `file_operations.py`, `object_creation.py`, `task_configuration.py`
   - `execution_management.py`, `communication.py`, `visualization.py`, `utilities.py`
   - `__init__.py` (for shell_modules package)

## Notes
- The original `shell.py` will be replaced with a forwarding stub that imports from `shell_modules`
- The new modular structure will live in `interface/shell_modules/` directory
- This refactoring is purely structural - no functional changes intended
- All existing imports (`from .interface import shell` and `from CelebiChrono.interface import shell`) will continue to work
- The `send` function is placed in `file_operations.py` (resolved from duplicate listing)

## Status
- Design approved: 2026-02-14
- Implementation started: Phase 1 completed, Phase 2 in progress
- Next step: Create implementation plan using writing-plans skill