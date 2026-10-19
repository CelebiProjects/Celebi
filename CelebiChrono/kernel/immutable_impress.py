"""Single-pass DAG evaluation for explicitly immutable project inputs.

Unlike interactive impress this never asks is_impressed(), scans project mtimes,
or recursively expands a predecessor. UUID and payload formats remain unchanged.
"""
import fcntl
import json
import os
import re
import tempfile
from collections import deque
from pathlib import Path
from types import SimpleNamespace

from .vimpression import VImpression
from .impression_store import ImpressionStore
from ..utils import metadata
from ..utils.path_utils import native_path_access


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".immutable-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _read(path):
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected metadata mapping: {path}")
    return data


def _discover(root):
    nodes = {}
    for directory, names, _ in os.walk(root, followlinks=False):
        path = Path(directory)
        config = path / ".celebi/config.json"
        if config.is_file():
            data = _read(config)
            data.update(_read(config.with_name("config.local.json")))
            if data.get("object_type") in ("task", "algorithm"):
                nodes[path.relative_to(root).as_posix()] = data
        names[:] = [name for name in names if not name.startswith((".", "__"))
                    and name not in ("impressions", "impressions_store", "stageout")
                    and not (path / name).is_symlink()]
    return nodes


def _order(nodes):
    counts, successors = {}, {name: [] for name in nodes}
    for name, data in nodes.items():
        # Aliases must also be available, but do not add them to the UUID's
        # dependency list unless they occur in predecessors (legacy semantics).
        predecessors, aliases = data.get("predecessors", []), data.get("alias_to_path", {})
        if (not isinstance(predecessors, list) or not isinstance(aliases, dict)
                or not all(isinstance(ref, str) for ref in predecessors)
                or not all(isinstance(ref, str) for ref in aliases.values())):
            raise ValueError(f"Invalid dependencies for {name!r}")
        refs = set(predecessors) | set(aliases.values())
        for ref in refs:
            if ref not in nodes:
                raise ValueError(f"Missing executable predecessor {ref!r} for {name!r}")
            successors[ref].append(name)
        counts[name] = len(refs)
    ready = deque(name for name, count in counts.items() if not count)
    ordered = []
    while ready:
        name = ready.popleft()
        ordered.append(name)
        for successor in successors[name]:
            counts[successor] -= 1
            if not counts[successor]:
                ready.append(successor)
    if len(ordered) != len(nodes):
        raise ValueError("Impression dependency graph contains a cycle")
    return ordered


def _attach_cache(root, cache, project_uuid):
    # A cache belongs to exactly one analysis. Inputs must be a disposable
    # checkout or already use these links; never delete/replace local results.
    cache.mkdir(parents=True, exist_ok=True)
    identity = cache / "project.json"
    if identity.exists() and _read(identity).get("project_uuid") != project_uuid:
        raise ValueError("Impression cache belongs to a different project")
    if not identity.exists():
        identity.write_text(json.dumps({"project_uuid": project_uuid}), encoding="utf-8")
    destinations = []
    for name in ("impressions", "impressions_store"):
        link = root / ".celebi" / name
        target = cache / ".celebi" / name
        if link.is_symlink():
            if link.resolve() != target.resolve():
                raise ValueError(f"Existing {name} points to a different cache")
        elif link.exists() and target.exists() and any(link.iterdir()):
            raise ValueError(f"Existing local {name}; reuse without --cache-dir first")
        destinations.append((link, target))
    for link, target in destinations:
        if link.exists() and not link.is_symlink() and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            link.rename(target)
        target.mkdir(parents=True, exist_ok=True)
        if not link.is_symlink():
            if link.exists():
                link.rmdir()  # Only an empty directory, checked above.
            link.symlink_to(target, target_is_directory=True)


