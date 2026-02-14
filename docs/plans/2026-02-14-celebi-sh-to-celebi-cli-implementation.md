# Celebi-sh to Celebi-cli Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate 37 shell commands from automatic generation in main.py to manual Click definitions in celebi_cli folder, renaming celebi-cli to celebi-cli.

**Architecture:** Create new celebi_cli/ folder with modular command organization matching shell_modules/. Replace dynamic generation with explicit Click decorators. Update entry points and references.

**Tech Stack:** Click framework, Python 3, existing CelebiChrono.interface.shell functions.

---

### Task 1: Create celebi_cli folder structure

**Files:**
- Create: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/__init__.py`
- Create: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/cli.py`
- Create: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/__init__.py`
- Create: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/navigation.py`
- Create: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/file_operations.py`
- Create: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/object_creation.py`
- Create: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/task_configuration.py`
- Create: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/execution_management.py`
- Create: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/communication.py`
- Create: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/visualization.py`
- Create: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/utils.py`

**Step 1: Create directory structure**

```bash
mkdir -p /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands
```

**Step 2: Create empty __init__.py files**

```bash
touch /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/__init__.py
touch /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/__init__.py
```

**Step 3: Create empty module files**

```bash
touch /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/cli.py
touch /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/navigation.py
touch /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/file_operations.py
touch /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/object_creation.py
touch /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/task_configuration.py
touch /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/execution_management.py
touch /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/communication.py
touch /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/visualization.py
touch /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/utils.py
```

**Step 4: Verify structure**

```bash
find /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli -type f -name "*.py" | sort
```
Expected: 11 Python files listed

**Step 5: Commit**

```bash
git add /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/
git commit -m "feat: create celebi_cli folder structure"
```

---

### Task 2: Create navigation commands (7 commands)

**Files:**
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/navigation.py`

**Commands to implement:**
1. `cd` (arg_count=1)
2. `tree` (arg_count=0)
3. `status` (arg_count=0)
4. `navigate` (arg_count=0)
5. `cdproject` (arg_count=1)
6. `short-ls` (arg_count=-1)
7. `jobs` (arg_count=-1)

**Step 1: Create navigation.py with imports**

```python
import click
import sys
from CelebiChrono.interface import shell

def _handle_result(result):
    """Helper to handle command result output."""
    if result is not None:
        if hasattr(result, 'colored'):
            print(result.colored())
        else:
            print(result)

def _handle_error(e):
    """Helper to handle errors."""
    print(f'Error executing Celebi command: {e}', file=sys.stderr)
    sys.exit(1)
```

**Step 2: Implement cd command (arg_count=1)**

```python
@click.command(name="cd")
@click.argument("path", type=str)
def cd_command(path):
    """Change directory within project.

    Changes the current working directory to a specified path or object within
    the current project. Supports both path-based navigation and numeric indices
    for quick access to recently viewed objects.
    """
    try:
        result = shell.cd(path)
        _handle_result(result)
    except ImportError as e:
        print(f'Error importing CelebiChrono module: {e}', file=sys.stderr)
        print('Make sure CelebiChrono is installed and in PYTHONPATH', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        _handle_error(e)
```

**Step 3: Implement tree command (arg_count=0)**

```python
@click.command(name="tree")
def tree_command():
    """Show tree view."""
    try:
        result = shell.tree()
        _handle_result(result)
    except ImportError as e:
        print(f'Error importing CelebiChrono module: {e}', file=sys.stderr)
        print('Make sure CelebiChrono is installed and in PYTHONPATH', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        _handle_error(e)
```

**Step 4: Implement remaining navigation commands**

Continue pattern for: `status`, `navigate`, `cdproject`, `short-ls`, `jobs`

**Step 5: Test navigation commands**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
python -c "import sys; sys.path.insert(0, '.'); from CelebiChrono.celebi_cli.commands.navigation import cd_command, tree_command; print('Navigation commands imported successfully')"
```
Expected: "Navigation commands imported successfully"

**Step 6: Commit**

```bash
git add /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/navigation.py
git commit -m "feat: implement navigation commands (cd, tree, status, navigate, cdproject, short-ls, jobs)"
```

---

### Task 3: Create file operations commands (9 commands)

**Files:**
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/file_operations.py`

