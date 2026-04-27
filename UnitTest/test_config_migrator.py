"""Tests for the ConfigMigrator utility."""

import unittest
import tempfile
import json
import os
from unittest.mock import patch, MagicMock

from CelebiChrono.utils import config_migrator
from CelebiChrono.utils.config_migrator import ConfigMigrator, MigrationResult


class TestMigrationResult(unittest.TestCase):
    """Tests for MigrationResult dataclass."""

    def test_summary_no_errors(self):
        """Test summary generation with no errors."""
        result = MigrationResult(migrated_count=5, skipped_count=2)
        summary = result.summary()

        self.assertIn("Migrated:  5", summary)
        self.assertIn("Skipped:   2", summary)
        self.assertIn("Errors:    None", summary)

    def test_summary_with_errors(self):
        """Test summary generation with errors."""
        result = MigrationResult(migrated_count=5, skipped_count=2)
        result.add_error("/path/to/config.json", "Invalid JSON")
        summary = result.summary()

        self.assertIn("Migrated:  5", summary)
        self.assertIn("Errors:    1 errors", summary)
        self.assertIn("/path/to/config.json", summary)

    def test_summary_dry_run(self):
        """Test that dry_run is noted in summary."""
        result = MigrationResult(migrated_count=5, dry_run=True)
        summary = result.summary()

        self.assertIn("(DRY RUN)", summary)


