"""
Replace operations for shell interface.

The ``replace`` function walks a folder, renames the objects whose names
contain the search string A, and updates the input paths and aliases of the
tasks and algorithms found in the walk, substituting A with B.
"""
import os

from ...kernel.vobject import VObject
from ...utils.message import Message


def _mapped_path(renamed, path):
    """Resolve path through the rename map of its ancestors.

    Args:
        renamed: Mapping of original absolute path -> new absolute path.
        path: The absolute path to resolve.

    Returns:
        The path with the longest matching renamed ancestor substituted.
    """
    best_old = ""
    for old in renamed:
        if (path == old or path.startswith(old + os.sep)) \
                and len(old) > len(best_old):
            best_old = old
    if not best_old:
        return path
    return os.path.join(renamed[best_old], os.path.relpath(path, best_old))


def _plan_renames(root, a, b):
    """Plan the object renames in the walk, parents first.

    Args:
        root: The VObject to walk.
        a: The search string.
        b: The replacement string.

    Returns:
        List of (old_path, new_path) tuples in execution order.
    """
    renames = []
    renamed = {}
    queue = [root]
    while queue:
        obj = queue.pop(0)
        path = _mapped_path(renamed, obj.path)
        name = os.path.basename(path)
        if obj.object_type() != "project" and a and a in name:
            new_path = os.path.join(os.path.dirname(path),
                                    name.replace(a, b))
            renamed[obj.path] = new_path
            renames.append((path, new_path))
        queue += obj.sub_objects()
    return renames


def _snapshot_inputs(root):
    """Snapshot the aliased inputs of the tasks and algorithms in the walk.

    Args:
        root: The VObject to walk.

    Returns:
        List of (task_path, [(alias, path), ...]) tuples.
    """
    snapshot = []
    for obj in root.sub_objects_recursively():
        if not obj.is_task_or_algorithm():
            continue
        pairs = []
        path_to_alias = obj.config_file.read_variable("path_to_alias", {})
        for path, alias in path_to_alias.items():
            if alias:
                pairs.append((alias, path))
        snapshot.append((obj.path, pairs))
    return snapshot


def _update_inputs(obj, pairs, a, b, dry_run):
    """Substitute A with B in the input paths and aliases of obj.

    Each matching input is removed and re-added, following the
    ``remove-input`` and ``add-input`` command flow.

    Args:
        obj: The task or algorithm object.
        pairs: Snapshot list of (alias, path) inputs.
        a: The search string.
        b: The replacement string.
        dry_run: Whether to only report the planned actions.

    Returns:
        Message: Message reporting the input updates.
    """
    message = Message()
    project_path = obj.project_path()
    for alias, path in pairs:
        if a not in path and a not in alias:
            continue
        new_path = path.replace(a, b)
        new_alias = alias.replace(a, b)
        if dry_run:
            message.add(f"remove-input {alias}; "
                        f"add-input @/{new_path} {new_alias}\n", "info")
            continue
        obj.remove_input(alias)
        obj.add_input(os.path.join(project_path, new_path), new_alias)
        if obj.alias_to_path(new_alias) == new_path:
            message.add(f"Updated input {new_alias} of @/{obj.invariant_path()}\n",
                        "info")
        else:
            message.add(f"Failed to update input {new_alias} of "
                        f"@{obj.invariant_path()}\n", "error")
    return message


def _execute_renames(renames, root, dry_run, message):
    """Execute the planned renames in order, parents first.

    Args:
        renames: List of (old_path, new_path) tuples.
        root: The walked object, used for the project path.
        dry_run: Whether to only report the planned actions.
        message: The Message to report into.

    Returns:
        Mapping of original path -> new path for the successful renames.
    """
    actual = {}
    for old_path, new_path in renames:
        rel_old = os.path.relpath(old_path, root.project_path())
        rel_new = os.path.relpath(new_path, root.project_path())
        if dry_run:
            message.add(f"mv @/{rel_old} @/{rel_new}\n", "info")
            continue
        current = _mapped_path(actual, old_path)
        result = VObject(current).move_to(new_path)
        if result.messages:
            message.append(result)
        else:
            actual[old_path] = new_path
            message.add(f"Renamed @/{rel_old} -> @/{rel_new}\n", "info")
    return actual


def replace(a, b, root, dry_run=False):
    """Replace A with B in the object names, input paths, and aliases.

    Walks the folder given by ``root`` recursively. Every object whose
    name contains A is renamed (with A substituted by B in a single
    pass). The input paths and aliases of the tasks and algorithms in
    the walk are substituted the same way, using the ``remove-input``
    and ``add-input`` object operations. The project root is never
    renamed.

    Args:
        a: The search string.
        b: The replacement string.
        root: The VObject to walk.
        dry_run: Whether to only report the planned actions.

    Returns:
        Message: Message reporting the changes, or error messages.
    """
    message = Message()
    if not a:
        message.add("The search string A must not be empty.", "error")
        return message

    snapshot = _snapshot_inputs(root)
    renames = _plan_renames(root, a, b)
    actual = _execute_renames(renames, root, dry_run, message)

    for task_path, pairs in snapshot:
        obj = VObject(_mapped_path(actual, task_path))
        message.append(_update_inputs(obj, pairs, a, b, dry_run))
    return message
