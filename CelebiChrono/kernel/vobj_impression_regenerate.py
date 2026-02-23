"""Impression regeneration for post-merge state synchronization.

This module handles regenerating impressions after a merge to ensure
the impression system reflects the merged project state.
"""
import os
import hashlib
import json
from typing import Dict, List, Set, Optional, Any
from logging import getLogger
from pathlib import Path

from .vobject import VObject
from .chern_cache import ChernCache

logger = getLogger("ChernLogger")
CHERN_CACHE = ChernCache.instance()


class ImpressionRegenerator(VObject):
    """Regenerates impressions from current project state after merge."""

    def __init__(self, path: str = "", project_path: str = ""):
        # Initialize Core with project path
        super().__init__(path, project_path)
        self.regenerated_count = 0
        self.skipped_count = 0
        self.failed_count = 0

    def regenerate_impressions(self, incremental: bool = True,
                               force: bool = False) -> Dict[str, int]:
        """
        Regenerate impressions for the current project.

        Args:
            incremental: Only regenerate impressions for changed objects
            force: Force regeneration even if impressions appear current

        Returns:
            Dictionary with regeneration statistics
        """
        logger.info("Starting impression regeneration (incremental=%s, force=%s)",
                    incremental, force)
        diagnostics = {
            'handled_objects': [],
            'skipped_objects': [],
            'failed_objects': []
        }

        # Get all objects in the project
        all_objects = self.sub_objects_recursively()

        # Filter to objects that support impressions
        impressionable_objects = [
            obj for obj in all_objects
            if hasattr(obj, 'impress') and callable(getattr(obj, 'impress'))
        ]

        logger.info("Found %d impressionable objects", len(impressionable_objects))

        if incremental and not force:
            changed_objects = self._identify_changed_objects(impressionable_objects)
        else:
            changed_objects = impressionable_objects

        logger.info("Regenerating impressions for %d objects", len(changed_objects))

        # Regenerate impressions
        for obj in changed_objects:
            self._regenerate_object_impression(obj, force)

        # Update parent-child relationships
        self._update_impression_lineage()

        stats = {
            'total_objects': len(impressionable_objects),
            'changed_objects': len(changed_objects),
            'regenerated': self.regenerated_count,
            'skipped': self.skipped_count,
            'failed': self.failed_count
        }

        logger.info("Impression regeneration completed: %s", stats)
        logger.debug("Detailed diagnostics: %s", diagnostics)
        return stats

    def _identify_changed_objects(self, objects: List) -> List:
        """
        Identify objects that have changed since their last impression.

        Args:
            objects: List of objects to check

        Returns:
            List of changed objects
        """
        changed = []

        for obj in objects:
            if not self._is_impression_current(obj):
                changed.append(obj)

        return changed

    def _is_impression_current(self, obj) -> bool:
        """
        Check if an object's impression is current.

        Compares the object's current state with its stored impression.
        """
        try:
            # Check if object has an impression
            if not hasattr(obj, 'is_impressed') or not obj.is_impressed():
                return False

            # Get current impression UUID
            current_impression = obj.impression()
            if not current_impression:
                return False

            # Check if impression matches current state
            # This would need to compute current state hash and compare
            # For now, use a simpler heuristic
            return self._check_impression_fast(obj, current_impression)

        except Exception as e:
            logger.warning("Error checking impression currency for %s: %s", obj, e)
            return False

    def _check_impression_fast(self, obj, impression_uuid: str) -> bool:
        """
        Fast check of impression currency using cached timestamps.

        This is a simplified version - the real implementation would
        need to compute content hashes.
        """
        # Check cache first
        cache_key = f"impression_check:{obj.invariant_path()}:{impression_uuid}"
        cached = CHERN_CACHE.get(cache_key)
        if cached is not None:
            return cached

        # Simplified check: compare modification times
        obj_path = obj.path if hasattr(obj, 'path') else None
        if not obj_path or not os.path.exists(obj_path):
            # Can't check - assume not current
            CHERN_CACHE.set(cache_key, False)
            return False

        # Get impression directory
        impression_dir = os.path.join('.celebi', 'impressions', impression_uuid)
        if not os.path.exists(impression_dir):
            # Impression doesn't exist
            CHERN_CACHE.set(cache_key, False)
            return False

        # Compare modification times
        obj_mtime = os.path.getmtime(obj_path)
        impression_mtime = os.path.getmtime(impression_dir)

        # If object modified after impression, impression is stale
        is_current = obj_mtime <= impression_mtime
        CHERN_CACHE.set(cache_key, is_current)

        return is_current

    def _regenerate_object_impression(self, obj, force: bool = False):
        """
        Regenerate impression for a single object.

        Args:
            obj: The object to regenerate impression for
            force: Force regeneration even if impression appears current
        """
        try:
            obj_path = obj.invariant_path() if hasattr(obj, 'invariant_path') else str(obj)

            # Check if regeneration is needed
            if not force and self._is_impression_current(obj):
                logger.debug("Skipping %s - impression appears current", obj_path)
                diagnostics['skipped_objects'].append(obj_path)
                self.skipped_count += 1
                return

            # Regenerate impression
            logger.debug("Regenerating impression for %s", obj_path)

            # Call object's impress method
            if hasattr(obj, 'impress') and callable(getattr(obj, 'impress')):
                # Note: impress() doesn't accept force parameter, but we've already
                # skipped the currency check if force=True
                try:
                    obj.impress()  # No force parameter
                    self.regenerated_count += 1
                    logger.debug("Successfully regenerated impression for %s", obj_path)
                    diagnostics['handled_objects'].append(obj_path)
                except Exception as e:
                    self.failed_count += 1
                    logger.warning("Failed to regenerate impression for %s: %s", obj_path, e)
                    diagnostics['failed_objects'].append({'object': obj_path, 'error': str(e)})
            else:
                self.failed_count += 1
                logger.warning("Object %s doesn't support impression regeneration", obj_path)

        except Exception as e:
            self.failed_count += 1
            logger.error("Error regenerating impression for %s: %s", obj, e)

    def _update_impression_lineage(self):
        """Update parent-child relationships between impressions."""
        # This would update the impression graph to reflect new parent-child
        # relationships after regeneration
        # For now, just log that this would happen
        logger.debug("Would update impression lineage (not implemented in prototype)")

    def regenerate_deterministic_uuids(self) -> Dict[str, List[str]]:
        """
        Regenerate deterministic UUIDs for all objects in the project.

        This ensures UUIDs are consistent with the current project state.

        Returns:
            Dictionary mapping old UUIDs to new UUIDs
        """
        logger.info("Regenerating deterministic UUIDs")

        uuid_mapping = {}
        all_objects = self.sub_objects_recursively()

        for obj in all_objects:
            if not hasattr(obj, 'uuid') or not hasattr(obj, 'generate_deterministic_uuid'):
                continue

            old_uuid = getattr(obj, 'uuid', None)
            if not old_uuid:
                continue

            # Generate new UUID based on current state
            try:
                new_uuid = obj.generate_deterministic_uuid()
                if new_uuid and new_uuid != old_uuid:
                    uuid_mapping[old_uuid] = new_uuid

                    # Update object's UUID
                    obj.uuid = new_uuid

                    # Update config file if it exists
                    if hasattr(obj, 'config_file'):
                        config = obj.config_file
                        if hasattr(config, 'write_variable'):
                            config.write_variable('uuid', new_uuid)

                    logger.debug("Updated UUID for %s: %s -> %s",
                                 obj.invariant_path(), old_uuid, new_uuid)

            except Exception as e:
                logger.warning("Failed to regenerate UUID for %s: %s", obj, e)

        logger.info("Regenerated %d UUIDs", len(uuid_mapping))
        return uuid_mapping

    def validate_impression_consistency(self) -> Dict[str, Any]:
        """
        Validate that all impressions are consistent with current project state.

        Returns:
            Dictionary with validation results
        """
        logger.info("Validating impression consistency")

        results = {
            'total_objects': 0,
            'consistent_objects': 0,
            'inconsistent_objects': 0,
            'missing_impressions': 0,
            'errors': []
        }

        all_objects = self.sub_objects_recursively()

        for obj in all_objects:
            results['total_objects'] += 1

            try:
                if not hasattr(obj, 'is_impressed'):
                    continue

                if not obj.is_impressed():
                    results['missing_impressions'] += 1
                    continue

                # Check impression consistency
                is_consistent = self._check_impression_consistency(obj)
                if is_consistent:
                    results['consistent_objects'] += 1
                else:
                    results['inconsistent_objects'] += 1
                    results['errors'].append({
                        'object': obj.invariant_path() if hasattr(obj, 'invariant_path') else str(obj),
                        'issue': 'Impression inconsistent with current state'
                    })

            except Exception as e:
                results['inconsistent_objects'] += 1
                results['errors'].append({
                    'object': obj.invariant_path() if hasattr(obj, 'invariant_path') else str(obj),
                    'issue': f'Validation error: {e}'
                })

        logger.info("Impression consistency validation completed: %s", results)
        return results

    def _check_impression_consistency(self, obj) -> bool:
        """
        Check if an object's impression is consistent with its current state.

        This is a more thorough check than _is_impression_current.
        """
        # Simplified implementation
        # Real implementation would compare content hashes

        if not hasattr(obj, 'impression'):
            return False

        impression_uuid = obj.impression()
        if not impression_uuid:
            return False

        # Check if impression directory exists
        impression_dir = os.path.join('.celebi', 'impressions', impression_uuid)
        if not os.path.exists(impression_dir):
            return False

        # Check if config.json exists in impression
        config_path = os.path.join(impression_dir, 'config.json')
        if not os.path.exists(config_path):
            return False

        # Compare key metadata
        try:
            with open(config_path, 'r') as f:
                impression_config = json.load(f)

            # Get current config
            if hasattr(obj, 'config_file') and hasattr(obj.config_file, 'read_variable'):
                current_uuid = obj.config_file.read_variable('uuid')
                impression_uuid_from_config = impression_config.get('uuid')

                if current_uuid and impression_uuid_from_config:
                    return current_uuid == impression_uuid_from_config

        except Exception:
            pass

        return False

    def cleanup_stale_impressions(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean up impressions that are no longer referenced.

        Args:
            dry_run: If True, only report what would be deleted

        Returns:
            Dictionary with cleanup statistics
        """
        logger.info("Cleaning up stale impressions (dry_run=%s)", dry_run)

        stats = {
            'total_impressions': 0,
            'referenced_impressions': 0,
            'stale_impressions': 0,
            'deleted_impressions': 0,
            'failed_deletions': 0,
            'stale_list': []
        }

        # Get all impression directories
        impressions_dir = os.path.join('.celebi', 'impressions')
        if not os.path.exists(impressions_dir):
            logger.warning("Impressions directory not found: %s", impressions_dir)
            return stats

        # Get all impression UUIDs from directory names
        all_impressions = []
        for item in os.listdir(impressions_dir):
            item_path = os.path.join(impressions_dir, item)
            if os.path.isdir(item_path):
                all_impressions.append(item)

        stats['total_impressions'] = len(all_impressions)

        # Get referenced impressions from all objects
        referenced_impressions = set()
        all_objects = self.sub_objects_recursively()

        for obj in all_objects:
            if hasattr(obj, 'impression'):
                try:
                    impression = obj.impression()
                    if impression:
                        referenced_impressions.add(impression)
                except Exception:
                    pass

            # Also check predecessor/successor impressions
            if hasattr(obj, 'pred_impressions'):
                try:
                    pred_impressions = obj.pred_impressions()
                    if pred_impressions:
                        referenced_impressions.update(pred_impressions)
                except Exception:
                    pass

        stats['referenced_impressions'] = len(referenced_impressions)

        # Identify stale impressions
        for impression_uuid in all_impressions:
            if impression_uuid not in referenced_impressions:
                stats['stale_impressions'] += 1
                stats['stale_list'].append(impression_uuid)

                if not dry_run:
                    # Delete stale impression
                    impression_dir = os.path.join(impressions_dir, impression_uuid)
                    try:
                        import shutil
                        shutil.rmtree(impression_dir)
                        stats['deleted_impressions'] += 1
                        logger.debug("Deleted stale impression: %s", impression_uuid)
                    except Exception as e:
                        stats['failed_deletions'] += 1
                        logger.warning("Failed to delete impression %s: %s", impression_uuid, e)

        logger.info("Stale impression cleanup completed: %s", stats)
        return stats