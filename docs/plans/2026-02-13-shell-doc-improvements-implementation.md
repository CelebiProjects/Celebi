# Shell Interface Documentation Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve documentation strings for all public functions in CelebiChrono/interface/shell.py following Google style format with consistent sections (Args, Returns, Examples, Note).

**Architecture:** Incremental standardization approach focusing on public functions only. Standardize existing good documentation first, then add missing sections to minimally documented functions, and finally create docstrings for undocumented functions.

**Tech Stack:** Python 3.7+, Google Python Style Guide, existing Celebi/Chern project structure.

---

## Overview

This plan implements the documentation improvements designed in `docs/plans/2026-02-13-shell-doc-improvements-design.md`. The `shell.py` module contains approximately 70 functions, with ~50 public functions requiring documentation improvements.

## Implementation Strategy

1. **Phase 1: Standardization** - Fix formatting and section headers for well-documented functions
2. **Phase 2: Completion** - Add missing sections to minimally documented functions
3. **Phase 3: Creation** - Create docstrings for undocumented functions
4. **Phase 4: Quality** - Enhance examples and notes, verify consistency

### Task 1: Analyze current documentation state

**Files:**
- Read: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py`
- Read: `/Users/zhaomr/workdir/Chern/Celebi/docs/plans/2026-02-13-shell-doc-improvements-design.md`

**Step 1: Read the shell.py file to understand current state**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
python -c "
import ast
with open('CelebiChrono/interface/shell.py') as f:
    tree = ast.parse(f.read())

functions = []
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        is_public = not node.name.startswith('_')
        has_docstring = ast.get_docstring(node) is not None
        functions.append({
            'name': node.name,
            'public': is_public,
            'has_doc': has_docstring,
            'lineno': node.lineno
        })

public_funcs = [f for f in functions if f['public']]
print(f'Total functions: {len(functions)}')
print(f'Public functions: {len(public_funcs)}')
print(f'Public with docstrings: {len([f for f in public_funcs if f[\"has_doc\"]])}')
print(f'Public without docstrings: {len([f for f in public_funcs if not f[\"has_doc\"]])}')
"
```

**Step 2: Categorize functions by documentation quality**

Create a Python script to analyze documentation quality:

```python
import ast
import re

def analyze_docstring(docstring):
    """Analyze docstring for required sections."""
    if not docstring:
        return {'has_doc': False}

    sections = {
        'has_args': bool(re.search(r'Args?:', docstring)),
        'has_returns': bool(re.search(r'Returns?:', docstring)),
        'has_examples': bool(re.search(r'Examples?:', docstring)),
        'has_note': bool(re.search(r'Note:', docstring)),
        'has_google_style': bool(re.search(r'Args?:?\n', docstring)),
    }
    sections['has_doc'] = True
    sections['completeness'] = sum(sections.values()) / 5.0
    return sections

with open('CelebiChrono/interface/shell.py') as f:
    tree = ast.parse(f.read())

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
        docstring = ast.get_docstring(node)
        analysis = analyze_docstring(docstring)
        print(f"{node.name:30} {'✓' if analysis.get('has_doc') else '✗'} "
              f"Args:{'✓' if analysis.get('has_args') else '✗'} "
              f"Returns:{'✓' if analysis.get('has_returns') else '✗'} "
              f"Examples:{'✓' if analysis.get('has_examples') else '✗'} "
              f"Note:{'✓' if analysis.get('has_note') else '✗'}")
```

**Step 3: Commit analysis results**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
git add docs/plans/2026-02-13-shell-doc-improvements-implementation.md
git commit -m "docs: add implementation plan for shell documentation improvements"
```

### Task 2: Create documentation template and utilities

**Files:**
- Create: `/Users/zhaomr/workdir/Chern/Celebi/scripts/doc_utils.py`

**Step 1: Create documentation utility functions**

```python
"""
Utilities for generating and validating Google-style docstrings.
"""

def generate_google_docstring(func_name, params, returns, description, examples, notes):
    """Generate a Google-style docstring template."""
    docstring = f'"""{description}\n\n'

    if params:
        docstring += 'Args:\n'
        for param_name, param_type, param_desc in params:
            docstring += f'    {param_name} ({param_type}): {param_desc}\n'
        docstring += '\n'

    if returns:
        docstring += f'Returns:\n    {returns}\n\n'

    if examples:
        docstring += 'Examples:\n'
        for example in examples:
            docstring += f'    {example}\n'
        docstring += '\n'

    if notes:
        docstring += 'Note:\n    '
        if isinstance(notes, list):
            docstring += '\n    '.join(notes)
        else:
            docstring += notes
        docstring += '\n'

    docstring += '"""'
    return docstring