**Commands to implement:**
1. `ls` (arg_count=999)
2. `mv` (arg_count=2)
3. `cp` (arg_count=2)
4. `rm` (arg_count=1)
5. `rmfile` (arg_count=1)
6. `mvfile` (arg_count=2)
7. `import` (arg_count=1)
8. `send` (arg_count=1)
9. `add-input` (arg_count=2)

**Step 1: Create file_operations.py with imports**

```python
import click
import sys
from CelebiChrono.interface import shell

def _handle_result(result):
    """Helper to handle command result output."""
    if result is not None:
        if hasattr(result, 'colored'):
            print(result.colored())
        else:
            print(result)

def _handle_error(e):
    """Helper to handle errors."""
    print(f'Error executing Celebi command: {e}', file=sys.stderr)
    sys.exit(1)
```

**Step 2: Implement ls command (arg_count=999)**

```python
@click.command(name="ls")
@click.argument("args", nargs=-1, type=str)
def ls_command(args):
    """List the contents of a Celebi object.

    Without a path, lists the current object; with a path, lists the
    specified object within the current project.
    """
    try:
        if args:
            result = shell.ls(*args)
        else:
            result = shell.ls("")
        _handle_result(result)
    except ImportError as e:
        print(f'Error importing CelebiChrono module: {e}', file=sys.stderr)
        print('Make sure CelebiChrono is installed and in PYTHONPATH', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        _handle_error(e)
```

**Step 3: Implement mv command (arg_count=2)**

```python
@click.command(name="mv")
@click.argument("src", type=str)
@click.argument("dst", type=str)
def mv_command(src, dst):
    """Move object."""
    try:
        result = shell.mv(src, dst)
        _handle_result(result)
    except ImportError as e:
        print(f'Error importing CelebiChrono module: {e}', file=sys.stderr)
        print('Make sure CelebiChrono is installed and in PYTHONPATH', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        _handle_error(e)
```

**Step 4: Implement remaining file operations commands**

Continue pattern for: `cp`, `rm`, `rmfile`, `mvfile`, `import`, `send`, `add-input`

**Step 5: Test file operations commands**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
python -c "import sys; sys.path.insert(0, '.'); from CelebiChrono.celebi_cli.commands.file_operations import ls_command, mv_command; print('File operations commands imported successfully')"
```
Expected: "File operations commands imported successfully"

**Step 6: Commit**

```bash
git add /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/file_operations.py
git commit -m "feat: implement file operations commands (ls, mv, cp, rm, rmfile, mvfile, import, send, add-input)"
```

---

### Task 4: Create remaining command modules

**Files:**
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/object_creation.py` (4 commands)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/task_configuration.py` (9 commands)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/execution_management.py` (8 commands)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/communication.py` (7 commands)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/visualization.py` (2 commands)

**Step 1: Implement object_creation.py (4 commands)**
- `create-algorithm` (arg_count=1)
- `create-task` (arg_count=1)
- `create-data` (arg_count=1)
- `mkdir` (arg_count=1)

**Step 2: Implement task_configuration.py (9 commands)**
- `remove-input` (arg_count=1)
- `add-algorithm` (arg_count=1)
- `add-parameter` (arg_count=2)
- `rm-parameter` (arg_count=1)
- `add-parameter-subtask` (arg_count=3)
- `set-env` (arg_count=1)
- `set-mem` (arg_count=1)
- `add-host` (arg_count=2)
- `hosts` (arg_count=0)

**Step 3: Implement execution_management.py (8 commands)**
- `runners` (arg_count=0)
- `register-runner` (arg_count=4)
- `remove-runner` (arg_count=1)
- `submit` (arg_count=1)
- `collect` (arg_count=1)
- `error-log` (arg_count=1)
- `view` (arg_count=1)
- `edit` (arg_count=1)

**Step 4: Implement communication.py (7 commands)**
- `config` (arg_count=0)
- `danger` (arg_count=1)
- `trace` (arg_count=1)
- `history` (arg_count=0)
- `changes` (arg_count=0)
- `preshell` (arg_count=0)
- `postshell` (arg_count=1)
- `impress` (arg_count=0)

**Step 5: Implement visualization.py (2 commands)**
- `tree` (already in navigation)
- `error-log` (already in execution_management)

