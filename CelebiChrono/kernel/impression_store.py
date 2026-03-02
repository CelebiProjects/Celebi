"""Content-addressed storage for impression payloads."""
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional

import fcntl

from ..utils import csys


class ImpressionStore:
    """A local content-addressed store for impressions."""

    def __init__(self, project_path: Optional[str] = None) -> None:
        self.project_path = project_path or csys.project_path()
        self.store_root = os.path.join(self.project_path, ".celebi", "impressions_store")
        self.blob_root = os.path.join(self.store_root, "objects", "blobs")
        self.tree_root = os.path.join(self.store_root, "objects", "trees")
        self.ref_root = os.path.join(self.store_root, "refs", "impressions")
        self.meta_root = os.path.join(self.store_root, "meta")
        self.lock_path = os.path.join(self.store_root, "store.lock")
        for directory in (
            self.blob_root,
            self.tree_root,
            self.ref_root,
            self.meta_root,
        ):
            csys.mkdir(directory)

    @staticmethod
    def _sha256_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _blob_path(self, blob_hash: str) -> str:
        return os.path.join(self.blob_root, blob_hash)

    def _tree_path(self, tree_hash: str) -> str:
        return os.path.join(self.tree_root, f"{tree_hash}.json")

    def _ref_path(self, impression_uuid: str) -> str:
        return os.path.join(self.ref_root, f"{impression_uuid}.json")

    @contextmanager
    def _write_lock(self):
        csys.mkdir(self.store_root)
        with open(self.lock_path, "a", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)

    @staticmethod
    def _atomic_write_bytes(path: str, data: bytes) -> None:
        directory = os.path.dirname(path)
        csys.mkdir(directory)
        fd, temp_path = tempfile.mkstemp(prefix=".tmp_", dir=directory)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @classmethod
    def _canonical_json_bytes(cls, payload: Any) -> bytes:
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def put_blob(self, content: bytes) -> str:
        blob_hash = self._sha256_bytes(content)
        blob_path = self._blob_path(blob_hash)
        if os.path.exists(blob_path):
            return blob_hash
        with self._write_lock():
            if not os.path.exists(blob_path):
                self._atomic_write_bytes(blob_path, content)
        return blob_hash

    def get_blob(self, blob_hash: str) -> bytes:
        with open(self._blob_path(blob_hash), "rb") as f:
            return f.read()

    def put_tree(self, entries: List[Dict[str, Any]]) -> str:
        tree_hash = self._sha256_bytes(self._canonical_json_bytes(entries))
        tree_path = self._tree_path(tree_hash)
        if os.path.exists(tree_path):
            return tree_hash
        with self._write_lock():
            if not os.path.exists(tree_path):
                self._atomic_write_bytes(tree_path, self._canonical_json_bytes(entries))
        return tree_hash

    def get_tree(self, tree_hash: str) -> List[Dict[str, Any]]:
        with open(self._tree_path(tree_hash), "r", encoding="utf-8") as f:
            return json.load(f)

    def has_impression_ref(self, impression_uuid: str) -> bool:
        return os.path.exists(self._ref_path(impression_uuid))

    def write_impression_ref(self, impression_uuid: str, data: Dict[str, Any]) -> None:
        payload = dict(data)
        payload["uuid"] = impression_uuid
        ref_path = self._ref_path(impression_uuid)
        with self._write_lock():
            self._atomic_write_bytes(ref_path, self._canonical_json_bytes(payload))

    def read_impression_ref(self, impression_uuid: str) -> Optional[Dict[str, Any]]:
        ref_path = self._ref_path(impression_uuid)
        if not os.path.exists(ref_path):
            return None
        with open(ref_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def iter_referenced_hashes(self) -> Iterable[str]:
        if not os.path.exists(self.ref_root):
            return
        for filename in os.listdir(self.ref_root):
            if not filename.endswith(".json"):
                continue
            with open(os.path.join(self.ref_root, filename), "r", encoding="utf-8") as f:
                ref = json.load(f)
            root_tree = ref.get("root_tree")
            if root_tree:
                yield root_tree

    def read_store_meta(self, key: str, default: Any = None) -> Any:
        path = os.path.join(self.meta_root, f"{key}.json")
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def write_store_meta(self, key: str, data: Any) -> None:
        path = os.path.join(self.meta_root, f"{key}.json")
        with self._write_lock():
            self._atomic_write_bytes(path, self._canonical_json_bytes(data))

    def loose_object_stats(self) -> Dict[str, int]:
        blob_count = 0
        blob_size = 0
        tree_count = 0
        tree_size = 0

        for directory, kind in ((self.blob_root, "blob"), (self.tree_root, "tree")):
            if not os.path.exists(directory):
                continue
            for name in os.listdir(directory):
                full_path = os.path.join(directory, name)
                if not os.path.isfile(full_path):
                    continue
                size = os.path.getsize(full_path)
                if kind == "blob":
                    blob_count += 1
                    blob_size += size
                else:
                    tree_count += 1
                    tree_size += size

        return {
            "blob_count": blob_count,
            "blob_size_bytes": blob_size,
            "tree_count": tree_count,
            "tree_size_bytes": tree_size,
            "total_count": blob_count + tree_count,
            "total_size_bytes": blob_size + tree_size,
        }
