"""Optional git integration system for Celebi.

This module provides feature detection, configuration, and graceful
degradation for Celebi's git integration features.
"""
import os
import json
import subprocess
from typing import Dict, Optional, Any, List
from logging import getLogger

logger = getLogger("ChernLogger")


class GitOptionalIntegration:
    """Manages optional git integration features."""

    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path or os.getcwd()
        self.config_path = os.path.join(self.project_path, '.celebi', 'git_config.json')
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load git integration configuration."""
        default_config = {
            'enabled': False,
            'hooks_installed': False,
            'auto_validate': True,
            'auto_regenerate': True,
            'prefer_local': True,
            'merge_strategy': 'interactive'
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                # Merge with defaults
                default_config.update(user_config)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Failed to load git config: %s", e)

        return default_config

    def _save_config(self):
        """Save git integration configuration."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            logger.error("Failed to save git config: %s", e)

    def is_git_repository(self) -> bool:
        """Check if current directory is a git repository."""
        git_dir = os.path.join(self.project_path, '.git')
        return os.path.exists(git_dir)

    def is_git_integration_enabled(self) -> bool:
        """Check if git integration is enabled for this project."""
        return self.config.get('enabled', False) and self.is_git_repository()

    def enable_integration(self) -> bool:
        """
        Enable git integration for this project.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_git_repository():
            logger.error("Cannot enable git integration: not a git repository")
            return False

        self.config['enabled'] = True
        self._save_config()

        logger.info("Git integration enabled for project")
        return True

    def disable_integration(self) -> bool:
        """
        Disable git integration for this project.

        Returns:
            True if successful, False otherwise
        """
        self.config['enabled'] = False
        self._save_config()

        # Remove hooks if installed
        if self.config.get('hooks_installed', False):
            self.uninstall_hooks()

        logger.info("Git integration disabled for project")
        return True

    def install_hooks(self) -> bool:
        """
        Install git hooks for Celebi integration.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_git_repository():
            logger.error("Cannot install hooks: not a git repository")
            return False

        hooks_dir = os.path.join(self.project_path, '.git', 'hooks')
        if not os.path.exists(hooks_dir):
            logger.error("Git hooks directory not found: %s", hooks_dir)
            return False

        # Create post-merge hook
        post_merge_hook = os.path.join(hooks_dir, 'post-merge')
        hook_content = """#!/bin/sh
# Celebi post-merge validation hook
# This hook validates Celebi project state after a git merge

# Only run if Celebi git integration is enabled
if [ -f ".celebi/git_config.json" ]; then
    python -c "
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from CelebiChrono.utils.git_merge_coordinator import GitMergeCoordinator
    coordinator = GitMergeCoordinator()
    result = coordinator.validate_post_merge()
    if not result['success']:
        print('Celebi post-merge validation found issues:')
        for issue in result.get('issues', []):
            print(f'  - {issue}')
        if result.get('repairs'):
            print('Automatic repairs performed:')
            for repair in result['repairs']:
                print(f'  - {repair}')
except Exception as e:
    print(f'Celebi post-merge hook error: {e}')
"
fi
"""

        try:
            with open(post_merge_hook, 'w', encoding='utf-8') as f:
                f.write(hook_content)

            # Make hook executable
            os.chmod(post_merge_hook, 0o755)

            self.config['hooks_installed'] = True
            self._save_config()

            logger.info("Git hooks installed successfully")
            return True

        except IOError as e:
            logger.error("Failed to install git hooks: %s", e)
            return False

    def uninstall_hooks(self) -> bool:
        """
        Uninstall Celebi git hooks.

        Returns:
            True if successful, False otherwise
        """
        hooks_dir = os.path.join(self.project_path, '.git', 'hooks')
        if not os.path.exists(hooks_dir):
            return True  # Nothing to uninstall

        # Remove post-merge hook
        post_merge_hook = os.path.join(hooks_dir, 'post-merge')
        if os.path.exists(post_merge_hook):
            try:
                # Check if it's our hook by reading first few lines
                with open(post_merge_hook, 'r', encoding='utf-8') as f:
                    content = f.read(100)
                if 'Celebi post-merge validation hook' in content:
                    os.remove(post_merge_hook)
                    logger.info("Removed Celebi post-merge hook")
            except IOError:
                pass  # Couldn't read or remove, but that's OK

        self.config['hooks_installed'] = False
        self._save_config()

        return True

    def get_git_info(self) -> Dict[str, Any]:
        """
        Get information about git repository status.

        Returns:
            Dictionary with git information
        """
        info = {
            'is_git_repo': self.is_git_repository(),
            'integration_enabled': self.is_git_integration_enabled(),
            'hooks_installed': self.config.get('hooks_installed', False),
            'current_branch': None,
            'has_uncommitted_changes': False,
            'remote_url': None,
            'error': None
        }

        if not info['is_git_repo']:
            return info

        try:
            # Get current branch
            cmd = ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
            process = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if not process.returncode:
                info['current_branch'] = process.stdout.strip()

            # Check for uncommitted changes
            cmd = ['git', 'status', '--porcelain']
            process = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            info['has_uncommitted_changes'] = bool(process.stdout.strip())

            # Get remote URL
            cmd = ['git', 'remote', 'get-url', 'origin']
            process = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if not process.returncode:
                info['remote_url'] = process.stdout.strip()

        except Exception as e:
            info['error'] = str(e)
            logger.error("Error getting git info: %s", e)

        return info

    def set_config_option(self, key: str, value: Any) -> bool:
        """
        Set a git integration configuration option.

        Args:
            key: Configuration key
            value: Configuration value

        Returns:
            True if successful, False otherwise
        """
        valid_keys = ['enabled', 'auto_validate', 'auto_regenerate',
                      'prefer_local', 'merge_strategy']

        if key not in valid_keys:
            logger.error("Invalid config key: %s", key)
            return False

        self.config[key] = value
        self._save_config()
        return True

    def get_config(self) -> Dict[str, Any]:
        """Get current git integration configuration."""
        return self.config.copy()

    def detect_potential_issues(self) -> List[Dict[str, Any]]:
        """
        Detect potential issues with git integration.

        Returns:
            List of detected issues
        """
        issues = []

        if not self.is_git_repository():
            issues.append({
                'level': 'error',
                'message': 'Not a git repository',
                'suggestion': 'Initialize git with "git init" or navigate to a git repository'
            })
            return issues

        # Check git version
        try:
            cmd = ['git', '--version']
            process = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if process.returncode:
                issues.append({
                    'level': 'error',
                    'message': 'Git not found or not executable',
                    'suggestion': 'Install git and ensure it is in PATH'
                })
        except Exception:
            issues.append({
                'level': 'error',
                'message': 'Git not found or not executable',
                'suggestion': 'Install git and ensure it is in PATH'
            })

        # Check for large files that might cause issues
        large_files = self._find_large_files()
        if large_files:
            issues.append({
                'level': 'warning',
                'message': f'Found {len(large_files)} large file(s) (>10MB)',
                'suggestion': 'Consider adding large files to .gitignore or using git LFS',
                'details': large_files
            })

        # Check for binary files in Celebi directories
        binary_files = self._find_binary_files_in_celebi()
        if binary_files:
            issues.append({
                'level': 'warning',
                'message': f'Found {len(binary_files)} binary file(s) in .celebi directory',
                'suggestion': 'Binary files may cause merge conflicts',
                'details': binary_files
            })

        return issues

    def _find_large_files(self, size_limit_mb: int = 10) -> List[Dict[str, Any]]:
        """Find large files in the repository."""
        large_files = []

        try:
            # Use find command to locate large files
            cmd = [
                'find',
                '.',
                '-type',
                'f',
                '-size',
                f'+{size_limit_mb}M',
                '-not',
                '-path',
                './.git/*',
                '-not',
                '-path',
                './.celebi/*',
            ]
            process = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if not process.returncode:
                for file_path in process.stdout.strip().split('\n'):
                    if file_path:
                        try:
                            size = os.path.getsize(os.path.join(self.project_path, file_path))
                            size_mb = size / (1024 * 1024)
                            large_files.append({
                                'path': file_path,
                                'size_mb': round(size_mb, 2)
                            })
                        except OSError:
                            pass

        except Exception:
            pass  # Silently fail

        return large_files

    def _find_binary_files_in_celebi(self) -> List[str]:
        """Find binary files in .celebi directory."""
        binary_files = []
        celebi_dir = os.path.join(self.project_path, '.celebi')

        if not os.path.exists(celebi_dir):
            return binary_files

        try:
            # Simple heuristic: check file extensions
            for root, _, files in os.walk(celebi_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Skip impressions directory (contains binary data)
                    if '.celebi/impressions' in file_path:
                        continue

                    # Check for common binary extensions
                    binary_extensions = ['.bin', '.dat', '.db', '.so', '.dll', '.exe',
                                         '.pyc', '.pyo', '.pyd', '.o', '.a']
                    if any(file.lower().endswith(ext) for ext in binary_extensions):
                        rel_path = os.path.relpath(file_path, self.project_path)
                        binary_files.append(rel_path)

        except Exception:
            pass  # Silently fail

        return binary_files

    def validate_git_workflow(self) -> Dict[str, Any]:
        """
        Validate that git workflow is compatible with Celebi.

        Returns:
            Dictionary with validation results
        """
        results = {
            'compatible': True,
            'issues': [],
            'warnings': [],
            'suggestions': []
        }

        if not self.is_git_repository():
            results['compatible'] = False
            results['issues'].append('Not a git repository')
            return results

        # Check for git flow or similar workflows
        try:
            cmd = ['git', 'config', '--get', 'gitflow.branch.master']
            process = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if not process.returncode:
                results['warnings'].append('Git flow detected')
                results['suggestions'].append(
                    'Celebi merge validation should work with git flow'
                )
        except Exception:
            pass

        # Check for merge strategy preferences
        try:
            cmd = ['git', 'config', '--get', 'pull.rebase']
            process = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if not process.returncode and process.stdout.strip() == 'true':
                results['warnings'].append('Git pull with rebase enabled')
                results['suggestions'].append(
                    'Consider using "git pull --no-rebase" for Celebi projects'
                )
        except Exception:
            pass

        # Check for custom merge drivers
        try:
            cmd = ['git', 'config', '--get', 'merge.celebi.driver']
            process = subprocess.run(
                cmd,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if not process.returncode:
                results['warnings'].append('Custom Celebi merge driver configured')
        except Exception:
            pass

        return results

    def get_recommended_settings(self) -> Dict[str, Any]:
        """Get recommended git settings for Celebi projects."""
        return {
            'git_config': {
                'merge.conflictStyle': 'diff3',
                'merge.verbosity': '2',
                'diff.algorithm': 'histogram'
            },
            '.gitignore_additions': [
                '# Celebi-specific',
                '.celebi/impressions/',
                '.celebi/impressions_store/',
                '.celebi/cache/',
                '*.pyc',
                '__pycache__/'
            ],
            'workflow_suggestions': [
                'Use feature branches for task development',
                'Merge with --no-ff to preserve merge history',
                'Run "celebi git-validate" after merges',
                'Enable auto-validation in git hooks'
            ]
        }
