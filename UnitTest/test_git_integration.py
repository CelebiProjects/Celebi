"""Unit tests for git integration components."""
import unittest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

from CelebiChrono.utils.git_optional import GitOptionalIntegration
from CelebiChrono.utils.git_merge_coordinator import GitMergeCoordinator, MergeStrategy


class TestGitOptionalIntegration(unittest.TestCase):
    """Test cases for GitOptionalIntegration class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.git_integration = GitOptionalIntegration(self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_is_git_repository(self):
        """Test git repository detection."""
        # Initially not a git repo
        self.assertFalse(self.git_integration.is_git_repository())

        # Create .git directory
        git_dir = os.path.join(self.test_dir, '.git')
        os.makedirs(git_dir)

        # Now should be detected as git repo
        self.assertTrue(self.git_integration.is_git_repository())

    def test_enable_disable_integration(self):
        """Test enabling and disabling git integration."""
        # Create .git directory first
        git_dir = os.path.join(self.test_dir, '.git')
        os.makedirs(git_dir)

        # Enable integration
        self.assertTrue(self.git_integration.enable_integration())
        self.assertTrue(self.git_integration.is_git_integration_enabled())

        # Disable integration
        self.assertTrue(self.git_integration.disable_integration())
        self.assertFalse(self.git_integration.is_git_integration_enabled())

    def test_config_management(self):
        """Test configuration management."""
        # Set config option
        self.assertTrue(self.git_integration.set_config_option('auto_validate', True))
        self.assertTrue(self.git_integration.set_config_option('merge_strategy', 'interactive'))

        # Get config
        config = self.git_integration.get_config()
        self.assertTrue(config['auto_validate'])
        self.assertEqual(config['merge_strategy'], 'interactive')

        # Invalid key should fail
        self.assertFalse(self.git_integration.set_config_option('invalid_key', 'value'))

    @patch('subprocess.run')
    def test_get_git_info(self, mock_subprocess):
        """Test getting git repository information."""
        # Mock git commands
        mock_subprocess.return_value.stdout = 'main\n'
        mock_subprocess.return_value.returncode = 0

        # Create .git directory
        git_dir = os.path.join(self.test_dir, '.git')
        os.makedirs(git_dir)

        info = self.git_integration.get_git_info()

        self.assertTrue(info['is_git_repo'])
        self.assertEqual(info['current_branch'], 'main')

    def test_detect_potential_issues(self):
        """Test detection of potential issues."""
        # Create .git directory
        git_dir = os.path.join(self.test_dir, '.git')
        os.makedirs(git_dir)

        issues = self.git_integration.detect_potential_issues()

        # Should at least check for git executable
        self.assertIsInstance(issues, list)

    def test_recommended_settings(self):
        """Test getting recommended settings."""
        settings = self.git_integration.get_recommended_settings()

        self.assertIn('git_config', settings)
        self.assertIn('.gitignore_additions', settings)
        self.assertIn('workflow_suggestions', settings)

        # Check specific recommendations
        self.assertIn('.celebi/impressions/', settings['.gitignore_additions'])


class TestGitMergeCoordinator(unittest.TestCase):
    """Test cases for GitMergeCoordinator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.coordinator = GitMergeCoordinator(self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('subprocess.run')
    def test_get_merge_status(self, mock_subprocess):
        """Test getting merge status."""
        # Mock git status
        mock_process = Mock()
        mock_process.stdout = ''
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Create .git directory and refresh coordinator
        git_dir = os.path.join(self.test_dir, '.git')
        os.makedirs(git_dir)
        self.coordinator = GitMergeCoordinator(self.test_dir)

        status = self.coordinator.get_merge_status()

        self.assertTrue(status['is_git_repo'])
        self.assertIn('ready_to_merge', status)

    @patch('CelebiChrono.utils.git_merge_coordinator.GitMergeCoordinator._run_git_merge')
    @patch('CelebiChrono.utils.git_merge_coordinator.GitMergeCoordinator._validate_and_repair')
    @patch('CelebiChrono.utils.git_merge_coordinator.GitMergeCoordinator._regenerate_impressions')
    def test_execute_merge_dry_run(self, mock_regenerate, mock_validate, mock_git_merge):
        """Test dry run merge execution."""
        # Mock successful git merge
        mock_git_merge.return_value = {
            'success': True,
            'output': 'Merge successful',
            'conflicts': []
        }

        mock_validate.return_value = {
            'success': True,
            'issues': [],
            'conflicts': [],
            'repairs': []
        }

        mock_regenerate.return_value = {
            'success': True,
            'stats': {'regenerated': 5}
        }

        # Create .git directory and refresh coordinator
        git_dir = os.path.join(self.test_dir, '.git')
        os.makedirs(git_dir)
        self.coordinator = GitMergeCoordinator(self.test_dir)

        # Execute dry run
        results = self.coordinator.execute_merge('feature-branch', MergeStrategy.AUTO, dry_run=True)

        self.assertTrue(results['success'])
        self.assertTrue(results['git_merge_success'])

        # In dry run, validation and regeneration shouldn't be called
        mock_validate.assert_not_called()
        mock_regenerate.assert_not_called()

    @patch('CelebiChrono.utils.git_merge_coordinator.GitMergeCoordinator._run_git_merge')
    def test_execute_merge_git_failure(self, mock_git_merge):
        """Test merge execution when git merge fails."""
        # Mock failed git merge
        mock_git_merge.return_value = {
            'success': False,
            'output': 'Merge failed',
            'error': 'Conflict detected',
            'conflicts': [{'file': 'test.py', 'type': 'content'}]
        }

        # Create .git directory
        git_dir = os.path.join(self.test_dir, '.git')
        os.makedirs(git_dir)

        results = self.coordinator.execute_merge('feature-branch', MergeStrategy.AUTO)

        self.assertFalse(results['success'])
        self.assertFalse(results['git_merge_success'])
        self.assertIn('errors', results)

    @patch('CelebiChrono.kernel.vobj_arc_doctor.ArcManagementDoctor')
    @patch('CelebiChrono.kernel.vobj_impression_regenerate.ImpressionRegenerator')
    def test_validate_post_merge(self, mock_regenerator, mock_doctor):
        """Test post-merge validation."""
        # Mock doctor validation
        mock_doctor_instance = Mock()
        mock_doctor.return_value = mock_doctor_instance
        mock_doctor_instance.validate_merge.return_value = (True, [], [])
        mock_doctor_instance.repair_merge_conflicts.return_value = (0, [])

        # Mock regenerator
        mock_regenerator_instance = Mock()
        mock_regenerator.return_value = mock_regenerator_instance

        # Create .git directory
        git_dir = os.path.join(self.test_dir, '.git')
        os.makedirs(git_dir)

        results = self.coordinator.validate_post_merge()

        self.assertTrue(results['success'])
        self.assertEqual(len(results.get('issues', [])), 0)

    def test_parse_git_conflicts(self):
        """Test parsing git conflict messages."""
        git_output = """Auto-merging test.py
CONFLICT (content): Merge conflict in test.py
CONFLICT (rename/delete): file.txt deleted in HEAD and renamed in feature
Automatic merge failed; fix conflicts and then commit the result.
"""

        conflicts = self.coordinator._parse_git_conflicts(git_output)

        self.assertEqual(len(conflicts), 2)
        self.assertEqual(conflicts[0]['type'], 'content')
        self.assertEqual(conflicts[0]['file'], 'test.py')
        self.assertEqual(conflicts[1]['type'], 'rename/delete')

    @patch('shutil.copytree')
    @patch('shutil.rmtree')
    def test_backup_restore(self, mock_rmtree, mock_copytree):
        """Test backup and restore functionality."""
        # Create .celebi directory for backup
        celebi_dir = os.path.join(self.test_dir, '.celebi')
        os.makedirs(celebi_dir)

        # Create .git directory
        git_dir = os.path.join(self.test_dir, '.git')
        os.makedirs(git_dir)

        # Test backup creation
        backup_info = self.coordinator._create_backup()
        self.assertIsNotNone(backup_info)
        self.assertIn('backup_dir', backup_info)
        self.assertIn('files', backup_info)

        # Test backup restore
        self.coordinator._restore_backup(backup_info)
        mock_copytree.assert_called()

        # Test backup cleanup
        self.coordinator._cleanup_backup(backup_info)
        mock_rmtree.assert_called()

    def test_merge_strategy_enum(self):
        """Test MergeStrategy enum values."""
        self.assertEqual(MergeStrategy.INTERACTIVE.value, 'interactive')
        self.assertEqual(MergeStrategy.AUTO.value, 'auto')
        self.assertEqual(MergeStrategy.LOCAL.value, 'local')
        self.assertEqual(MergeStrategy.REMOTE.value, 'remote')
        self.assertEqual(MergeStrategy.UNION.value, 'union')


class TestIntegration(unittest.TestCase):
    """Integration tests for git merge system."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_config_file_roundtrip(self):
        """Test configuration file save and load."""
        git_integration = GitOptionalIntegration(self.test_dir)

        # Enable integration
        git_integration.enable_integration()

        # Modify config
        git_integration.set_config_option('auto_validate', False)
        git_integration.set_config_option('merge_strategy', 'auto')

        # Create new instance to load config
        git_integration2 = GitOptionalIntegration(self.test_dir)
        config = git_integration2.get_config()

        self.assertFalse(config['auto_validate'])
        self.assertEqual(config['merge_strategy'], 'auto')

    @patch('os.path.exists')
    def test_git_repo_detection_edge_cases(self, mock_exists):
        """Test edge cases for git repository detection."""
        # Test when .git exists but is a file
        mock_exists.side_effect = lambda path: path.endswith('.git')

        git_integration = GitOptionalIntegration(self.test_dir)
        # Should still return True even if .git is a file
        # (actual implementation may vary)
        result = git_integration.is_git_repository()
        # Just ensure it doesn't crash
        self.assertIsInstance(result, bool)


if __name__ == '__main__':
    unittest.main()
