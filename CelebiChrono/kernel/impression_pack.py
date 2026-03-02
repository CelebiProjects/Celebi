"""Packing helpers for CAS impressions.

Current implementation provides threshold checks and stats; packfile writing
is intentionally deferred while preserving command/API surface.
"""
from typing import Dict

from .impression_store import ImpressionStore


class ImpressionPack:
    """Pack planner for loose CAS objects."""

    def __init__(self, project_path: str = "") -> None:
        self.store = ImpressionStore(project_path or None)

    def maybe_pack(
        self,
        max_loose_objects: int = 5000,
        max_loose_size_mb: int = 256,
        force: bool = False,
    ) -> Dict[str, int]:
        stats = self.store.loose_object_stats()
        size_mb = stats["total_size_bytes"] / (1024 * 1024)
        should_pack = force or (
            stats["total_count"] >= max_loose_objects or size_mb >= max_loose_size_mb
        )

        return {
            "should_pack": int(should_pack),
            "packed_objects": 0,
            "total_loose_objects": stats["total_count"],
            "total_loose_size_bytes": stats["total_size_bytes"],
        }