**Step 6: Test all modules import**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
python -c "
import sys
sys.path.insert(0, '.')
try:
    from CelebiChrono.celebi_cli.commands.object_creation import *
    from CelebiChrono.celebi_cli.commands.task_configuration import *
    from CelebiChrono.celebi_cli.commands.execution_management import *
    from CelebiChrono.celebi_cli.commands.communication import *
    from CelebiChrono.celebi_cli.commands.visualization import *
    print('All command modules imported successfully')
except Exception as e:
    print(f'Import error: {e}')
    sys.exit(1)
"
```
Expected: "All command modules imported successfully"

**Step 7: Commit**

```bash
git add /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/commands/
git commit -m "feat: implement remaining command modules (object_creation, task_configuration, execution_management, communication, visualization)"
```

---

### Task 5: Create main CLI group

**Files:**
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/cli.py`

**Step 1: Create cli.py with imports**

```python
import click
from .commands import navigation, file_operations, object_creation, task_configuration, execution_management, communication, visualization

@click.group()
def cli():
    """Celebi CLI commands for project management."""
    pass

# Register navigation commands
cli.add_command(navigation.cd_command)
cli.add_command(navigation.tree_command)
cli.add_command(navigation.status_command)
cli.add_command(navigation.navigate_command)
cli.add_command(navigation.cdproject_command)
cli.add_command(navigation.short_ls_command)
cli.add_command(navigation.jobs_command)

# Register file operations commands
cli.add_command(file_operations.ls_command)
cli.add_command(file_operations.mv_command)
cli.add_command(file_operations.cp_command)
cli.add_command(file_operations.rm_command)
cli.add_command(file_operations.rmfile_command)
cli.add_command(file_operations.mvfile_command)
cli.add_command(file_operations.import_command)
cli.add_command(file_operations.send_command)
cli.add_command(file_operations.add_input_command)

# Register object creation commands
cli.add_command(object_creation.create_algorithm_command)
cli.add_command(object_creation.create_task_command)
cli.add_command(object_creation.create_data_command)
cli.add_command(object_creation.mkdir_command)

# Register task configuration commands
cli.add_command(task_configuration.remove_input_command)
cli.add_command(task_configuration.add_algorithm_command)
cli.add_command(task_configuration.add_parameter_command)
cli.add_command(task_configuration.rm_parameter_command)
cli.add_command(task_configuration.add_parameter_subtask_command)
cli.add_command(task_configuration.set_env_command)
cli.add_command(task_configuration.set_mem_command)
cli.add_command(task_configuration.add_host_command)
cli.add_command(task_configuration.hosts_command)

# Register execution management commands
cli.add_command(execution_management.runners_command)
cli.add_command(execution_management.register_runner_command)
cli.add_command(execution_management.remove_runner_command)
cli.add_command(execution_management.submit_command)
cli.add_command(execution_management.collect_command)
cli.add_command(execution_management.error_log_command)
cli.add_command(execution_management.view_command)
cli.add_command(execution_management.edit_command)

# Register communication commands
cli.add_command(communication.config_command)
cli.add_command(communication.danger_command)
cli.add_command(communication.trace_command)
cli.add_command(communication.history_command)
cli.add_command(communication.changes_command)
cli.add_command(communication.preshell_command)
cli.add_command(communication.postshell_command)
cli.add_command(communication.impress_command)

# Note: tree and error-log already registered from navigation and execution_management
```

**Step 2: Test CLI group**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
python -c "
import sys
sys.path.insert(0, '.')
from CelebiChrono.celebi_cli.cli import cli
print(f'CLI group created with {len(cli.commands)} commands')
"
```
Expected: "CLI group created with 37 commands"

**Step 3: Commit**

```bash
git add /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/celebi_cli/cli.py
git commit -m "feat: create main CLI group with all 37 commands"
```

---

### Task 6: Update pyproject.toml entry point

**Files:**
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/pyproject.toml`

**Step 1: Update line 48**

Current line 48: `celebi-cli = "CelebiChrono.main:sh"`

New line 48: `celebi-cli = "CelebiChrono.celebi_cli.cli:cli"`

**Step 2: Verify change**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
sed -n '48p' pyproject.toml
```
Expected: `celebi-cli = "CelebiChrono.celebi_cli.cli:cli"`

**Step 3: Test installation**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
pip install -e .
which celebi-cli
```
Expected: Path to celebi-cli executable

**Step 4: Commit**

```bash
git add /Users/zhaomr/workdir/Chern/Celebi/pyproject.toml
git commit -m "feat: update entry point from celebi-cli to celebi-cli"
```