def validate_google_docstring(docstring):
    """Validate a docstring against Google style requirements."""
    # Basic validation logic
    required_sections = ['Args', 'Returns', 'Examples', 'Note']
    missing = []

    for section in required_sections:
        if section.lower() not in docstring.lower():
            missing.append(section)

    return {
        'valid': len(missing) == 0,
        'missing_sections': missing,
        'has_triple_quotes': '"""' in docstring,
    }
```

**Step 2: Add test for documentation utilities**

```python
def test_generate_google_docstring():
    """Test docstring generation."""
    params = [('line', 'str', 'Path or index to navigate to')]
    returns = 'None'
    description = 'Change directory within current project.'
    examples = ['cd subdir  # Change to subdirectory', 'cd 2      # Change to index 2']
    notes = ['Project boundary safety enforced']

    docstring = generate_google_docstring(
        'cd', params, returns, description, examples, notes
    )

    assert 'Args:' in docstring
    assert 'Returns:' in docstring
    assert 'Examples:' in docstring
    assert 'Note:' in docstring
    assert 'line (str): Path or index to navigate to' in docstring
    print("✓ Docstring generation test passed")
```

**Step 3: Run the test**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
python -c "import sys; sys.path.insert(0, '.'); from scripts.doc_utils import test_generate_google_docstring; test_generate_google_docstring()"
```

**Step 4: Commit utilities**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
git add scripts/doc_utils.py
git commit -m "feat: add documentation utilities for Google-style docstrings"
```

### Task 3: Standardize navigation functions

**Files:**
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:28-38` (cd_project, shell_cd_project)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:40-67` (cd - already partially done)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:1034-1041` (navigate)

**Step 1: Standardize cd_project function**

Current function at line 28 needs docstring improvement:

```python
def cd_project(line: str) -> None:
    """Switch to a different project and change directory to its path.

    Changes the current working project and navigates to its root directory.
    This function updates both the Celebi project manager and the system
    working directory.

    Args:
        line (str): Name of the project to switch to.

    Examples:
        cd_project my_project      # Switch to project named 'my_project'
        cd_project analysis        # Switch to 'analysis' project

    Note:
        The project must exist in the Celebi project registry.
        Current working directory will change to the project's root path.
    """
    MANAGER.switch_project(line)
    os.chdir(MANAGER.current_object().path)
```

**Step 2: Standardize shell_cd_project function**

```python
def shell_cd_project(line: str) -> None:
    """Switch to a different project and print the new path.

    Changes the current working project and prints the absolute path
    to the project's root directory. This is the shell-version that
    outputs the path for shell integration.

    Args:
        line (str): Name of the project to switch to.

    Examples:
        shell_cd_project my_project  # Switch and print path to 'my_project'

    Note:
        Prints the absolute path to stdout for shell capture.
        Uses the same project validation as cd_project.
    """
    cd_project(line)
    print(MANAGER.current_object().path)
```

**Step 3: Verify cd function is already standardized**

Check that the cd function (lines 40-67) already has proper Google-style docstring.
If not, update to match the standardized format.

**Step 4: Standardize navigate function**

```python
def navigate() -> str:
    """Return the path of the current project.

    Retrieves the absolute filesystem path of the currently active
    Celebi project. This is useful for shell scripts and external
    tools that need to know the project location.

    Returns:
        Absolute path to the current project's root directory.

    Examples:
        project_path = navigate()  # Get current project path
        cd $(navigate)/subdir     # Use in shell command

    Note:
        Returns empty string if no project is currently active.
        Requires the ChernProjectManager to be initialized.
    """
    from ..interface.ChernManager import ChernProjectManager
    manager = ChernProjectManager().get_manager()
    project_name = manager.get_current_project()
    return manager.get_project_path(project_name)
```

**Step 5: Test the navigation functions**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
python -c "
import sys
sys.path.insert(0, '.')
# Simple syntax check
exec(open('CelebiChrono/interface/shell.py').read())
print('✓ Navigation functions syntax check passed')
"
```

**Step 6: Commit navigation function improvements**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
git add CelebiChrono/interface/shell.py
git commit -m "docs: standardize navigation function docstrings to Google style"
```

### Task 4: Standardize file operation functions

