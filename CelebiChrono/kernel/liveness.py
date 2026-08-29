"""Compute the project's live impression set: the current version of
every task and algorithm plus its transitive input dependencies."""
import os

from CelebiChrono.utils import metadata
from CelebiChrono.utils.path_utils import project_path as _project_path

IMPRESSIONS_DIR = ".celebi/impressions"


def _object_variables(obj_dir):
    """Merged variable reader across an object's two-tier config files.

    Reads <obj>/.celebi/config.json (shared) first, then the local
    override <obj>/.celebi/config.local.json (which records the
    impression pointer and history); the local file wins. Mirrors
    metadata.TwoTierConfigFile.
    """
    two_tier = metadata.TwoTierConfigFile(
        os.path.join(obj_dir, ".celebi", "config.json"))

    def read(key, default):
        return two_tier.read_variable(key, default)
    return read


def _objects(project_dir):
    """Yield object_type + variable reader for each task/algorithm dir."""
    if not os.path.isdir(project_dir):
        return
    for name in os.listdir(project_dir):
        obj_dir = os.path.join(project_dir, name)
        if not os.path.isdir(obj_dir) or name.startswith("."):
            continue
        config_path = os.path.join(obj_dir, ".celebi", "config.json")
        if not os.path.isfile(config_path):
            continue
        object_type = metadata.TwoTierConfigFile(config_path).read_variable(
            "object_type", "")
        if object_type not in ("task", "algorithm"):
            continue
        yield object_type, _object_variables(obj_dir)


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
    """
    project_dir = project_dir or _project_path()
    live, superseded, current = set(), set(), set()
    for _object_type, read in _objects(project_dir):
        pointer = read("impression", "")
        if pointer:
            current.add(pointer)
            _collect_inputs(project_dir, pointer, live)
        for record in read("impressions", []) or []:
            uuid = record.get("uuid", "") if isinstance(record, dict) else ""
            if uuid:
                superseded.add(uuid)
    live |= current
    superseded -= live
    return sorted(live), sorted(superseded)
