# Project-Root Path Support for Task-Configuration Commands

## Summary

Extend Celebi task-configuration shell functions so they accept `@/path` and `@` as project-root-relative paths, matching the behavior already present in file-operation and navigation commands.

## Motivation

Users currently expect `@/tasks/prev/output` style paths to work everywhere, because docstrings for `add-input`, `add-algorithm`, and `add-parameter-subtask` already show these examples. In practice, only file-operation and navigation commands resolve `@/`; task-configuration commands pass the literal string through, causing path-not-found failures.

## Scope

### In scope

Add `@/` and `@` resolution to all task-configuration shell functions that take object paths:

- `add_input(path, alias)`
- `add_algorithm(path)`
- `add_parameter_subtask(dirname, par, value)`

### Out of scope

- Commands that do not take object paths (`add_parameter`, `set_environment`, `set_memory_limit`, etc.).
- Refactoring the existing `@/` normalization in `file_operations.py` or `navigation.py`; this design follows the same inline pattern.
- New error messages for use outside a project; existing behavior is preserved.

## Design

### New helper

Add the following helper to `CelebiChrono/interface/shell_modules/task_configuration.py`:

```python
def _resolve_project_path(path: str) -> str:
    """Resolve a path that may be project-relative (@/... or @)."""
    if path.startswith("@/") or path == "@":
        return os.path.normpath(os.path.join(csys.project_path(), path.strip("@")))
    return path
```

### Function updates

1. `add_input(path, alias)` — normalize `path` immediately on entry, before directory-object bulk logic.
2. `add_algorithm(path)` — normalize `path` immediately on entry.
3. `add_parameter_subtask(dirname, par, value)` — normalize `dirname` before `MANAGER.sub_object(dirname)`.

No kernel changes are required. The resolved absolute paths are exactly what `vtask_input.py` and `vobj_arc_input.py` already expect.

### Data flow example

Command: `add-input @/tasks/previous/output result`

1. Shell function `add_input("@/tasks/previous/output", "result")` is invoked.
2. `_resolve_project_path` converts the first argument to `/project/tasks/previous/output`.
3. The current task’s `add_input("/project/tasks/previous/output", "result")` links the object with alias `result`.

## Error handling

Follow existing behavior. If `csys.project_path()` returns an empty string (outside a project), the normalized path becomes invalid and fails later with the same error as a non-`@/` invalid path. No new error messages are introduced.

## Testing

Add unit tests that:

- Mock `csys.project_path` to a fixed project root.
- Verify `add_input("@/tasks/foo", "alias")` resolves to the absolute project path.
- Verify `add_algorithm("@/algorithms/foo")` resolves correctly.
- Verify `add_parameter_subtask("@/tasks/model", ...)` resolves correctly.
- Verify plain relative and absolute paths continue to work unchanged.

Run the existing test suite to ensure no regressions.

## References

- Existing `@/` normalization pattern: `CelebiChrono/interface/shell_modules/file_operations.py::_normalize_paths`
- Existing `@/` navigation support: `CelebiChrono/interface/shell_modules/navigation.py::_cd_by_path`
- Project-root discovery: `CelebiChrono/utils/path_utils.py::project_path`
