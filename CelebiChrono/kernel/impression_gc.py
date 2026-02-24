"""Garbage collection for CAS-backed impression storage."""
import os
import time
from typing import Dict, Set

from .impression_store import ImpressionStore


class ImpressionGC:
    """Mark-and-sweep style cleanup for loose CAS objects."""

    def __init__(self, project_path: str = "") -> None:
        self.store = ImpressionStore(project_path or None)

    def _collect_live_hashes(self) -> Set[str]:
        live_hashes: Set[str] = set()
        stack = list(self.store.iter_referenced_hashes())
        while stack:
            tree_hash = stack.pop()
            if not tree_hash or tree_hash in live_hashes:
                continue
            live_hashes.add(tree_hash)
            try:
                entries = self.store.get_tree(tree_hash)
            except FileNotFoundError:
                continue
            for entry in entries:
                entry_hash = entry.get("hash")
                if entry_hash:
                    live_hashes.add(entry_hash)
        return live_hashes

    def run(self, grace_days: int = 14, dry_run: bool = True) -> Dict[str, int]:
        """GC unreachable loose objects after grace period."""
        live_hashes = self._collect_live_hashes()
        now = int(time.time())
        grace_seconds = grace_days * 24 * 3600

        unreachable_meta = self.store.read_store_meta("unreachable", {})
        if not isinstance(unreachable_meta, dict):
            unreachable_meta = {}

        deleted_count = 0
        deleted_bytes = 0
        unreachable_count = 0

        def sweep_dir(directory: str, suffix: str = "") -> None:
            nonlocal deleted_count, deleted_bytes, unreachable_count
            if not os.path.exists(directory):
                return
            for name in os.listdir(directory):
                full_path = os.path.join(directory, name)
                if not os.path.isfile(full_path):
                    continue
                obj_hash = name[:-len(suffix)] if suffix and name.endswith(suffix) else name
                if obj_hash in live_hashes:
                    unreachable_meta.pop(obj_hash, None)
                    continue

                unreachable_count += 1
                first_seen = int(unreachable_meta.get(obj_hash, now))
                unreachable_meta[obj_hash] = first_seen
                age = now - first_seen
                if age < grace_seconds:
                    continue
                if dry_run:
                    continue

                size = os.path.getsize(full_path)
                os.remove(full_path)
                deleted_count += 1
                deleted_bytes += size
                unreachable_meta.pop(obj_hash, None)

        sweep_dir(self.store.blob_root)
        sweep_dir(self.store.tree_root, suffix=".json")

        self.store.write_store_meta("unreachable", unreachable_meta)
        return {
            "live_hashes": len(live_hashes),
            "unreachable_objects": unreachable_count,
            "deleted_objects": deleted_count,
            "deleted_bytes": deleted_bytes,
            "dry_run": int(dry_run),
            "grace_days": grace_days,
        }