def _complete_ref(store, ref, checked_blobs):
    """Do not silently reuse a partial payload left by an interrupted run."""
    try:
        tree_hash = ref.get("root_tree", "") if isinstance(ref, dict) else ""
        if not re.fullmatch(r"[0-9a-f]{64}", tree_hash):
            return False
        tree = store.get_tree(tree_hash)
        for entry in tree:
            blob_hash = entry["hash"]
            if not re.fullmatch(r"[0-9a-f]{64}", blob_hash):
                return False
            if blob_hash not in checked_blobs:
                checked_blobs[blob_hash] = Path(store._blob_path(blob_hash)).is_file()
            if not checked_blobs[blob_hash]:
                return False
        return True
    except (OSError, ValueError, TypeError, KeyError):
        return False


class _Payload:
    """Already evaluated predecessor/alias references for the existing writer."""
    def __init__(self, root, name, data, resolved):
        self.path = str(root / name)
        self.name, self.data, self.resolved = name, data, resolved
        self.config_file = SimpleNamespace(read_variable=data.get)

    def pred_impressions(self):
        return [SimpleNamespace(uuid=uid) for uid in sorted(
            self.resolved[ref] for ref in self.data.get("predecessors", []))]

    def object_type(self):
        return self.data["object_type"]

    def invariant_path(self):
        return self.name

    def is_task_or_algorithm(self):
        return True

    def alias_to_impression(self, alias):
        return SimpleNamespace(uuid=self.resolved[self.data["alias_to_path"][alias]])

    def impression(self):
        # Never trust committed or stale local pointers as execution history.
        return None


def impress_immutable(project_root, cache_dir=None, progress=None):
    """Evaluate each executable node once. Caller guarantees unchanged inputs.

    Graph work is O(V+E), excluding canonical sorting. File hashing/storage is
    linear in input bytes; existing refs/payloads are never rewritten. The
    optional cache is project-scoped and survives disposable Git checkouts.
    """
    root = Path(project_root).resolve()
    if Path.cwd().resolve() != root:
        raise ValueError("Run immutable impress from the project root")
    project_uuid = _read(root / ".celebi/config.json").get("project_uuid")
    if not project_uuid or not (root / ".celebi/project.json").is_file():
        raise ValueError("Expected a Celebi project root")
    cache = Path(cache_dir).resolve() if cache_dir else root / ".celebi"
    if cache_dir and cache.is_relative_to(root):
        raise ValueError("--cache-dir must be outside the project input tree")
    cache.mkdir(parents=True, exist_ok=True)
    with native_path_access(), (cache / "immutable-impress.lock").open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        nodes = _discover(root)
        ordered = _order(nodes)  # Fail before writing any impression on a cycle.
        if cache_dir:
            _attach_cache(root, cache, project_uuid)
        store = ImpressionStore(str(root))
        hasher = VImpression()
        resolved, created, reused = {}, 0, 0
        checked_blobs, complete_refs = {}, {}
        for index, name in enumerate(ordered, 1):
            data = nodes[name]
            deps = [resolved[ref] for ref in data.get("predecessors", [])]
            uid = hasher.generate_imp_uuid(project_uuid, str(root / name), deps)
            impression = VImpression(uid)
            try:
                ref = store.read_impression_ref(uid)
            except (OSError, ValueError):
                ref = None
            if uid not in complete_refs:
                complete_refs[uid] = _complete_ref(store, ref, checked_blobs)
            if complete_refs[uid]:
                reused += 1
                # Older runs may have CAS refs without the compatibility config.
                if not Path(impression.config_file.file_path).is_file():
                    _write(Path(impression.config_file.file_path), ref)
            else:
                impression.create(_Payload(root, name, data, resolved))
                created += 1
                complete_refs[uid] = True
                fresh = store.read_impression_ref(uid)
                for entry in store.get_tree(fresh["root_tree"]):
                    checked_blobs[entry["hash"]] = True
            resolved[name] = uid
            metadata.TwoTierConfigFile(str(root / name / ".celebi/config.json")).write_variable(
                "impression", uid)
            if index == 1 or index % 25 == 0 or index == len(ordered):
                stats = {"processed": index, "total": len(ordered),
                         "created": created, "reused": reused}
                _write(root / ".celebi/immutable-impress-progress.json", stats)
                if progress:
                    progress(stats)
        result = {"objects": resolved, "processed": len(resolved), "total": len(nodes),
                  "created": created, "reused": reused}
        _write(root / ".celebi/immutable-impress.json", result)
        return result