---

### Task 7: Remove dynamic generation from main.py

**Files:**
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/main.py`

**Step 1: Remove _shell_commands list (lines 291-337)**

Delete lines 291-337 containing the `_shell_commands` list.

**Step 2: Remove dynamic generation loop (lines 339-576)**

Delete lines 339-576 containing the `for cmd_name, func_name, arg_count, description in _shell_commands:` loop.

**Step 3: Remove cli_sh group and sh() function**

Find and remove:
- `@click.group()` decorator for `cli_sh` (around line 285)
- `sh()` function definition (around line 287)

**Step 4: Keep cli group (lines 68-213)**

Ensure the `cli` group for primary commands remains unchanged.

**Step 5: Test main.py still works**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
python -c "
import sys
sys.path.insert(0, '.')
from CelebiChrono.main import cli
print('Main CLI group still works')
"
```
Expected: "Main CLI group still works"

**Step 6: Commit**

```bash
git add /Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/main.py
git commit -m "feat: remove dynamic command generation from main.py"
```

---

### Task 8: Update .claude/settings.local.json references

**Files:**
- Modify: `/Users/zhaomr/workdir/Chern/.claude/settings.local.json`

**Step 1: Replace celebi-cli with celebi-cli**

Lines 16-23 contain `celebi-cli` references:
- Line 16: `"Bash(celebi-cli tree:*)"` → `"Bash(celebi-cli tree:*)"`
- Line 17: `"Bash(celebi-cli ls:*)"` → `"Bash(celebi-cli ls:*)"`
- Line 20: `"Bash(celebi-cli short-ls:*)"` → `"Bash(celebi-cli short-ls:*)"`
- Line 21: `"Bash(celebi-cli jobs:*)"` → `"Bash(celebi-cli jobs:*)"`
- Line 22: `"Bash(celebi-cli navigate:*)"` → `"Bash(celebi-cli navigate:*)"`
- Line 23: `"Bash(celebi-cli:*)"` → `"Bash(celebi-cli:*)"`

**Step 2: Verify changes**

```bash
cd /Users/zhaomr/workdir/Chern
grep -n "celebi-" .claude/settings.local.json
```
Expected: Only `celebi-cli` references, no `celebi-cli`

**Step 3: Commit**

```bash
git add /Users/zhaomr/workdir/Chern/.claude/settings.local.json
git commit -m "feat: update .claude/settings.local.json references from celebi-cli to celebi-cli"
```

---

### Task 9: Test all 37 commands

**Step 1: Test celebi-cli --help**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
celebi-cli --help
```
Expected: Shows all 37 commands with descriptions

**Step 2: Test each command category**

```bash
# Test navigation
celebi-cli cd --help
celebi-cli tree --help
celebi-cli status --help

# Test file operations
celebi-cli ls --help
celebi-cli mv --help
celebi-cli cp --help

# Test object creation
celebi-cli create-algorithm --help
celebi-cli create-task --help

# Test task configuration
celebi-cli add-input --help
celebi-cli add-algorithm --help

# Test execution management
celebi-cli submit --help
celebi-cli collect --help

# Test communication
celebi-cli config --help
celebi-cli impress --help
```

**Step 3: Verify celebi-cli no longer works**

```bash
which celebi-cli || echo "celebi-cli not found (expected)"
```
Expected: "celebi-cli not found (expected)"

**Step 4: Run any existing tests**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
find . -name "*test*.py" -type f | head -5
# Run tests if they exist
```

**Step 5: Commit final verification**

```bash
git add -A
git commit -m "feat: complete celebi-cli to celebi-cli migration with all 37 commands tested"
```

---

## Verification Summary

1. **Command Count**: `celebi-cli --help` shows 37 commands
2. **Help Text**: Each command has proper help text from shell functions
3. **Argument Handling**: Commands accept correct number of arguments
4. **Error Handling**: Import errors and execution errors handled properly
5. **Output Formatting**: Colored output preserved where applicable
6. **Backward Compatibility**: `celebi-cli` command removed entirely
7. **References Updated**: `.claude/settings.local.json` uses `celebi-cli`

## Notes for Implementer

- Follow exact patterns from dynamic generation in main.py
- Maintain same error handling and output formatting
- Test each command with appropriate arguments
- Verify no regressions in functionality
- All 37 commands must work identically to celebi-cli version