**Files:**
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:168-208` (mv - already partially done)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:209-254` (cp - already partially done)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:256-313` (ls)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:315-327` (successors)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:329-332` (short_ls)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:433-467` (rm)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:469-488` (rm_file)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:490-498` (mv_file)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:518-540` (import_file)

**Step 1: Verify mv and cp are already standardized**

Check lines 168-254 for mv and cp functions. Ensure they follow Google style completely.

**Step 2: Standardize ls function**

```python
def ls(*args):
    """List the contents of a Celebi object.

    Displays the object's structure including sub-objects (projects, tasks,
    algorithms, data objects). Shows README, sub-objects, and task information
    by default.

    Args:
        *args: Variable length argument list. Accepts 0 or 1 argument:
            - If no arguments: lists the current object
            - If one argument: treats it as a path to list (must be within
              the current project)

    Returns:
        Message object with listing results or None if error occurs.

    Examples:
        ls                    # List current object
        ls /path/to/object    # List specific object within project
        ls @/subdir           # List object using project-relative path

    Note:
        Returns None if path is outside project bounds or object doesn't exist.
        Uses LsParameters configuration for display options.
    """
    if len(args) == 0:
        # No path provided, list current object
        return MANAGER.current_object().ls()
    elif len(args) == 1:
        path = args[0]
        # Resolve and validate the path
        path = csys.special_path_string(path)
        if path.startswith("@/") or path == "@":
            path = os.path.normpath(csys.project_path() + path.strip("@"))
        else:
            path = os.path.abspath(path)

        # Check if path is within current project
        try:
            if os.path.relpath(path, csys.project_path()).startswith(".."):
                # print("[ERROR] Unable to list object outside the current project.")
                return None
        except Exception as e:
            # print(f"[ERROR] Failed to validate path: {e}")
            return None

        # Check if object exists
        if not csys.exists(path):
            # print(f"[ERROR] Object not found: {path}")
            return None

        # Get the object and list it
        try:
            return create_object_instance(path).ls()
        except Exception as e:
            # print(f"[ERROR] Failed to list object: {e}")
            msg = Message()
            msg.add(f"Failed to list object: {e}", "error")
            return msg
    else:
        # print("[ERROR] ls takes at most one argument (path)")
        msg = Message()
        msg.add("ls takes at most one argument (path)", "error")
        return msg
```

**Step 3: Standardize successors function**

```python
def successors() -> Message:
    """List the successors of the current object.

    Displays objects that depend on or follow from the current object
    in the workflow graph. Successors represent downstream dependencies
    in task execution chains.

    Returns:
        Message containing list of successor objects with their metadata.

    Examples:
        successors()  # List all successors of current object

    Note:
        Only shows direct successors, not transitive dependencies.
        Returns empty message if no successors exist.
    """
    return MANAGER.current_object().ls(
        LsParameters(
            readme=False,
            successors=True,
            predecessors=False,
            status=False,
            sub_objects=False,
            task_info=False,
        )
    )
```

**Step 4: Standardize short_ls function**

```python
def short_ls(_: str) -> None:
    """Show short listing of the current object.

    Displays a compact summary of the current object's contents
    without detailed metadata. Useful for quick overviews in
    directories with many objects.

    Args:
        _ (str): Unused parameter maintained for interface consistency.

    Examples:
        short_ls ''  # Show compact listing (empty string as parameter)

    Note:
        Parameter is unused but required for command interface compatibility.
        Shows only object names and types, not detailed metadata.
    """
    MANAGER.current_object().short_ls()
```

**Step 5: Standardize rm function**

```python
def rm(line: str) -> None:
    """Remove objects (files, directories, tasks, algorithms) from the project.

    Deletes Celebi objects from the current project. The operation is validated
    to ensure project integrity and prevent accidental deletion of critical
    components.

    Args:
        line (str): Path to the object to remove.

    Examples:
        rm file.txt              # Remove file
        rm directory/            # Remove directory
        rm @/path/to/object      # Remove using project-relative path

    Note:
        - Cannot remove the current project root
        - Cannot remove objects outside the project boundary
        - Some objects may be protected from deletion
        - Returns Message with deletion results
    """
    line = os.path.abspath(line)
    # Deal with the illegal operation
    if line == csys.project_path():
        print("Unable to remove project")
        return
    if os.path.relpath(line, csys.project_path()).startswith(".."):
        print("Unable to remove directory outside the project")
        return
    if not csys.exists(line):
        print("File not exists")
        return
    result = VObject(line).rm()
    if result.messages:  # If there are error messages
        print(result.colored())
