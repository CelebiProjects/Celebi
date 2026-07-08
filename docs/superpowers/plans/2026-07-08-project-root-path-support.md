# Project-Root Path Support for Task-Configuration Commands

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make all task-configuration shell commands that take object paths accept `@/path` and `@` as project-root-relative paths, matching existing file-operation and navigation commands.

**Architecture:** Add a small private helper `_resolve_project_path` in `CelebiChrono/interface/shell_modules/task_configuration.py` that converts `@/...` or `@` to an absolute path under `csys.project_path()`. Apply it at the entry point of `add_input`, `add_algorithm`, and `add_parameter_subtask`. No kernel changes are needed because the kernel already expects absolute paths.

**Tech Stack:** Python 3.9+, `unittest.mock`, `pytest`, `pylint`

## Global Constraints

- Follow the existing `@/` normalization pattern already used in `file_operations.py::_normalize_paths` and `navigation.py::_cd_by_path`.
- Preserve existing behavior for plain relative and absolute paths.
- Do not add new error messages for use outside a project; let invalid paths fail naturally as they do today.
- Commands affected: `add_input`, `add_algorithm`, `add_parameter_subtask`.

---

## File Structure

| File | Role |
|------|------|
| `CelebiChrono/interface/shell_modules/task_configuration.py` | Add `_resolve_project_path` helper and apply it to the three affected commands. |
| `UnitTest/test_task_configuration_paths.py` | New test file covering helper behavior and command-level `@/` resolution for all three commands. |

---

## Task 1: Add `_resolve_project_path` helper and apply it to task-configuration commands

**Files:**
- Modify: `CelebiChrono/interface/shell_modules/task_configuration.py:9-12` (imports)
- Modify: `CelebiChrono/interface/shell_modules/task_configuration.py:14-15` (add helper after imports)
- Modify: `CelebiChrono/interface/shell_modules/task_configuration.py:104` (`add_input`)
- Modify: `CelebiChrono/interface/shell_modules/task_configuration.py:178` (`add_algorithm`)
- Modify: `CelebiChrono/interface/shell_modules/task_configuration.py:265-269` (`add_parameter_subtask`)

**Interfaces:**
- Consumes: `csys.project_path()` from `CelebiChrono.utils.csys`
- Produces: `_resolve_project_path(path: str) -> str`

- [ ] **Step 1: Add the `csys` import**

In `CelebiChrono/interface/shell_modules/task_configuration.py`, change the import block from:

```python
from ...utils import metadata
from ...utils.message import Message
```

To:

```python
from ...utils import csys
from ...utils import metadata
from ...utils.message import Message
```

- [ ] **Step 2: Add the `_resolve_project_path` helper**

Insert this function immediately after the imports and before `def jobs(_: str) -> Message:`:

```python
def _resolve_project_path(path: str) -> str:
    """Resolve a path that may be project-relative (@/... or @).

    A path starting with "@/" or equal to "@" is interpreted as relative
    to the current Celebi project root. Other paths are returned unchanged.
    """
    if path.startswith("@/") or path == "@":
        return os.path.normpath(os.path.join(csys.project_path(), path.strip("@")))
    return path
```

- [ ] **Step 3: Apply the helper in `add_input`**

In `add_input`, immediately after `message = Message()`, add:

```python
    path = _resolve_project_path(path)
```

The function start should now look like this:

```python
def add_input(path: str, alias: str) -> Message:  # pylint: disable=too-many-branches, too-many-return-statements
    """Add an input to the current task or algorithm.
    ...
    """
    message = Message()
    path = _resolve_project_path(path)
    if MANAGER.current_object().object_type() == "directory":
        ...
```

- [ ] **Step 4: Apply the helper in `add_algorithm`**

In `add_algorithm`, immediately after `message = Message()`, add:

```python
    path = _resolve_project_path(path)
```

The function start should now look like this:

```python
def add_algorithm(path: str) -> Message:
    """Add an algorithm to the current task.
    ...
    """
    message = Message()
    path = _resolve_project_path(path)
    if MANAGER.current_object().object_type() == "directory":
        ...
```

- [ ] **Step 5: Apply the helper in `add_parameter_subtask`**

In `add_parameter_subtask`, after the context check and before `MANAGER.sub_object(dirname)`, add:

```python
    dirname = _resolve_project_path(dirname)
```

The relevant section should look like this:

