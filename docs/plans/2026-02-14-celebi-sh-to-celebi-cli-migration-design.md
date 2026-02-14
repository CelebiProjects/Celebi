# Design: Migrate celebi-cli to celebi-cli with manual command definitions

**Date**: 2026-02-14
**Author**: Claude Code
**Status**: Design Phase

## Overview

Migrate the `celebi-cli` command-line interface from automatic command generation to manual Click command definitions, renaming it to `celebi-cli` in the process. This involves creating a new `celebi_cli` folder structure with organized command modules and removing the dynamic generation system from `main.py`.

## Current Architecture

### Current State
- **Entry Point**: `celebi-cli = "CelebiChrono.main:sh"` in `pyproject.toml`
- **Command Generation**: Automatic generation from `_shell_commands` list in `main.py` (lines 291-337)
- **37 Commands**: Organized into categories but generated dynamically
- **Shell Implementation**: Functions in `interface/shell_modules/` (navigation, file_operations, etc.)
- **References**: Used in `.claude/settings.local.json` and test scripts

### Dynamic Generation System
The current system uses:
1. `_shell_commands` list with tuples: `(cmd_name, func_name, arg_count, description)`
2. `_make_command()` helper function that creates Click commands based on `arg_count`
3. Automatic help text extraction from shell function docstrings
4. Error handling wrappers around shell function calls

## Requirements

1. **Rename**: Change command prefix from `celebi-cli` to `celebi-cli`
2. **Manual Definitions**: Replace automatic generation with explicit Click command definitions
3. **Organization**: Create new `celebi_cli` folder with modular command structure
4. **No Backward Compatibility**: Completely replace `celebi-cli` (no alias)
5. **Functionality Preservation**: All 37 commands must work identically

## Design Approach

### 1. New Folder Structure
```
celebi_cli/
├── __init__.py
├── cli.py                    # Main CLI group
├── commands/
│   ├── __init__.py
│   ├── navigation.py        # cd, navigate, cd_project (7 commands)
│   ├── file_operations.py   # ls, mv, cp, rm (9 commands)
│   ├── object_creation.py   # create-algorithm, create-task (4 commands)
│   ├── task_configuration.py # add-input, add-algorithm (9 commands)
│   ├── execution_management.py # jobs, status, submit (8 commands)
│   ├── communication.py     # view, impress, config (7 commands)
│   └── visualization.py     # tree, error_log
└── utils.py                 # Helper functions
```

### 2. Command Migration Strategy

Each command will be manually defined with explicit Click decorators:

```python
# Example: ls command (arg_count = 999)
@click.command(name="ls")
@click.argument("args", nargs=-1, type=str)
def ls_command(args):
    """List the contents of a Celebi object.

    Without a path, lists the current object; with a path, lists the
    specified object within the current project.
    """
    from CelebiChrono.interface.shell import ls
    if args:
        result = ls(*args)
    else:
        result = ls("")
    if result is not None:
        if hasattr(result, 'colored'):
            print(result.colored())
        else:
            print(result)
```

### 3. Argument Handling Patterns

Based on `arg_count` values:
- `-1`: No arguments (`@click.command()` only)
- `0`: No arguments (`@click.command()` only)
- `1`: Single required argument (`@click.argument("arg", type=str)`)
- `2`: Two required arguments (`@click.argument("arg1", type=str)`, `@click.argument("arg2", type=str)`)
- `3`: Three required arguments
- `4`: Four required arguments
- `999`: Variable arguments (`@click.argument("args", nargs=-1, type=str)`)

### 4. Main CLI Group

```python
# celebi_cli/cli.py
import click
from .commands import navigation, file_operations, object_creation, task_configuration, execution_management, communication, visualization

@click.group()
def cli():
    """Celebi CLI commands for project management."""
    pass

# Register all commands
cli.add_command(navigation.cd_command)
cli.add_command(file_operations.ls_command)
# ... register all 37 commands
```

## Implementation Plan

### Phase 1: Create New Structure
1. Create `celebi_cli` directory and subdirectories
2. Create `__init__.py` files for packages
3. Create manual command definitions for all 37 commands
4. Organize commands by category matching `shell_modules`

### Phase 2: Update Entry Points
1. Update `pyproject.toml`: Change `celebi-cli` to `celebi-cli` with new import path
2. Remove `celebi-cli` entry point entirely
3. Update `main.py`: Remove `_shell_commands` list and dynamic generation code
4. Remove `cli_sh` group and `sh()` function from `main.py`

### Phase 3: Update References
1. Update `.claude/settings.local.json`: Replace `celebi-cli` with `celebi-cli`
2. Update test scripts referencing `celebi-cli`
3. Update documentation in `docs/plans/`
4. Update CI/CD configurations if any

### Phase 4: Testing
1. Test all 37 commands with `celebi-cli`
2. Verify `celebi-cli` no longer works
3. Test error handling and edge cases
4. Run existing test suite

## Command Categories

### Navigation (7 commands)
- `cd`, `tree`, `status`, `navigate`, `cdproject`, `short-ls`, `jobs`

### File Operations (9 commands)
- `ls`, `mv`, `cp`, `rm`, `rmfile`, `mvfile`, `import`, `send`, `add-input`

### Object Creation (4 commands)
- `create-algorithm`, `create-task`, `create-data`, `mkdir`

### Task Configuration (9 commands)
- `remove-input`, `add-algorithm`, `add-parameter`, `rm-parameter`, `add-parameter-subtask`, `set-env`, `set-mem`, `add-host`, `hosts`

### Execution Management (8 commands)
- `runners`, `register-runner`, `remove-runner`, `submit`, `collect`, `error-log`, `view`, `edit`

### Communication & Visualization (7 commands)
- `config`, `danger`, `trace`, `history`, `changes`, `preshell`, `postshell`, `impress`

## Critical Files

### Files to Modify
1. `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/main.py` - Remove lines 291-576
2. `/Users/zhaomr/workdir/Chern/Celebi/pyproject.toml` - Update line 48
3. `/Users/zhaomr/workdir/Chern/.claude/settings.local.json` - Update lines 16-23

### Files to Create
1. `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/` - Entire new structure
2. `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/cli.py` - Main CLI group
3. 8 command module files in `celebi_cli/commands/`

## Benefits

1. **Better Organization**: Commands organized in logical modules
2. **Explicit Control**: Manual definitions provide better control over behavior
3. **Improved Maintainability**: Easier to understand and modify individual commands
4. **Consistent Naming**: `celebi-cli` aligns with standard CLI naming conventions
5. **Cleaner Codebase**: Removes complex dynamic generation logic

## Risks and Mitigations

1. **Argument Handling Errors**: Carefully map `arg_count` to Click argument decorators
2. **Missing Commands**: Verify all 37 commands are migrated
3. **Behavior Changes**: Test each command to ensure identical behavior
4. **Reference Updates**: Search for all `celebi-cli` references in codebase

## Verification

1. `celebi-cli --help` shows all 37 commands
2. Each command produces same output as `celebi-cli`
3. Error messages match existing behavior
4. Integration tests pass
5. Documentation reflects new command name

## Dependencies

- Click framework (already dependency)
- Existing shell functions in `interface/shell_modules/`
- No new external dependencies required

## Timeline

Estimated effort: Medium (37 commands to migrate, multiple files to update)

## Approval

This design requires approval before implementation begins.