```

**Step 6: Test file operation functions**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
python -m py_compile CelebiChrono/interface/shell.py
echo "✓ File operation functions syntax check passed"
```

**Step 7: Commit file operation improvements**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
git add CelebiChrono/interface/shell.py
git commit -m "docs: standardize file operation function docstrings"
```

### Task 5: Standardize object creation functions

**Files:**
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:334-363` (mkalgorithm)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:365-392` (mktask)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:394-403` (mkdata)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:405-431` (mkdir)

**Step 1: Verify mkalgorithm is already standardized**

Check lines 334-363. Update if needed.

**Step 2: Standardize mktask function**

```python
def mktask(line: str) -> None:
    """Create a new task object.

    Creates a new task within the current project. Tasks are executable units
    that combine inputs, algorithms, and parameters to produce outputs.
    Tasks can be submitted for execution and tracked through their lifecycle.

    Args:
        line (str): Path where the task should be created. Must be within
            a valid directory or project location.

    Examples:
        create-task my_task           # Create task at my_task/
        create-task path/to/task      # Create at specific path
        create-task @/tasks/new       # Use project-relative path

    Note:
        Tasks can only be created within directories or projects,
        not within other object types like algorithms or data objects.
        Initializes with default task configuration.
    """
    line = csys.refine_path(line, MANAGER.current_object().path)
    parent_path = os.path.abspath(line+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("directory", "project"):
        print("Not allowed to create task here")
        return
    create_task(line)
```

**Step 3: Standardize mkdata function**

```python
def mkdata(line: str) -> None:
    """Create a new data task object.

    Creates a specialized task object designed for data storage and
    management. Data tasks are optimized for handling input/output
    data rather than computational execution.

    Args:
        line (str): Path where the data task should be created.

    Examples:
        create-data my_data           # Create data task at my_data/
        create-data path/to/data      # Create at specific path

    Note:
        Data tasks have different configuration than regular tasks.
        Primarily used for data storage and organization in workflows.
    """
    line = csys.refine_path(line, MANAGER.current_object().path)
    parent_path = os.path.abspath(line+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("directory", "project"):
        print("Not allowed to create task here")
        return
    create_data(line)
```

**Step 4: Verify mkdir is already standardized**

Check lines 405-431. Update if needed.

**Step 5: Test object creation functions**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
python -c "
import ast
with open('CelebiChrono/interface/shell.py') as f:
    content = f.read()
    # Check for required sections in object creation functions
    functions_to_check = ['mkalgorithm', 'mktask', 'mkdata', 'mkdir']
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in functions_to_check:
            docstring = ast.get_docstring(node)
            if docstring:
                print(f'✓ {node.name} has docstring')
                if 'Args:' in docstring: print(f'  - Has Args section')
                if 'Examples:' in docstring: print(f'  - Has Examples section')
                if 'Note:' in docstring: print(f'  - Has Note section')
            else:
                print(f'✗ {node.name} missing docstring')
"
```

**Step 6: Commit object creation improvements**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
git add CelebiChrono/interface/shell.py
git commit -m "docs: standardize object creation function docstrings"
```

### Task 6: Standardize task configuration functions

**Files:**
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:500-503` (add_source)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:505-512` (jobs)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:514-517` (status)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:542-610` (add_input)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:612-627` (add_algorithm)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:629-644` (add_parameter)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:645-655` (add_parameter_subtask)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:656-671` (set_environment)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:673-688` (set_memory_limit)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:690-696` (rm_parameter)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:698-713` (remove_input)

**Step 1: Standardize add_source function**

```python
def add_source(line: str) -> None:
    """Add a source to the current object.

    Links an external file or data source to the current Celebi object.
    Sources represent input dependencies that are tracked for provenance.

    Args:
        line (str): Path to the source file or object to add.

    Examples:
        add_source data/input.txt      # Add file as source
        add_source @/other_task/output # Add task output as source

    Note:
        Sources are tracked for dependency analysis and reproducibility.
        The source must exist within the project or accessible path.
    """
    MANAGER.current_object().add_source(line)
```

**Step 2: Standardize jobs function**

```python
def jobs(_: str) -> None:
    """Show jobs for current algorithm or task.

    Displays execution jobs associated with the current algorithm or task.
    Jobs represent individual runs or instances of task execution.

    Args:
        _ (str): Unused parameter maintained for interface consistency.

    Examples:
        jobs ''  # Show jobs for current object (empty string as parameter)

    Note:
        Only works within task or algorithm objects.
        Shows job status, IDs, and execution metadata.
    """
    object_type = MANAGER.current_object().object_type()
    if object_type not in ("algorithm", "task"):
        print("Not able to found job")
        return
    MANAGER.current_object().jobs()
```

**Step 3: Standardize status function**

```python
def status():
    """Show status of current object.

    Displays the current state and health information for the object.
    Includes execution status, validation results, and metadata checks.

    Returns:
        Message object with formatted status information.

    Examples:
        status()  # Display current object status

    Note:
        Status information varies by object type (task, algorithm, etc.).
        Includes both static configuration and dynamic runtime state.
    """
    return MANAGER.current_object().printed_status()
```

**Step 4: Verify add_input is already standardized**

Check lines 542-610. This function already has good documentation.

**Step 5: Standardize add_algorithm function**

```python
def add_algorithm(path: str) -> None:
    """Add an algorithm to current task.

    Links an algorithm object to the current task for execution.
    The algorithm defines the computational procedure to run.

    Args:
        path (str): Path to the algorithm object to add.

    Examples:
        add_algorithm @/algorithms/process  # Add algorithm from project path
        add_algorithm ../algos/transform    # Add relative algorithm

    Note:
        Current object must be a task (not algorithm or directory).
        Algorithm must exist and be valid for execution.
        Replaces any previously set algorithm.
    """
    if MANAGER.current_object().object_type() == "directory":
        sub_objects = MANAGER.current_object().sub_objects()
        for obj in sub_objects:
            if obj.object_type() != "task":
                continue
            obj_path = MANAGER.current_object().relative_path(obj.path)
            task = MANAGER.sub_object(obj_path)
            task.add_algorithm(path)
        return
    if MANAGER.current_object().object_type() != "task":
        print("Unable to call add_algorithm if you are not in a task.")
        return
    MANAGER.current_object().add_algorithm(path)
```

**Step 6: Test task configuration functions**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
python -c "
# Quick syntax check for task configuration functions
import sys
sys.path.insert(0, '.')
try:
    exec(open('CelebiChrono/interface/shell.py').read())
    print('✓ Task configuration functions syntax check passed')
except SyntaxError as e:
    print(f'✗ Syntax error: {e}')
    sys.exit(1)
"
```

**Step 7: Commit task configuration improvements**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
git add CelebiChrono/interface/shell.py
git commit -m "docs: standardize task configuration function docstrings"
```

### Task 7: Standardize execution management functions

**Files:**
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:798-826` (submit)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:827-840` (purge)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:841-854` (purge_old_impressions)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:961-985` (collect)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:986-1000` (collect_outputs)
- Modify: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py:1001-1015` (collect_logs)

**Step 1: Verify submit is already standardized**

Check lines 798-826. Update Returns section to focus on content.

**Step 2: Standardize purge function**

```python
def purge():
    """Purge temporary files and cleanup current object.

    Removes temporary files, cache data, and other non-essential artifacts
    associated with the current object. This helps free up disk space and
    resolve potential consistency issues.

    Returns:
        Message with purge results and cleanup statistics.

    Examples:
        purge()  # Clean up temporary files for current object

    Note:
        The exact behavior depends on the object type.
        Some objects may have protected data that cannot be purged.
        Use with caution as purged data cannot be recovered.
    """
    message = MANAGER.current_object().purge()
    print(message.colored())
```

**Step 3: Standardize purge_old_impressions function**

```python
def purge_old_impressions():
    """Purge old impression data from current object.

    Removes historical impression data that is no longer needed, preserving
    only recent or essential impressions. Impressions are visualization
    or snapshot data generated during task execution.

    Returns:
        Message with purge statistics and removed impression details.

    Examples:
        purge_old_impressions()  # Remove outdated impressions

    Note:
        The age threshold for 'old' impressions is configurable.
        Some impression data may be protected from deletion.
        Helps manage storage usage for long-running projects.
    """
    message = MANAGER.current_object().purge_old_impressions()
    print(message.colored())
```

**Step 4: Verify collect functions are already standardized**

Check lines 961-1015. Update Returns sections to focus on content.

**Step 5: Test execution management functions**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
python -c "
# Validate docstring structure for execution functions
import ast
with open('CelebiChrono/interface/shell.py') as f:
    tree = ast.parse(f.read())

exec_functions = ['submit', 'purge', 'purge_old_impressions',
                  'collect', 'collect_outputs', 'collect_logs']

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name in exec_functions:
        docstring = ast.get_docstring(node)
        if docstring and 'Returns:' in docstring:
            # Check Returns doesn't just say 'Message object'
            if 'Message object' in docstring and len(docstring.split('Returns:')) > 1:
                returns_section = docstring.split('Returns:')[1].split('\\n')[0].strip()
                if 'Message' not in returns_section or len(returns_section) > 20:
                    print(f'✓ {node.name}: Returns describes content')
                else:
                    print(f'✗ {node.name}: Returns needs content description')
"
```

**Step 6: Commit execution management improvements**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
git add CelebiChrono/interface/shell.py
git commit -m "docs: standardize execution management function docstrings"
```

### Task 8: Standardize remaining utility functions

**Files:** Various locations for remaining ~20 public functions.

**Step 1: Create checklist of remaining functions**

```python
import ast
with open('CelebiChrono/interface/shell.py') as f:
    tree = ast.parse(f.read())

remaining = []
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
        docstring = ast.get_docstring(node)
        if not docstring or 'Args:' not in docstring or 'Examples:' not in docstring:
            remaining.append(node.name)

print(f"Remaining functions to standardize: {len(remaining)}")
print(", ".join(remaining))
```

**Step 2: Batch process remaining functions**

Based on output, create docstrings for each remaining function following the same pattern.

**Step 3: Final syntax check**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
python -m py_compile CelebiChrono/interface/shell.py
echo "✓ Final syntax check passed"
```

**Step 4: Commit all remaining improvements**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
git add CelebiChrono/interface/shell.py
git commit -m "docs: standardize all remaining public function docstrings"
```

### Task 9: Final verification and quality check

**Files:**
- Read: `/Users/zhaomr/workdir/Chern/Celebi/CelebiChrono/interface/shell.py`
- Test: Create validation script

**Step 1: Create comprehensive validation script**

```python
"""
Validate all public function docstrings meet Google style requirements.
"""
import ast
import re

def validate_function_docstring(func_node):
    """Validate a single function's docstring."""
    docstring = ast.get_docstring(func_node)

    if not docstring:
        return {'valid': False, 'errors': ['Missing docstring']}

    errors = []

    # Check for required sections
    required_sections = ['Args', 'Returns', 'Examples', 'Note']
    for section in required_sections:
        if section == 'Returns' and func_node.returns is None:
            continue  # Skip Returns for functions returning None
        if not re.search(f'{section}:', docstring):
            errors.append(f'Missing {section} section')

    # Check Args format if function has parameters
    if func_node.args.args and 'Args:' in docstring:
        # Simple check for parameter documentation
        args_section = re.search(r'Args:.*?(?=\n\n|\Z)', docstring, re.DOTALL)
        if args_section:
            args_text = args_section.group(0)
            # Should have at least one parameter documented
            param_lines = [l for l in args_text.split('\n') if '):' in l]
            if len(param_lines) < len(func_node.args.args):
                errors.append('Incomplete Args documentation')

    return {'valid': len(errors) == 0, 'errors': errors}

# Run validation
with open('CelebiChrono/interface/shell.py') as f:
    tree = ast.parse(f.read())

results = []
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
        validation = validate_function_docstring(node)
        results.append((node.name, validation))

# Print results
print("Documentation Validation Results:")
print("=" * 50)
all_valid = True
for func_name, validation in results:
    status = "✓" if validation['valid'] else "✗"
    print(f"{status} {func_name:30}")
    if not validation['valid']:
        all_valid = False
        for error in validation['errors']:
            print(f"    - {error}")

if all_valid:
    print("\n✓ All public functions have valid Google-style docstrings!")
else:
    print("\n✗ Some functions need documentation improvements.")
```

**Step 2: Run validation**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
python scripts/validate_docs.py
```

**Step 3: Fix any remaining issues**

Based on validation output, fix any remaining documentation issues.

**Step 4: Final commit**

```bash
cd /Users/zhaomr/workdir/Chern/Celebi
git add CelebiChrono/interface/shell.py scripts/validate_docs.py
git commit -m "docs: complete shell interface documentation standardization"
```

## Plan Complete

The implementation plan is complete and saved to `docs/plans/2026-02-13-shell-doc-improvements-implementation.md`.

**Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development
- Stay in this session
- Fresh subagent per task + code review

**If Parallel Session chosen:**
- Guide them to open new session in worktree
- **REQUIRED SUB-SKILL:** New session uses superpowers:executing-plans