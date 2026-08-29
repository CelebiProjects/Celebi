"""Compute the project's live impression set: the current version of
every task and algorithm plus its transitive input dependencies."""
import os

from CelebiChrono.utils import metadata
from CelebiChrono.utils.path_utils import project_path as _project_path

IMPRESSIONS_DIR = ".celebi/impressions"


def _collect_inputs(project_dir, root_uuid, seen):
    """Transitively add the impression's dependency uuids to seen.

    A dependency uuid without an impression config is dangling and is
    silently skipped.
    """
    if not root_uuid or root_uuid in seen:
        return
    config_path = os.path.join(project_dir, IMPRESSIONS_DIR, root_uuid,
                               "config.json")
    if not os.path.isfile(config_path):
        return
    seen.add(root_uuid)
    config = metadata.ConfigFile(config_path)
    for dep in config.read_variable("dependencies", []) or []:
        if isinstance(dep, str):
            _collect_inputs(project_dir, dep, seen)
    aliases = config.read_variable("alias_to_impression", {}) or {}
    for dep in aliases.values():
        if isinstance(dep, str):
            _collect_inputs(project_dir, dep, seen)


def compute_live_sets(project_dir=None):
    """Return (live, superseded) uuid lists for the project.

    live: the current impression pointer of every task/algorithm plus
    its transitive input dependencies.
    superseded: every impression in an object's impression history that
    is not a current pointer (of any object).

    Objects are enumerated through VProject.sub_objects_recursively —
    Celebi's own traversal, which walks nested directory objects and
    skips zombies — and each object's pointer/history is read through
    its two-tier config_file.
    """
    from CelebiChrono.kernel.vproject import VProject

    project_dir = project_dir or _project_path()
    live, superseded, current = set(), set(), set()
    project = VProject(project_dir, project_dir)
    for obj in project.sub_objects_recursively():
        if obj.object_type() not in ("task", "algorithm"):
            continue
        pointer = obj.config_file.read_variable("impression", "")
        if pointer:
            current.add(pointer)
            _collect_inputs(project_dir, pointer, live)
        for record in obj.config_file.read_variable(
                "impressions", []) or []:
            uuid = record.get("uuid", "") if isinstance(record, dict) else ""
            if uuid:
                superseded.add(uuid)
    live |= current
    superseded -= live
    return sorted(live), sorted(superseded)
