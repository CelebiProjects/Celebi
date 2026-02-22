"""YAML/JSON config file merge with semantic conflict resolution for Celebi.

This module provides specialized merging for Celebi's configuration files
with semantic understanding of UUIDs, dependencies, and other Celebi-specific
structures.
"""
import yaml
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from logging import getLogger

logger = getLogger("ChernLogger")


class ConfigConflictType(Enum):
    """Types of configuration merge conflicts."""
    UUID_CONFLICT = "uuid_conflict"  # Same UUID with different content
    DEPENDENCY_CONFLICT = "dependency_conflict"  # Different dependency lists
    ALIAS_CONFLICT = "alias_conflict"  # Same alias pointing to different objects
    VALUE_CONFLICT = "value_conflict"  # Different values for same key
    STRUCTURE_CONFLICT = "structure_conflict"  # Different data structures
    CONFLICT_MARKER = "conflict_marker"  # Git left conflict markers in file


class ConfigMerger:
    """Merges Celebi configuration files with semantic conflict resolution."""

    def __init__(self, prefer_local: bool = True):
        self.prefer_local = prefer_local
        self.conflicts: List[Dict] = []

    def merge_yaml_files(self, local_content: str, remote_content: str,
                         base_content: str) -> Tuple[str, List[Dict]]:
        """
        Merge YAML configuration files with semantic understanding.

        Args:
            local_content: YAML content from local branch
            remote_content: YAML content from remote branch
            base_content: YAML content from common ancestor

        Returns:
            Tuple of (merged_content, conflicts)
        """
        try:
            local_data = yaml.safe_load(local_content) or {}
            remote_data = yaml.safe_load(remote_content) or {}
            base_data = yaml.safe_load(base_content) or {}
        except yaml.YAMLError as e:
            logger.error("Failed to parse YAML: %s", e)
            # Fall back to textual merge
            return self._textual_merge(local_content, remote_content, base_content)

        # Check for git conflict markers first
        if self._has_conflict_markers(local_content) or self._has_conflict_markers(remote_content):
            return self._resolve_conflict_markers(local_content, remote_content)

        # Perform semantic merge
        merged_data = self._merge_dicts(local_data, remote_data, base_data, path="")

        # Convert back to YAML
        merged_content = yaml.dump(merged_data, default_flow_style=False, sort_keys=False)

        return merged_content, self.conflicts

    def merge_json_files(self, local_content: str, remote_content: str,
                         base_content: str) -> Tuple[str, List[Dict]]:
        """
        Merge JSON configuration files with semantic understanding.

        Args:
            local_content: JSON content from local branch
            remote_content: JSON content from remote branch
            base_content: JSON content from common ancestor

        Returns:
            Tuple of (merged_content, conflicts)
        """
        try:
            local_data = json.loads(local_content) if local_content.strip() else {}
            remote_data = json.loads(remote_content) if remote_content.strip() else {}
            base_data = json.loads(base_content) if base_content.strip() else {}
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON: %s", e)
            # Fall back to textual merge
            return self._textual_merge(local_content, remote_content, base_content)

        # Check for git conflict markers first
        if self._has_conflict_markers(local_content) or self._has_conflict_markers(remote_content):
            return self._resolve_conflict_markers(local_content, remote_content)

        # Perform semantic merge
        merged_data = self._merge_dicts(local_data, remote_data, base_data, path="")

        # Convert back to JSON
        merged_content = json.dumps(merged_data, indent=2)

        return merged_content, self.conflicts

    def _merge_dicts(self, local: Dict, remote: Dict, base: Dict, path: str) -> Dict:
        """Recursively merge dictionaries with semantic understanding."""
        merged = {}

        # All keys from all versions
        all_keys = set(local.keys()) | set(remote.keys()) | set(base.keys())

        for key in all_keys:
            current_path = f"{path}.{key}" if path else key

            local_val = local.get(key)
            remote_val = remote.get(key)
            base_val = base.get(key)

            # Special handling for Celebi-specific fields
            if key in ["uuid", "id"]:
                merged[key] = self._merge_uuid(local_val, remote_val, base_val, current_path)
            elif key in ["dependencies", "predecessors", "successors"]:
                merged[key] = self._merge_dependencies(local_val, remote_val, base_val, current_path)
            elif key in ["aliases", "path_to_alias"]:
                merged[key] = self._merge_aliases(local_val, remote_val, base_val, current_path)
            elif isinstance(local_val, dict) and isinstance(remote_val, dict):
                # Recursively merge nested dictionaries
                base_dict = base_val if isinstance(base_val, dict) else {}
                merged[key] = self._merge_dicts(local_val, remote_val, base_dict, current_path)
            elif isinstance(local_val, list) and isinstance(remote_val, list):
                merged[key] = self._merge_lists(local_val, remote_val, base_val, current_path)
            else:
                merged[key] = self._merge_values(local_val, remote_val, base_val, current_path)

        return merged

    def _merge_uuid(self, local_val: Any, remote_val: Any, base_val: Any, path: str) -> Any:
        """Merge UUID fields - must be identical or conflict."""
        if local_val == remote_val:
            return local_val or remote_val
        elif local_val == base_val:
            return remote_val  # Remote changed it
        elif remote_val == base_val:
            return local_val  # Local changed it
        else:
            # Both changed differently - conflict
            self.conflicts.append({
                'type': ConfigConflictType.UUID_CONFLICT.value,
                'path': path,
                'local': local_val,
                'remote': remote_val,
                'base': base_val,
                'description': f"UUID conflict at {path}: local='{local_val}', remote='{remote_val}'"
            })
            # Prefer local by default
            return local_val if self.prefer_local else remote_val

    def _merge_dependencies(self, local_val: Any, remote_val: Any,
                            base_val: Any, path: str) -> List:
        """Merge dependency lists using DAG union logic."""
        local_list = self._ensure_list(local_val)
        remote_list = self._ensure_list(remote_val)
        base_list = self._ensure_list(base_val)

        # Convert to sets for easier comparison
        local_set = set(local_list)
        remote_set = set(remote_list)
        base_set = set(base_list)

        # Additive changes: added in either branch
        added_local = local_set - base_set
        added_remote = remote_set - base_set

        # Subtractive changes: removed in either branch
        removed_local = base_set - local_set
        removed_remote = base_set - remote_set

        # Union of all dependencies
        merged_set = local_set.union(remote_set)

        # Check for conflicts
        if removed_local and removed_remote:
            # Both branches removed dependencies - check if same ones
            common_removed = removed_local.intersection(removed_remote)
            if common_removed:
                # Both removed same dependencies - remove from merged set
                merged_set = merged_set - common_removed
            else:
                # Different dependencies removed - conflict
                self.conflicts.append({
                    'type': ConfigConflictType.DEPENDENCY_CONFLICT.value,
                    'path': path,
                    'local': list(local_set),
                    'remote': list(remote_set),
                    'base': list(base_set),
                    'description': f"Dependency conflict at {path}: different removals"
                })

        return list(merged_set)

    def _merge_aliases(self, local_val: Any, remote_val: Any,
                       base_val: Any, path: str) -> Dict:
        """Merge alias mappings."""
        local_dict = self._ensure_dict(local_val)
        remote_dict = self._ensure_dict(remote_val)
        base_dict = self._ensure_dict(base_val)

        merged = {}
        all_keys = set(local_dict.keys()) | set(remote_dict.keys()) | set(base_dict.keys())

        for key in all_keys:
            local_alias = local_dict.get(key)
            remote_alias = remote_dict.get(key)
            base_alias = base_dict.get(key)

            if local_alias == remote_alias:
                merged[key] = local_alias or remote_alias
            elif local_alias == base_alias:
                merged[key] = remote_alias  # Remote changed it
            elif remote_alias == base_alias:
                merged[key] = local_alias  # Local changed it
            else:
                # Both changed differently - conflict
                self.conflicts.append({
                    'type': ConfigConflictType.ALIAS_CONFLICT.value,
                    'path': f"{path}.{key}",
                    'local': local_alias,
                    'remote': remote_alias,
                    'base': base_alias,
                    'description': f"Alias conflict for key '{key}': local='{local_alias}', remote='{remote_alias}'"
                })
                # Prefer local by default
                merged[key] = local_alias if self.prefer_local else remote_alias

        return merged

    def _merge_lists(self, local_list: List, remote_list: List,
                     base_list: List, path: str) -> List:
        """Merge lists - simple union for now."""
        if base_list is None:
            base_list = []

        # Simple union for lists
        merged_set = set(local_list) | set(remote_list)
        return list(merged_set)

    def _merge_values(self, local_val: Any, remote_val: Any,
                      base_val: Any, path: str) -> Any:
        """Merge simple values."""
        if local_val == remote_val:
            return local_val or remote_val
        elif local_val == base_val:
            return remote_val  # Remote changed it
        elif remote_val == base_val:
            return local_val  # Local changed it
        else:
            # Both changed differently - conflict
            self.conflicts.append({
                'type': ConfigConflictType.VALUE_CONFLICT.value,
                'path': path,
                'local': local_val,
                'remote': remote_val,
                'base': base_val,
                'description': f"Value conflict at {path}: local='{local_val}', remote='{remote_val}'"
            })
            # Prefer local by default
            return local_val if self.prefer_local else remote_val

    def _has_conflict_markers(self, content: str) -> bool:
        """Check if content contains git conflict markers."""
        conflict_patterns = [
            r'^<<<<<<<',
            r'^=======',
            r'^>>>>>>>'
        ]
        for line in content.split('\n'):
            for pattern in conflict_patterns:
                if re.match(pattern, line.strip()):
                    return True
        return False

    def _resolve_conflict_markers(self, local_content: str,
                                  remote_content: str) -> Tuple[str, List[Dict]]:
        """
        Resolve git conflict markers in configuration files.

        This parses conflict markers and applies semantic merge to the
        extracted local and remote sections.
        """
        logger.warning("Found git conflict markers, attempting semantic resolution")

        # Extract local and remote sections from conflict markers
        local_section = self._extract_section(local_content, '<<<<<<<', '=======')
        remote_section = self._extract_section(remote_content, '=======', '>>>>>>>')

        if not local_section or not remote_section:
            # Couldn't parse conflict markers - return local as fallback
            self.conflicts.append({
                'type': ConfigConflictType.CONFLICT_MARKER.value,
                'description': "Unparseable git conflict markers",
                'resolution': 'used_local_content'
            })
            return local_content, self.conflicts

        # Try to parse as YAML first, then JSON
        merged_content = None
        try:
            local_data = yaml.safe_load(local_section) or {}
            remote_data = yaml.safe_load(remote_section) or {}
            merged_data = self._merge_dicts(local_data, remote_data, {}, "")
            merged_content = yaml.dump(merged_data, default_flow_style=False, sort_keys=False)
        except yaml.YAMLError:
            try:
                local_data = json.loads(local_section) if local_section.strip() else {}
                remote_data = json.loads(remote_section) if remote_section.strip() else {}
                merged_data = self._merge_dicts(local_data, remote_data, {}, "")
                merged_content = json.dumps(merged_data, indent=2)
            except json.JSONDecodeError:
                # Neither YAML nor JSON - use textual merge
                merged_content = self._textual_merge_simple(local_section, remote_section)

        self.conflicts.append({
            'type': ConfigConflictType.CONFLICT_MARKER.value,
            'description': "Resolved git conflict markers semantically",
            'resolution': 'semantic_merge'
        })

        return merged_content, self.conflicts

    def _extract_section(self, content: str, start_marker: str,
                         end_marker: str) -> Optional[str]:
        """Extract section between conflict markers."""
        lines = content.split('\n')
        in_section = False
        section_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith(start_marker):
                in_section = True
                continue
            elif stripped.startswith(end_marker):
                break
            elif in_section:
                section_lines.append(line)

        return '\n'.join(section_lines) if section_lines else None

    def _textual_merge(self, local_content: str, remote_content: str,
                       base_content: str) -> Tuple[str, List[Dict]]:
        """Fallback textual merge when semantic merge fails."""
        # Simple heuristic: use local if prefer_local, otherwise remote
        if self.prefer_local:
            merged = local_content
        else:
            merged = remote_content

        self.conflicts.append({
            'type': ConfigConflictType.STRUCTURE_CONFLICT.value,
            'description': "Used textual merge due to parse errors",
            'resolution': 'textual_fallback'
        })

        return merged, self.conflicts

    def _textual_merge_simple(self, local_content: str,
                              remote_content: str) -> str:
        """Simple textual merge for non-parsable content."""
        if self.prefer_local:
            return local_content
        else:
            return remote_content

    def _ensure_list(self, value: Any) -> List:
        """Ensure value is a list."""
        if value is None:
            return []
        elif isinstance(value, list):
            return value
        elif isinstance(value, (str, int, float, bool)):
            return [value]
        else:
            try:
                return list(value)
            except (TypeError, ValueError):
                return [str(value)]

    def _ensure_dict(self, value: Any) -> Dict:
        """Ensure value is a dict."""
        if value is None:
            return {}
        elif isinstance(value, dict):
            return value
        else:
            # Try to convert if it's a list of pairs
            if isinstance(value, list) and all(isinstance(item, (list, tuple)) and len(item) == 2
                                               for item in value):
                return dict(value)
            else:
                return {}


def detect_config_file_type(content: str) -> str:
    """Detect if content is YAML or JSON."""
    content = content.strip()
    if not content:
        return "unknown"

    # Check for JSON
    if content.startswith('{') or content.startswith('['):
        try:
            json.loads(content)
            return "json"
        except json.JSONDecodeError:
            pass

    # Check for YAML
    try:
        yaml.safe_load(content)
        return "yaml"
    except yaml.YAMLError:
        pass

    return "unknown"