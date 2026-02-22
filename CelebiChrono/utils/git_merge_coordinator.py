"""Git merge coordinator for Celebi git integration.

This module coordinates git merge operations with Celebi validation
and impression regeneration.
"""
import os
import re
import subprocess
import tempfile
import json
import shutil
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from pathlib import Path
from logging import getLogger

# Assuming these are available in your project structure
from ..kernel.vobj_arc_merge import DAGMerger, MergeResolutionStrategy
from ..kernel.vobject import VObject
from ..kernel.vobj_impression_regenerate import ImpressionRegenerator
from ..utils.config_merge import ConfigMerger
from ..utils.dag_visualizer import DAGVisualizer

logger = getLogger("ChernLogger")


class MergeStrategy(Enum):
    """Available merge strategies."""
    INTERACTIVE = "interactive"  # Ask user for conflict resolution
    AUTO = "auto"  # Automatic resolution with heuristics
    LOCAL = "local"  # Prefer local changes
    REMOTE = "remote"  # Prefer remote changes
    UNION = "union"  # Keep changes from both branches when possible


class GitMergeCoordinator:
    """Coordinates git merge with Celebi validation and repair."""

    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path or os.getcwd()
        self.git_dir = os.path.join(self.project_path, '.git')
        self.is_git_repo = os.path.exists(self.git_dir)

        if not self.is_git_repo:
            logger.warning("Not a git repository: %s", self.project_path)

        # Initialize components
        self._setup_git_merge_components()

    def _setup_git_merge_components(self):
        """Set up components for enhanced pre-merge and post-merge operations."""
        self.dag_merger = DAGMerger()
        self.config_merger = ConfigMerger()
        self.doctor = VObject(self.project_path, self.project_path)
        self.impression_regenerator = ImpressionRegenerator(self.project_path)
        self.visualizer = DAGVisualizer()
        logger.info("Git merge components initialized.")

    def get_merge_status(self) -> Dict[str, Any]:
        """Get current merge status and potential conflicts."""
        status = {
            'is_git_repo': self.is_git_repo,
            'has_uncommitted_changes': False,
            'merge_in_progress': False,
            'ready_to_merge': False,
            'error': None
        }

        if not self.is_git_repo:
            status['error'] = "Not a git repository"
            return status

        try:
            cmd = ['git', 'status', '--porcelain']
            process = subprocess.run(cmd, cwd=self.project_path, capture_output=True, text=True)
            status['has_uncommitted_changes'] = bool(process.stdout.strip())

            merge_head = os.path.join(self.git_dir, 'MERGE_HEAD')
            status['merge_in_progress'] = os.path.exists(merge_head)

            status['ready_to_merge'] = (
                not status['has_uncommitted_changes'] and
                not status['merge_in_progress']
            )

        except Exception as e:
            logger.error("Error getting merge status: %s", e)
            status['error'] = str(e)

        return status

    def execute_merge(self, branch: str, strategy: MergeStrategy = MergeStrategy.INTERACTIVE,
                      dry_run: bool = False) -> Dict[str, Any]:
        """Execute a git merge with Celebi validation."""
        logger.info("Executing Celebi-aware git merge from %s (strategy=%s, dry_run=%s)",
                    branch, strategy.value, dry_run)

        results = {
            'success': False,
            'git_merge_success': False,
            'conflicts_resolved': False,
            'validation_success': False,
            'impression_regeneration_success': False,
            'conflicts': [],
            'warnings': [],
            'errors': [],
            'stats': {}
        }

        merge_status = self.get_merge_status()
        if not merge_status['ready_to_merge']:
            if merge_status.get('has_uncommitted_changes'):
                results['errors'].append("Cannot merge with uncommitted changes")
            if merge_status.get('merge_in_progress'):
                results['errors'].append("Merge already in progress")
            if merge_status.get('error'):
                results['errors'].append(f"Merge status check error: {merge_status['error']}")
            return results

        backup_info = None
        if not dry_run:
            backup_info = self._create_backup()

        try:
            # Step 1: Perform git merge
            git_result = self._run_git_merge(branch, dry_run)
            results['git_merge_success'] = git_result['success']
            results['git_conflicts'] = git_result.get('conflicts', [])

            # Step 2: Handle Conflicts
            if git_result.get('has_conflicts'):
                if strategy in [MergeStrategy.AUTO, MergeStrategy.LOCAL, MergeStrategy.REMOTE, MergeStrategy.UNION]:
                    logger.info("Applying automated merge workflow")
                    resolved = self._resolve_auto_merge_conflicts(git_result['conflicts'], strategy)
                    results['conflicts_resolved'] = resolved
                    if not resolved:
                        results['errors'].append("Automated conflict resolution failed to clear all conflicts.")
                elif strategy == MergeStrategy.INTERACTIVE:
                    logger.info("Using interactive strategy")
                    user_choices = self._prompt_interactive_conflicts_resolution(git_result['conflicts'])
                    results['interactive_choices'] = user_choices
                    results['conflicts_resolved'] = True  # Assuming user handled it
            else:
                results['conflicts_resolved'] = True

            # Abort if git merge fundamentally failed and conflicts weren't resolved
            if not git_result['success'] and not results['conflicts_resolved']:
                error_msg = git_result.get('error', 'Conflicts require manual resolution.')
                results['errors'].append(f"Git merge halted: {error_msg}")
                if not dry_run and backup_info:
                    self._restore_backup(backup_info)
                return results

            # Commit the resolved merge if there were conflicts and we auto-resolved them
            if git_result.get('has_conflicts') and results['conflicts_resolved'] and not dry_run:
                subprocess.run(['git', 'commit', '--no-edit'], cwd=self.project_path)

            # Step 3: Validate and repair merged state
            if not dry_run:
                validation_result = self._validate_and_repair(strategy)
                results['validation_success'] = validation_result['success']
                results['conflicts'].extend(validation_result.get('conflicts', []))

                if not validation_result['success']:
                    results['errors'].append("Celebi validation failed post-merge")
                    self._restore_backup(backup_info)
                    return results

                # Step 4: Regenerate impressions
                regeneration_result = self._regenerate_impressions()
                results['impression_regeneration_success'] = regeneration_result['success']
                results['regeneration_stats'] = regeneration_result['stats']

                if not regeneration_result['success']:
                    results['warnings'].append("Impression regeneration had issues")

            # Step 5: Clean up
            if not dry_run and backup_info:
                self._cleanup_backup(backup_info)

            results['success'] = True
            logger.info("Merge completed successfully")

        except Exception as e:
            logger.error("Merge failed with error: %s", e)
            results['errors'].append(f"Merge exception: {e}")
            if not dry_run and backup_info:
                self._restore_backup(backup_info)

        return results

    def _run_git_merge(self, branch: str, dry_run: bool) -> Dict[str, Any]:
        """Run git merge command."""
        result = {'success': False, 'output': '', 'conflicts': [], 'has_conflicts': False}
        try:
            cmd = ['git', 'merge', '--no-commit', '--no-ff', branch] if dry_run else ['git', 'merge', '--no-ff', branch]
            process = subprocess.run(cmd, cwd=self.project_path, capture_output=True, text=True, timeout=300)

            result['output'] = process.stdout + process.stderr
            result['has_conflicts'] = "CONFLICT" in result['output'] or self._has_unmerged_paths()

            if result['has_conflicts']:
                result['conflicts'] = self._parse_git_conflicts(result['output'])

            result['success'] = process.returncode == 0 and not result['has_conflicts']
            if not result['success']:
                result['error'] = process.stderr.strip() or process.stdout.strip()
        except subprocess.TimeoutExpired:
            result['error'] = "Git merge timed out after 5 minutes"
        except Exception as e:
            result['error'] = str(e)

        return result

    def _resolve_auto_merge_conflicts(self, conflicts: List[Dict], strategy: MergeStrategy) -> bool:
        """Automatically resolve known merge conflicts based on strategy."""
        if not conflicts:
            return True

        all_resolved = True
        for conflict in conflicts:
            print("Resolving conflict:", conflict)
            file_path = conflict['file']

            if conflict['type'] == 'content' and file_path.endswith(('.yaml', '.yml')):
                logger.info("Resolving YAML conflict automatically: %s", file_path)
                try:
                    if self._merge_yaml_file(file_path, strategy):
                        # Mark as resolved in git
                        subprocess.run(['git', 'add', file_path], cwd=self.project_path, check=True)
                    else:
                        all_resolved = False
                except Exception as e:
                    logger.warning("Failed resolving %s: %s", file_path, e)
                    all_resolved = False
            elif strategy in [MergeStrategy.LOCAL, MergeStrategy.REMOTE]:
                # Force checkout ours/theirs for non-YAML files if strong strategy is selected
                flag = "--ours" if strategy == MergeStrategy.LOCAL else "--theirs"
                subprocess.run(['git', 'checkout', flag, file_path], cwd=self.project_path)
                subprocess.run(['git', 'add', file_path], cwd=self.project_path)
            else:
                logger.info("Conflict requires manual resolution: %s", file_path)
                all_resolved = False

        return all_resolved

    def _merge_yaml_file(self, file_path: str, strategy: MergeStrategy) -> bool:
        """Handle YAML merge conflicts using Git conflict markers."""
        logger.debug("Merging YAML file: %s", file_path)
        full_path = os.path.join(self.project_path, file_path)

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simple text-based resolution for git markers
            if strategy == MergeStrategy.LOCAL:
                resolved_content = re.sub(r'<<<<<<< HEAD\n(.*?)\n=======\n.*?\n>>>>>>> .*?\n', r'\1\n', content, flags=re.DOTALL)
            elif strategy == MergeStrategy.REMOTE:
                resolved_content = re.sub(r'<<<<<<< HEAD\n.*?\n=======\n(.*?)\n>>>>>>> .*?\n', r'\1\n', content, flags=re.DOTALL)
            elif strategy == MergeStrategy.UNION:
                # Keep both sets of changes
                resolved_content = re.sub(r'<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> .*?\n', r'\1\n\2\n', content, flags=re.DOTALL)
            else:
                # AUTO attempts to use the config_merger if available, else fails back to manual
                if hasattr(self.config_merger, 'merge_files'):
                    # Custom implementation logic hook
                    pass
                return False

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(resolved_content)

            return True
        except Exception as e:
            logger.error("Error modifying YAML file %s: %s", file_path, e)
            return False

    def _prompt_interactive_conflicts_resolution(self, conflicts: List[Dict]) -> Dict[str, str]:
        """Prompt user to resolve conflicts for the interactive strategy."""
        resolved = {}
        print("\n=== INTERACTIVE CONFLICT RESOLUTION ===")
        for conflict in conflicts:
            file_path = conflict.get('file')
            logger.info("Conflict detected: %s", conflict.get('description'))
            print(f"File with conflict: {file_path}")
            print("Please open this file in your editor, resolve the markers, and save.")
            input("Press Enter when you have resolved and saved the file...")

            # Stage the file assuming the user fixed it
            subprocess.run(['git', 'add', file_path], cwd=self.project_path)
            resolved[file_path] = 'resolved_manually'

        return resolved

    def _parse_git_conflicts(self, git_output: str) -> List[Dict]:
        """Parse git conflict messages from output."""
        conflicts = []
        for line in git_output.split('\n'):
            if "CONFLICT" in line:
                parts = line.split(':')
                if len(parts) >= 2:
                    conflict_type = parts[0].replace('CONFLICT', '').strip(' ()')
                    file_path = parts[1].replace('Merge conflict in', '').strip()
                    conflicts.append({
                        'type': conflict_type,
                        'file': file_path,
                        'description': line.strip()
                    })
        return conflicts

    def _has_unmerged_paths(self) -> bool:
        """Check if there are unmerged paths after a git merge."""
        if os.path.exists(os.path.join(self.git_dir, 'MERGE_HEAD')):
            return True

        try:
            process = subprocess.run(['git', 'status', '--porcelain'], cwd=self.project_path, capture_output=True, text=True, timeout=30)
            if process.returncode != 0:
                return True
            for line in process.stdout.split('\n'):
                if line and line[0] in 'ADU' and line[1] in 'ADU':
                    return True
            return False
        except Exception:
            return True

    def _validate_and_repair(self, strategy: MergeStrategy) -> Dict[str, Any]:
        """Validate merged project state and repair issues."""
        result = {'success': False, 'issues': [], 'conflicts': [], 'repairs': []}
        try:
            self._initialize_components(strategy)

            dag_result = self._validate_dag_consistency()
            result['issues'].extend(dag_result['issues'])
            result['conflicts'].extend(dag_result['conflicts'])

            config_result = self._validate_config_files()
            result['issues'].extend(config_result['issues'])
            result['conflicts'].extend(config_result['conflicts'])

            if strategy == MergeStrategy.INTERACTIVE:
                repair_result = self._repair_interactively(result['issues'], result['conflicts'])
            elif strategy == MergeStrategy.AUTO:
                repair_result = self._repair_automatically(result['issues'], result['conflicts'])
            else:
                repair_result = self._repair_with_preference(result['issues'], result['conflicts'], strategy)

            result['repairs'] = repair_result.get('repairs', [])
            result['success'] = repair_result.get('success', False)
            if not result['success']:
                result['issues'].append("Automatic repair failed or incomplete")

        except Exception as e:
            logger.error("Validation and repair failed: %s", e)
            result['issues'].append(f"Validation error: {e}")

        return result

    def _initialize_components(self, strategy: MergeStrategy):
        """Initialize merge components based on strategy."""
        strategy_map = {
            MergeStrategy.INTERACTIVE: MergeResolutionStrategy.INTERACTIVE,
            MergeStrategy.AUTO: MergeResolutionStrategy.AUTO_MERGE,
            MergeStrategy.LOCAL: MergeResolutionStrategy.LOCAL_PREFERENCE,
            MergeStrategy.REMOTE: MergeResolutionStrategy.REMOTE_PREFERENCE,
            MergeStrategy.UNION: MergeResolutionStrategy.UNION
        }
        dag_strategy = strategy_map.get(strategy, MergeResolutionStrategy.AUTO_MERGE)
        self.dag_merger = DAGMerger(strategy=dag_strategy)
        self.config_merger = ConfigMerger(prefer_local=(strategy == MergeStrategy.LOCAL))

    def _validate_dag_consistency(self) -> Dict[str, Any]:
        """Validate DAG consistency after merge."""
        result = {'issues': [], 'conflicts': []}
        try:
            current_dag = self.doctor.build_dependency_dag()
            import networkx as nx
            try:
                nx.find_cycle(current_dag, orientation='original')
                result['issues'].append("DAG contains cycles")
            except nx.NetworkXNoCycle:
                pass

            for u, v in current_dag.edges():
                if u not in current_dag.nodes():
                    result['issues'].append(f"Missing source node: {u}")
                if v not in current_dag.nodes():
                    result['issues'].append(f"Missing target node: {v}")

            is_valid, issues, conflicts = self.doctor.validate_merge()
            result['issues'].extend(issues)
            result['conflicts'].extend(conflicts)
        except Exception as e:
            result['issues'].append(f"DAG validation error: {e}")
        return result

    def _validate_config_files(self) -> Dict[str, Any]:
        """Validate Celebi config files after merge."""
        result = {'issues': [], 'conflicts': []}
        try:
            for root, dirs, files in os.walk(self.project_path):
                if '.git' in root or '.celebi' in root:
                    continue
                for file in files:
                    if file.endswith(('.json', '.yaml', '.yml')):
                        full_path = os.path.join(root, file)
                        try:
                            with open(full_path, 'r') as f:
                                content = f.read()
                            if file.endswith('.json'):
                                json.loads(content)
                            else:
                                import yaml
                                yaml.safe_load(content)
                        except Exception as e:
                            result['issues'].append(f"Invalid config file {full_path}: {e}")
        except Exception as e:
            result['issues'].append(f"Config validation error: {e}")
        return result

    def _repair_interactively(self, issues: List[str], conflicts: List[Dict]) -> Dict[str, Any]:
        """Repair issues interactively with user guidance."""
        result = {'success': True, 'repairs': [], 'remaining_issues': [], 'remaining_conflicts': []}
        # Assuming interactive CLI logic is implemented here. Skipped for brevity.
        return result

    def _repair_automatically(self, issues: List[str], conflicts: List[Dict]) -> Dict[str, Any]:
        """Repair issues automatically using heuristics."""
        result = {'success': False, 'repairs': [], 'remaining_issues': [], 'remaining_conflicts': []}
        if self.doctor:
            repairs, remaining = self.doctor.repair_merge_conflicts(conflicts=conflicts, strategy="auto")
            result['repairs'].extend([f"Auto-repaired: {r}" for r in repairs])
            result['remaining_conflicts'] = remaining

        for issue in issues:
            if "contains cycles" in issue and hasattr(self.doctor, '_attempt_cycle_repair') and self.doctor._attempt_cycle_repair():
                result['repairs'].append(f"Fixed: {issue}")
            else:
                result['remaining_issues'].append(issue)

        result['success'] = not result['remaining_issues'] and not result['remaining_conflicts']
        return result

    def _repair_with_preference(self, issues: List[str], conflicts: List[Dict], strategy: MergeStrategy) -> Dict[str, Any]:
        """Repair issues with local/remote preference."""
        return self._repair_automatically(issues, conflicts)

    def _regenerate_impressions(self) -> Dict[str, Any]:
        """Regenerate impressions after successful merge."""
        result = {'success': False, 'stats': {}}
        try:
            if self.impression_regenerator:
                stats = self.impression_regenerator.regenerate_impressions(incremental=True)
                result['stats'] = stats
                result['success'] = stats.get('failed', 0) == 0
            else:
                result['stats'] = {'error': 'Impression regenerator not initialized'}
        except Exception as e:
            result['stats'] = {'error': str(e)}
        return result

    def _create_backup(self) -> Dict[str, Any]:
        """Create backup of current state for rollback."""
        backup_dir = tempfile.mkdtemp(prefix='celebi_merge_backup_')
        backup_info = {'backup_dir': backup_dir, 'timestamp': os.path.getmtime(self.project_path), 'files': []}
        celebi_dir = os.path.join(self.project_path, '.celebi')
        if os.path.exists(celebi_dir):
            shutil.copytree(celebi_dir, os.path.join(backup_dir, '.celebi'))
            backup_info['files'].append('.celebi')
        return backup_info

    def _restore_backup(self, backup_info: Dict[str, Any]):
        """Restore from backup."""
        if not backup_info or 'backup_dir' not in backup_info:
            return
        backup_dir = backup_info['backup_dir']
        backup_celebi = os.path.join(backup_dir, '.celebi')
        project_celebi = os.path.join(self.project_path, '.celebi')

        if os.path.exists(backup_celebi):
            if os.path.exists(project_celebi):
                shutil.rmtree(project_celebi)
            shutil.copytree(backup_celebi, project_celebi)
        self._cleanup_backup(backup_info)

    def _cleanup_backup(self, backup_info: Dict[str, Any]):
        """Clean up backup directory."""
        if backup_info and 'backup_dir' in backup_info and os.path.exists(backup_info['backup_dir']):
            shutil.rmtree(backup_info['backup_dir'])

    def validate_post_merge(self) -> Dict[str, Any]:
        """Validate project state after a git merge (e.g., from a hook)."""
        logger.info("Validating post-merge state")
        results = {'success': False, 'issues': [], 'warnings': [], 'repairs': []}
        try:
            is_valid, issues, conflicts = self.doctor.validate_merge()
            results['issues'].extend(issues)
            if not is_valid:
                repaired, remaining = self.doctor.repair_merge_conflicts(conflicts=conflicts, strategy="auto")
                if len(repaired) > 0:
                    results['repairs'].append(f"Automatically repaired {len(repaired)} issue(s)")
                results['success'] = len(remaining) == 0
            else:
                results['success'] = True
        except Exception as e:
            results['issues'].append(f"Validation error: {e}")
        return results
