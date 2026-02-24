"""Materialize CAS-backed impressions into a filesystem tree."""
import os
from typing import Optional

from ..utils import csys
from .impression_store import ImpressionStore


class ImpressionMaterializer:
    """Reconstructs a snapshot tree from impression CAS metadata."""

    def __init__(self, project_path: Optional[str] = None) -> None:
        self.store = ImpressionStore(project_path)

    def materialize_impression(self, impression_uuid: str, target_dir: str) -> str:
        """Materialize an impression's content into target_dir and return target_dir."""
        ref = self.store.read_impression_ref(impression_uuid)
        if not ref:
            raise FileNotFoundError(f"Impression ref not found: {impression_uuid}")

        root_tree = ref.get("root_tree")
        if not root_tree:
            raise ValueError(f"Impression {impression_uuid} has no root_tree")

        csys.mkdir(target_dir)
        tree_entries = self.store.get_tree(root_tree)
        for entry in tree_entries:
            if entry.get("type") != "blob":
                continue
            rel_path = entry["path"]
            blob_hash = entry["hash"]
            content = self.store.get_blob(blob_hash)
            out_path = os.path.join(target_dir, rel_path)
            parent = os.path.dirname(out_path)
            if parent:
                csys.mkdir(parent)
            with open(out_path, "wb") as f:
                f.write(content)
        return target_dir