```python
    if MANAGER.current_object().object_type() not in ("directory", "project"):
        message.add("Unable to call add_parameter_subtask if you are not in a dir", "error")
        return message
    dirname = _resolve_project_path(dirname)
    obj = MANAGER.sub_object(dirname)
    if not obj.is_task():
        ...
```

- [ ] **Step 6: Verify the module imports cleanly**

Run:

```bash
python -c "from CelebiChrono.interface.shell_modules.task_configuration import add_input, add_algorithm, add_parameter_subtask, _resolve_project_path; print('imports ok')"
```

Expected output:

```
imports ok
```

- [ ] **Step 7: Commit**

```bash
git add CelebiChrono/interface/shell_modules/task_configuration.py
git commit -m "feat: resolve @/ paths in task-configuration commands

Add _resolve_project_path helper and apply it to add_input,
add_algorithm, and add_parameter_subtask so they accept
project-root-relative paths (@/path and @).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Add unit tests for `@/` path resolution

**Files:**
- Create: `UnitTest/test_task_configuration_paths.py`

**Interfaces:**
- Consumes: `task_configuration._resolve_project_path`, `task_configuration.add_input`, `task_configuration.add_algorithm`, `task_configuration.add_parameter_subtask`, `MANAGER`
- Produces: Passing unit tests for `@/` resolution

- [ ] **Step 1: Create the test file**

Create `UnitTest/test_task_configuration_paths.py` with this content:

```python
"""Tests for project-root path resolution in task configuration commands."""

import unittest
from unittest.mock import patch, MagicMock

from CelebiChrono.interface.shell_modules import task_configuration
from CelebiChrono.interface.shell_modules._manager import MANAGER


class TestResolveProjectPath(unittest.TestCase):
    """Tests for the _resolve_project_path helper."""

    @patch.object(task_configuration, "csys")
    def test_at_slash_resolves_to_project_root(self, mock_csys):
        mock_csys.project_path.return_value = "/project"
        result = task_configuration._resolve_project_path("@/tasks/foo")
        self.assertEqual(result, "/project/tasks/foo")

    @patch.object(task_configuration, "csys")
    def test_at_alone_resolves_to_project_root(self, mock_csys):
        mock_csys.project_path.return_value = "/project"
        result = task_configuration._resolve_project_path("@")
        self.assertEqual(result, "/project")

    @patch.object(task_configuration, "csys")
    def test_plain_relative_path_unchanged(self, mock_csys):
        result = task_configuration._resolve_project_path("tasks/foo")
        self.assertEqual(result, "tasks/foo")
        mock_csys.project_path.assert_not_called()

    @patch.object(task_configuration, "csys")
    def test_absolute_path_unchanged(self, mock_csys):
        result = task_configuration._resolve_project_path("/abs/path")
        self.assertEqual(result, "/abs/path")
        mock_csys.project_path.assert_not_called()


class TestAddInputPathResolution(unittest.TestCase):
    """Tests that add_input resolves @/ paths."""

    @patch.object(task_configuration, "csys")
    @patch.object(MANAGER, "current_object")
    def test_add_input_resolves_at_slash_path(self, mock_current_object, mock_csys):
        mock_csys.project_path.return_value = "/project"
        mock_task = MagicMock()
        mock_task.object_type.return_value = "task"
        mock_current_object.return_value = mock_task

        task_configuration.add_input("@/tasks/prev/output", "result")

        mock_task.add_input.assert_called_once_with(
            "/project/tasks/prev/output", "result"
        )

    @patch.object(task_configuration, "csys")
    @patch.object(MANAGER, "current_object")
    def test_add_input_keeps_plain_path(self, mock_current_object, mock_csys):
        mock_task = MagicMock()
        mock_task.object_type.return_value = "task"
        mock_current_object.return_value = mock_task

        task_configuration.add_input("tasks/prev/output", "result")

        mock_task.add_input.assert_called_once_with("tasks/prev/output", "result")
        mock_csys.project_path.assert_not_called()


