"""Config migration utility to convert old single-file config to new two-tier structure.

This module provides utilities to migrate Celebi projects from the old configuration
format (single config.json with all settings mixed) to the new two-tier format
(separate config.json for shared metadata and config.local.json for local settings).
"""

import json
import os
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple

from . import csys
from . import metadata

logger = logging.getLogger("ChernLogger")


# Field categorization
SHARED_FIELDS = {
    "object_type", "chern_version", "project_uuid",
    "predecessors", "successors",
    "path_to_alias", "alias_to_path"
}

LOCAL_FIELDS = {
    "auto_download", "default_runner", "use_eos"
}


@dataclass
class MigrationResult:
    """Result of a config migration operation."""
    migrated_count: int = 0
    skipped_count: int = 0
    errors: List[Tuple[str, str]] = field(default_factory=list)
    dry_run: bool = False

    def add_error(self, path: str, error: str) -> None:
        """Add an error to the result."""
        self.errors.append((path, error))

    def summary(self) -> str:
        """Get a human-readable summary of the migration result."""
        lines = []
        mode = " (DRY RUN)" if self.dry_run else ""
        lines.append(f"Migration Summary{mode}")
        lines.append("-" * 50)
        lines.append(f"Migrated:  {self.migrated_count} objects")
        lines.append(f"Skipped:   {self.skipped_count} objects (already migrated)")

        if self.errors:
            lines.append(f"Errors:    {len(self.errors)} errors")
            for path, error in self.errors:
                lines.append(f"  - {path}: {error}")
        else:
            lines.append("Errors:    None")

        return "\n".join(lines)


class ConfigMigrator:
    """Migrates Celebi project configs from old single-file to new two-tier format."""

    def __init__(self, project_path: str) -> None:
        """Initialize the migrator with a project path.

        Args:
            project_path: Root path of the Celebi project to migrate.
        """
        self.project_path = csys.strip_path_string(project_path)
        if not os.path.isdir(self.project_path):
            raise ValueError(f"Project path does not exist: {project_path}")

    def migrate(self, dry_run: bool = True) -> MigrationResult:
        """Migrate all configs in the project tree.

        Args:
            dry_run: If True, simulate changes without writing files.

        Returns:
            MigrationResult with statistics and any errors.
        """
        result = MigrationResult(dry_run=dry_run)

        # Walk through all directories in the project
        for root, dirs, files in os.walk(self.project_path):
            # Check if this directory has a .celebi/config.json
            celebi_path = os.path.join(root, ".celebi")
            config_path = os.path.join(celebi_path, "config.json")

            if os.path.isfile(config_path):
                try:
                    if self._migrate_object(config_path, dry_run):
                        result.migrated_count += 1
                    else:
                        result.skipped_count += 1
                except Exception as e:
                    result.add_error(config_path, str(e))
                    logger.error(f"Error migrating {config_path}: {e}")

        return result

    def _migrate_object(self, config_path: str, dry_run: bool = True) -> bool:
        """Migrate a single object's config file.

        Args:
            config_path: Path to the config.json file.
            dry_run: If True, don't write files.

        Returns:
            True if migration was performed, False if skipped (already migrated).

        Raises:
            Exception: If the config cannot be migrated.
        """
        # Check if already migrated
        config_dir = os.path.dirname(config_path)
        local_config_path = os.path.join(config_dir, "config.local.json")

        if os.path.isfile(local_config_path):
            logger.debug(f"Already migrated: {config_path}")
            return False

        # Read the old config
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                old_config = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise Exception(f"Cannot read config: {e}")

        if not isinstance(old_config, dict):
            raise Exception(f"Config is not a JSON object")

        # If config is empty or only has object_type, already in new format
        if len(old_config) <= 1 and "object_type" in old_config:
            logger.debug(f"Already in new format: {config_path}")
            return False

        # Separate fields into shared and local
        shared_config = {}
        local_config = {}

        for key, value in old_config.items():
            if key in SHARED_FIELDS:
                shared_config[key] = value
            elif key in LOCAL_FIELDS:
                local_config[key] = value
            else:
                # Unknown fields go to shared (preserves data)
                shared_config[key] = value

        # Write configs if dry_run is False
        if not dry_run:
            # Write shared config (overwrite existing)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(shared_config, f, indent=2)

            # Write local config (create new)
            if local_config:
                os.makedirs(config_dir, exist_ok=True)
                with open(local_config_path, 'w', encoding='utf-8') as f:
                    json.dump(local_config, f, indent=2)

        logger.info(
            f"Migrated {config_path}: "
            f"{len(shared_config)} shared, {len(local_config)} local"
        )
        return True

    def verify(self) -> bool:
        """Verify that migration was successful.

        Checks that all config files can be read correctly with TwoTierConfigFile.

        Returns:
            True if all configs are valid, False otherwise.
        """
        all_valid = True

        for root, dirs, files in os.walk(self.project_path):
            config_path = os.path.join(root, ".celebi", "config.json")

            if os.path.isfile(config_path):
                try:
                    config = metadata.TwoTierConfigFile(config_path)
                    # Try reading object_type to verify structure
                    obj_type = config.read_variable("object_type")
                    if not obj_type:
                        logger.warning(f"Missing object_type in {config_path}")
                        all_valid = False
                except Exception as e:
                    logger.error(f"Verification failed for {config_path}: {e}")
                    all_valid = False

        return all_valid
