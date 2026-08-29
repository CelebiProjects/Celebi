"""Compute the project's live impression set: the current version of
every task and algorithm plus its transitive input dependencies."""
import os

from CelebiChrono.utils import metadata
from CelebiChrono.utils.path_utils import project_path as _project_path

IMPRESSIONS_DIR = ".celebi/impressions"


def _object_variables(obj_dir):
    """Merged variable reader across an object's config files.

    Reads <obj>/config.json first, then <obj>/.celebi/config.local.json
    (which records the impression history); the local file wins.
    """
    def read(key, default):
        value = default
        for path in (os.path.join(obj_dir, "config.json"),
                     os.path.join(obj_dir, ".celebi", "config.local.json")):
            if os.path.isfile(path):
                value = metadata.ConfigFile(path).read_variable(key, value)
        return value
    return read


def _objects(project_dir):
    """Yield object_type + variable reader for each task/algorithm dir."""
    if not os.path.isdir(project_dir):
        return
    for name in os.listdir(project_dir):
        obj_dir = os.path.join(project_dir, name)
        if not os.path.isdir(obj_dir) or name.startswith("."):
            continue
        config_path = os.path.join(obj_dir, "config.json")
        if not os.path.isfile(config_path):
            continue
        object_type = metadata.ConfigFile(config_path).read_variable(
            "object_type", "")
        if object_type not in ("task", "algorithm"):
            continue
        yield object_type, _object_variables(obj_dir)


def _impression_config(project_dir, uuid):
    """ConfigFile of an impression in the project's impression store."""
    return metadata.ConfigFile(os.path.join(
        project_dir, IMPRESSIONS_DIR, uuid, "config.json"))


def _collect_inputs(project_dir, root_uuid, seen):
    """Transitively add the impression's dependency uuids to seen."""
    if not root_uuid or root_uuid in seen:
        return
    seen.add(root_uuid)
    config = _impression_config(project_dir, root_uuid)
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