class TestAddAlgorithmPathResolution(unittest.TestCase):
    """Tests that add_algorithm resolves @/ paths."""

    @patch.object(task_configuration, "csys")
    @patch.object(MANAGER, "current_object")
    def test_add_algorithm_resolves_at_slash_path(self, mock_current_object, mock_csys):
        mock_csys.project_path.return_value = "/project"
        mock_task = MagicMock()
        mock_task.object_type.return_value = "task"
        mock_current_object.return_value = mock_task

        task_configuration.add_algorithm("@/algorithms/proc")

        mock_task.add_algorithm.assert_called_once_with("/project/algorithms/proc")

    @patch.object(task_configuration, "csys")
    @patch.object(MANAGER, "current_object")
    def test_add_algorithm_keeps_plain_path(self, mock_current_object, mock_csys):
        mock_task = MagicMock()
        mock_task.object_type.return_value = "task"
        mock_current_object.return_value = mock_task

        task_configuration.add_algorithm("algorithms/proc")

        mock_task.add_algorithm.assert_called_once_with("algorithms/proc")
        mock_csys.project_path.assert_not_called()


class TestAddParameterSubtaskPathResolution(unittest.TestCase):
    """Tests that add_parameter_subtask resolves @/ paths."""

    @patch.object(task_configuration, "csys")
    @patch.object(MANAGER, "current_object")
    @patch.object(MANAGER, "sub_object")
    def test_add_parameter_subtask_resolves_at_slash_path(
        self, mock_sub_object, mock_current_object, mock_csys
    ):
        mock_csys.project_path.return_value = "/project"
        mock_dir = MagicMock()
        mock_dir.object_type.return_value = "directory"
        mock_current_object.return_value = mock_dir
        mock_task = MagicMock()
        mock_task.is_task.return_value = True
        mock_sub_object.return_value = mock_task

        task_configuration.add_parameter_subtask("@/tasks/model", "lr", "0.01")

        mock_sub_object.assert_called_once_with("/project/tasks/model")
        mock_task.add_parameter.assert_called_once_with("lr", "0.01")

    @patch.object(task_configuration, "csys")
    @patch.object(MANAGER, "current_object")
    @patch.object(MANAGER, "sub_object")
    def test_add_parameter_subtask_keeps_plain_path(
        self, mock_sub_object, mock_current_object, mock_csys
    ):
        mock_dir = MagicMock()
        mock_dir.object_type.return_value = "directory"
        mock_current_object.return_value = mock_dir
        mock_task = MagicMock()
        mock_task.is_task.return_value = True
        mock_sub_object.return_value = mock_task

        task_configuration.add_parameter_subtask("tasks/model", "lr", "0.01")

        mock_sub_object.assert_called_once_with("tasks/model")
        mock_task.add_parameter.assert_called_once_with("lr", "0.01")
        mock_csys.project_path.assert_not_called()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new tests**

```bash
cd UnitTest
python -m pytest test_task_configuration_paths.py -v
```

Expected: All 10 tests pass.

- [ ] **Step 3: Commit**

```bash
git add UnitTest/test_task_configuration_paths.py
git commit -m "test: add @/ path resolution tests for task-configuration commands

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Regression verification

**Files:**
- No file changes expected.

- [ ] **Step 1: Run the full unit-test suite**

```bash
cd UnitTest
python -m pytest -v
```

Expected: All existing tests continue to pass; the 10 new tests pass.

- [ ] **Step 2: Run pylint on the modified module**

```bash
python -m pylint --rcfile=.pylintrc CelebiChrono/interface/shell_modules/task_configuration.py
```

Expected: No new pylint errors introduced by the change.

- [ ] **Step 3: If any fixes are needed, commit them**

```bash
git add <fixed-files>
git commit -m "fix: address lint/regression issues from @/ path support

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

### Spec coverage

- `@/path` resolution for `add_input`: Task 1, Step 3; Task 2, `TestAddInputPathResolution`.
- `@/path` resolution for `add_algorithm`: Task 1, Step 4; Task 2, `TestAddAlgorithmPathResolution`.
- `@/path` resolution for `add_parameter_subtask`: Task 1, Step 5; Task 2, `TestAddParameterSubtaskPathResolution`.
- `@` alone resolves to project root: Task 2, `TestResolveProjectPath.test_at_alone_resolves_to_project_root`.
- Plain paths unchanged: Task 2, helper and command tests for plain paths.
- Follow existing behavior/error handling: Global Constraints; Task 1 helper uses the same pattern as existing code.
- No kernel changes: File Structure table notes only shell module and tests change.

### Placeholder scan

No TBD, TODO, or vague instructions. All code blocks contain complete, runnable content.

### Type consistency

- `_resolve_project_path(path: str) -> str` is used consistently.
- `add_input`, `add_algorithm`, and `add_parameter_subtask` keep their original signatures; only the local path/dirname variable is normalized.
