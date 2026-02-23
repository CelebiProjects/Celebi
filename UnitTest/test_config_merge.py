"""Unit tests for configuration file merging."""
import unittest
import yaml
import json

from CelebiChrono.utils.config_merge import ConfigMerger, detect_config_file_type


class TestConfigMerger(unittest.TestCase):
    """Test cases for ConfigMerger class."""

    def setUp(self):
        """Set up test fixtures."""
        self.merger = ConfigMerger(prefer_local=True)

    def test_yaml_merge_no_conflicts(self):
        """Test merging YAML files with no conflicts."""
        local = """
name: test
version: 1.0
dependencies:
  - task1
  - task2
"""
        remote = """
name: test
version: 1.0
dependencies:
  - task1
  - task2
"""
        base = """
name: test
version: 1.0
dependencies:
  - task1
  - task2
"""

        merged, conflicts = self.merger.merge_yaml_files(local, remote, base)

        # Should merge without conflicts
        self.assertEqual(len(conflicts), 0)

        # Parse merged result
        parsed = yaml.safe_load(merged)
        self.assertEqual(parsed['name'], 'test')
        self.assertEqual(parsed['version'], '1.0')
        self.assertEqual(set(parsed['dependencies']), {'task1', 'task2'})

    def test_yaml_merge_additive_dependencies(self):
        """Test merging YAML with additive dependency changes."""
        base = """
dependencies:
  - task1
"""
        local = """
dependencies:
  - task1
  - task2
"""
        remote = """
dependencies:
  - task1
  - task3
"""

        merged, conflicts = self.merger.merge_yaml_files(local, remote, base)

        # Should have union of dependencies
        parsed = yaml.safe_load(merged)
        deps = set(parsed['dependencies'])
        self.assertEqual(deps, {'task1', 'task2', 'task3'})
        self.assertEqual(len(conflicts), 0)

    def test_yaml_merge_uuid_conflict(self):
        """Test merging YAML with UUID conflict."""
        base = """
uuid: abc-123
name: test
"""
        local = """
uuid: def-456
name: test
"""
        remote = """
uuid: ghi-789
name: test
"""

        merged, conflicts = self.merger.merge_yaml_files(local, remote, base)

        # Should have UUID conflict
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['type'], 'uuid_conflict')

        # Should prefer local UUID (since prefer_local=True)
        parsed = yaml.safe_load(merged)
        self.assertEqual(parsed['uuid'], 'def-456')

    def test_json_merge_no_conflicts(self):
        """Test merging JSON files with no conflicts."""
        local = json.dumps({
            "name": "test",
            "version": "1.0",
            "dependencies": ["task1", "task2"]
        })
        remote = json.dumps({
            "name": "test",
            "version": "1.0",
            "dependencies": ["task1", "task2"]
        })
        base = json.dumps({
            "name": "test",
            "version": "1.0",
            "dependencies": ["task1", "task2"]
        })

        merged, conflicts = self.merger.merge_json_files(local, remote, base)

        self.assertEqual(len(conflicts), 0)

        parsed = json.loads(merged)
        self.assertEqual(parsed['name'], 'test')
        self.assertEqual(parsed['version'], '1.0')

    def test_json_merge_alias_conflict(self):
        """Test merging JSON with alias conflicts."""
        base = json.dumps({
            "aliases": {
                "input1": "task1",
                "input2": "task2"
            }
        })
        local = json.dumps({
            "aliases": {
                "input1": "task1",
                "input2": "taskX"  # Changed
            }
        })
        remote = json.dumps({
            "aliases": {
                "input1": "task1",
                "input2": "taskY"  # Changed differently
            }
        })

        merged, conflicts = self.merger.merge_json_files(local, remote, base)

        # Should have alias conflict
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['type'], 'alias_conflict')

        # Should prefer local (since prefer_local=True)
        parsed = json.loads(merged)
        self.assertEqual(parsed['aliases']['input2'], 'taskX')

    def test_merge_with_conflict_markers(self):
        """Test merging files with git conflict markers."""
        content_with_conflict = """<<<<<<< HEAD
dependencies:
  - task1
  - task2
=======
dependencies:
  - task1
  - task3
>>>>>>> feature
"""

        # Simpler test - just check that it handles conflict markers
        merged, conflicts = self.merger.merge_yaml_files(
            content_with_conflict,
            content_with_conflict,
            ""
        )

        # Should detect conflict markers
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['type'], 'conflict_marker')

    def test_detect_config_file_type(self):
        """Test config file type detection."""
        # Test JSON detection
        json_content = '{"name": "test", "version": 1}'
        self.assertEqual(detect_config_file_type(json_content), 'json')

        # Test YAML detection
        yaml_content = 'name: test\nversion: 1'
        self.assertEqual(detect_config_file_type(yaml_content), 'yaml')

        # Test unknown
        unknown_content = 'This is not JSON or YAML'
        self.assertEqual(detect_config_file_type(unknown_content), 'unknown')

    def test_remote_preference(self):
        """Test merging with remote preference."""
        # Create merger that prefers remote
        remote_merger = ConfigMerger(prefer_local=False)

        base = """
uuid: abc-123
"""
        local = """
uuid: def-456
"""
        remote = """
uuid: ghi-789
"""

        merged, conflicts = remote_merger.merge_yaml_files(local, remote, base)

        # Should prefer remote UUID
        parsed = yaml.safe_load(merged)
        self.assertEqual(parsed['uuid'], 'ghi-789')

    def test_merge_empty_files(self):
        """Test merging empty or invalid files."""
        # Test with empty content
        merged, conflicts = self.merger.merge_yaml_files("", "", "")
        self.assertEqual(len(conflicts), 0)

        # Test with invalid YAML (should fall back to textual merge)
        invalid = "not: valid: yaml"
        merged, conflicts = self.merger.merge_yaml_files(invalid, invalid, invalid)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['type'], 'structure_conflict')

    def test_merge_complex_nested(self):
        """Test merging complex nested structures."""
        base = """
metadata:
  author: alice
  created: 2024-01-01
config:
  params:
    param1: value1
"""
        local = """
metadata:
  author: alice
  created: 2024-01-01
  updated: 2024-02-01
config:
  params:
    param1: value1
    param2: value2
"""
        remote = """
metadata:
  author: alice
  created: 2024-01-01
config:
  params:
    param1: modified
    param3: value3
"""

        merged, conflicts = self.merger.merge_yaml_files(local, remote, base)

        parsed = yaml.safe_load(merged)

        # Should have updated date from local
        self.assertEqual(parsed['metadata']['updated'], '2024-02-01')

        # Should have param conflict (param1 changed differently)
        param_conflicts = [c for c in conflicts if 'param1' in str(c)]
        self.assertGreater(len(param_conflicts), 0)

        # Should prefer local param1 (since prefer_local=True)
        self.assertEqual(parsed['config']['params']['param1'], 'value1')


if __name__ == '__main__':
    unittest.main()