class TestConfigMigrator(unittest.TestCase):
    """Tests for ConfigMigrator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_config(self, path, config_dict):
        """Helper to create a config file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(config_dict, f)

    def test_init_valid_path(self):
        """Test initialization with valid project path."""
        migrator = ConfigMigrator(self.temp_dir)
        self.assertEqual(migrator.project_path, self.temp_dir)

    def test_init_invalid_path(self):
        """Test initialization with invalid project path."""
        with self.assertRaises(ValueError):
            ConfigMigrator("/nonexistent/path")

    def test_migrate_single_object(self):
        """Test migrating a single object config."""
        # Create old-style config with mixed fields
        config_path = os.path.join(self.temp_dir, ".celebi", "config.json")
        old_config = {
            "object_type": "task",
            "auto_download": True,
            "default_runner": "local",
            "use_eos": False,
            "predecessors": ["task1"],
        }
        self._create_config(config_path, old_config)

        # Migrate with dry_run=False
        migrator = ConfigMigrator(self.temp_dir)
        result = migrator.migrate(dry_run=False)

        # Check results
        self.assertEqual(result.migrated_count, 1)
        self.assertEqual(result.skipped_count, 0)

        # Check that config.json has shared fields only
        with open(config_path) as f:
            shared_config = json.load(f)
        self.assertIn("object_type", shared_config)
        self.assertIn("predecessors", shared_config)
        self.assertNotIn("auto_download", shared_config)

        # Check that config.local.json was created
        local_config_path = os.path.join(self.temp_dir, ".celebi", "config.local.json")
        self.assertTrue(os.path.isfile(local_config_path))
        with open(local_config_path) as f:
            local_config = json.load(f)
        self.assertIn("auto_download", local_config)
        self.assertIn("default_runner", local_config)
        self.assertNotIn("object_type", local_config)

    def test_migrate_dry_run(self):
        """Test that dry_run doesn't modify files."""
        config_path = os.path.join(self.temp_dir, ".celebi", "config.json")
        old_config = {
            "object_type": "task",
            "auto_download": True,
            "default_runner": "local",
        }
        self._create_config(config_path, old_config)

        # Migrate with dry_run=True
        migrator = ConfigMigrator(self.temp_dir)
        result = migrator.migrate(dry_run=True)

        # Check that migration was planned but not executed
        self.assertEqual(result.migrated_count, 1)
        self.assertTrue(result.dry_run)

        # Check that config.local.json was NOT created
        local_config_path = os.path.join(self.temp_dir, ".celebi", "config.local.json")
        self.assertFalse(os.path.isfile(local_config_path))

        # Check that original config is unchanged
        with open(config_path) as f:
            current_config = json.load(f)
        self.assertEqual(current_config, old_config)

    def test_migrate_already_migrated(self):
        """Test that already-migrated configs are skipped."""
        celebi_dir = os.path.join(self.temp_dir, ".celebi")
        os.makedirs(celebi_dir)

        # Create both config files (migrated state)
        config_path = os.path.join(celebi_dir, "config.json")
        local_config_path = os.path.join(celebi_dir, "config.local.json")
        self._create_config(config_path, {"object_type": "task"})
        self._create_config(local_config_path, {"auto_download": True})

        # Migrate
        migrator = ConfigMigrator(self.temp_dir)
        result = migrator.migrate(dry_run=False)

        # Check that it was skipped
        self.assertEqual(result.migrated_count, 0)
        self.assertEqual(result.skipped_count, 1)

    def test_migrate_recursive(self):
        """Test recursive migration of entire project tree."""
        # Create project with multiple objects
        project_path = self.temp_dir
        objects = ["task1", "task2", "dir1"]

        for obj in objects:
            config_path = os.path.join(project_path, obj, ".celebi", "config.json")
            old_config = {
                "object_type": "task",
                "auto_download": True,
                "default_runner": "local",
            }
            self._create_config(config_path, old_config)

        # Migrate
        migrator = ConfigMigrator(project_path)
        result = migrator.migrate(dry_run=False)

        # Check results
        self.assertEqual(result.migrated_count, 3)
        self.assertEqual(result.skipped_count, 0)

        # Verify each object was migrated
        for obj in objects:
            local_config_path = os.path.join(
                project_path, obj, ".celebi", "config.local.json"
            )
            self.assertTrue(os.path.isfile(local_config_path))

    def test_migrate_unknown_fields(self):
        """Test that unknown fields are preserved in shared config."""
        config_path = os.path.join(self.temp_dir, ".celebi", "config.json")
        old_config = {
            "object_type": "task",
            "auto_download": True,
            "custom_field": "custom_value",
        }
        self._create_config(config_path, old_config)

        # Migrate
        migrator = ConfigMigrator(self.temp_dir)
        result = migrator.migrate(dry_run=False)

        # Check that custom field was preserved in shared config
        with open(config_path) as f:
            shared_config = json.load(f)
        self.assertIn("custom_field", shared_config)
        self.assertEqual(shared_config["custom_field"], "custom_value")

    def test_migrate_already_new_format(self):
        """Test that configs in new format are skipped."""
        config_path = os.path.join(self.temp_dir, ".celebi", "config.json")
        # New format: only object_type
        self._create_config(config_path, {"object_type": "task"})

        # Migrate
        migrator = ConfigMigrator(self.temp_dir)
        result = migrator.migrate(dry_run=False)

        # Check that it was skipped
        self.assertEqual(result.migrated_count, 0)
        self.assertEqual(result.skipped_count, 1)

    def test_migrate_invalid_config(self):
        """Test handling of invalid config files."""
        config_path = os.path.join(self.temp_dir, ".celebi", "config.json")
        os.makedirs(os.path.dirname(config_path))

        # Write invalid JSON
        with open(config_path, 'w') as f:
            f.write("{invalid json")

        # Migrate should handle error gracefully
        migrator = ConfigMigrator(self.temp_dir)
        result = migrator.migrate(dry_run=False)

        # Check that error was recorded
        self.assertEqual(result.migrated_count, 0)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("Cannot read config", result.errors[0][1])

    def test_migrate_config_not_dict(self):
        """Test handling of config that is not a dict."""
        config_path = os.path.join(self.temp_dir, ".celebi", "config.json")
        os.makedirs(os.path.dirname(config_path))

        # Write JSON array instead of object
        with open(config_path, 'w') as f:
            json.dump([1, 2, 3], f)

        # Migrate should handle error gracefully
        migrator = ConfigMigrator(self.temp_dir)
        result = migrator.migrate(dry_run=False)

        # Check that error was recorded
        self.assertEqual(result.migrated_count, 0)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("not a JSON object", result.errors[0][1])

    def test_verify_valid(self):
        """Test verification of successfully migrated configs."""
        config_path = os.path.join(self.temp_dir, ".celebi", "config.json")
        local_config_path = os.path.join(self.temp_dir, ".celebi", "config.local.json")

        self._create_config(config_path, {"object_type": "task"})
        self._create_config(local_config_path, {"auto_download": True})

        # Verify
        migrator = ConfigMigrator(self.temp_dir)
        self.assertTrue(migrator.verify())

    def test_verify_missing_object_type(self):
        """Test verification fails for missing object_type."""
        config_path = os.path.join(self.temp_dir, ".celebi", "config.json")
        self._create_config(config_path, {})  # Empty config

        # Verify should fail
        migrator = ConfigMigrator(self.temp_dir)
        self.assertFalse(migrator.verify())


if __name__ == '__main__':
    unittest.main()
