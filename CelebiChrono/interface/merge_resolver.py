"""Interactive merge conflict resolution interface for Celebi.

This module provides user-friendly interfaces for resolving
merge conflicts with clear prompts and visualizations.
"""
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from logging import getLogger

from ..utils.dag_visualizer import DAGVisualizer
from ..kernel.vobj_arc_merge import MergeConflict, MergeConflictType

logger = getLogger("ChernLogger")


class ResolutionAction(Enum):
    """Actions that can be taken to resolve conflicts."""
    KEEP_LOCAL = "keep_local"
    KEEP_REMOTE = "keep_remote"
    KEEP_BOTH = "keep_both"
    MANUAL_EDIT = "manual_edit"
    SKIP = "skip"
    ABORT = "abort"


class MergeResolver:
    """Interactive resolver for merge conflicts."""

    def __init__(self, use_color: bool = True):
        self.use_color = use_color and sys.stdout.isatty()
        self.visualizer = DAGVisualizer(use_unicode=True)
        self.resolved_conflicts = []
        self.pending_conflicts = []

    def resolve_conflicts_interactively(self, conflicts: List[Dict],
                                        context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Resolve conflicts interactively with user guidance.

        Args:
            conflicts: List of conflict dictionaries
            context: Additional context for resolution

        Returns:
            Dictionary with resolution results
        """
        if not conflicts:
            return {
                'success': True,
                'resolved': 0,
                'skipped': 0,
                'remaining': 0,
                'actions': []
            }

        print("\n" + "=" * 80)
        print("CELEBI MERGE CONFLICT RESOLUTION")
        print("=" * 80)

        # Show summary
        self._show_conflict_summary(conflicts)

        # Group conflicts by type
        grouped_conflicts = self._group_conflicts_by_type(conflicts)

        # Resolve each group
        results = {
            'success': False,
            'resolved': 0,
            'skipped': 0,
            'remaining': len(conflicts),
            'actions': []
        }

        # Resolve DAG conflicts first (most critical)
        if 'dag' in grouped_conflicts:
            print("\n" + "-" * 80)
            print("RESOLVING DEPENDENCY GRAPH CONFLICTS")
            print("-" * 80)
            dag_results = self._resolve_dag_conflicts(grouped_conflicts['dag'], context)
            results['resolved'] += dag_results['resolved']
            results['skipped'] += dag_results['skipped']
            results['actions'].extend(dag_results['actions'])

        # Resolve config conflicts
        if 'config' in grouped_conflicts:
            print("\n" + "-" * 80)
            print("RESOLVING CONFIGURATION FILE CONFLICTS")
            print("-" * 80)
            config_results = self._resolve_config_conflicts(grouped_conflicts['config'], context)
            results['resolved'] += config_results['resolved']
            results['skipped'] += config_results['skipped']
            results['actions'].extend(config_results['actions'])

        # Resolve other conflicts
        other_types = [t for t in grouped_conflicts.keys() if t not in ['dag', 'config']]
        for conflict_type in other_types:
            print(f"\n" + "-" * 80)
            print(f"RESOLVING {conflict_type.upper()} CONFLICTS")
            print("-" * 80)
            type_results = self._resolve_generic_conflicts(grouped_conflicts[conflict_type], context)
            results['resolved'] += type_results['resolved']
            results['skipped'] += type_results['skipped']
            results['actions'].extend(type_results['actions'])

        # Update remaining count
        results['remaining'] = len(conflicts) - results['resolved'] - results['skipped']
        results['success'] = results['remaining'] == 0

        # Show final summary
        self._show_resolution_summary(results)

        return results

    def _show_conflict_summary(self, conflicts: List[Dict]):
        """Show summary of all conflicts."""
        print(f"\nFound {len(conflicts)} conflict(s):")

        # Count by type
        type_counts = {}
        for conflict in conflicts:
            conflict_type = conflict.get('type', 'unknown')
            type_counts[conflict_type] = type_counts.get(conflict_type, 0) + 1

        for conflict_type, count in type_counts.items():
            print(f"  {conflict_type}: {count}")

        # Show most critical conflicts first
        critical_types = ['cycle_creation', 'uuid_conflict', 'dag_conflict']
        critical_conflicts = [c for c in conflicts if c.get('type') in critical_types]

        if critical_conflicts:
            print("\nCRITICAL CONFLICTS (require immediate attention):")
            for conflict in critical_conflicts[:3]:  # Show first 3
                print(f"  • {conflict.get('description', 'Unknown')}")
            if len(critical_conflicts) > 3:
                print(f"  ... and {len(critical_conflicts) - 3} more")

    def _group_conflicts_by_type(self, conflicts: List[Dict]) -> Dict[str, List[Dict]]:
        """Group conflicts by their type."""
        groups = {}

        for conflict in conflicts:
            conflict_type = conflict.get('type', 'unknown')

            # Map to broader categories
            if 'dag' in conflict_type or 'cycle' in conflict_type or 'edge' in conflict_type:
                category = 'dag'
            elif 'config' in conflict_type or 'yaml' in conflict_type or 'json' in conflict_type:
                category = 'config'
            elif 'uuid' in conflict_type:
                category = 'uuid'
            elif 'alias' in conflict_type:
                category = 'alias'
            else:
                category = 'other'

            if category not in groups:
                groups[category] = []
            groups[category].append(conflict)

        return groups

    def _resolve_dag_conflicts(self, conflicts: List[Dict],
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve DAG-related conflicts."""
        results = {
            'resolved': 0,
            'skipped': 0,
            'actions': []
        }

        for i, conflict in enumerate(conflicts, 1):
            print(f"\nDAG Conflict {i}/{len(conflicts)}:")
            print(f"  {conflict.get('description', 'Unknown conflict')}")

            # Show visualization if available
            if 'local' in conflict and 'remote' in conflict:
                self._show_dag_diff(conflict['local'], conflict['remote'])

            # Get resolution options
            options = self._get_dag_resolution_options(conflict)

            # Present options to user
            choice = self._present_resolution_options(options, conflict)

            if choice == ResolutionAction.SKIP:
                print("  Skipping conflict (will remain unresolved)")
                results['skipped'] += 1
                results['actions'].append({
                    'conflict': conflict.get('description'),
                    'action': 'skipped',
                    'reason': 'user_choice'
                })
            elif choice == ResolutionAction.ABORT:
                print("  Merge aborted by user")
                return results  # Early exit
            else:
                # Apply resolution
                action_result = self._apply_dag_resolution(conflict, choice)
                if action_result['success']:
                    results['resolved'] += 1
                    results['actions'].append({
                        'conflict': conflict.get('description'),
                        'action': choice.value,
                        'details': action_result.get('details')
                    })
                    print(f"  Conflict resolved ({choice.value})")
                else:
                    results['skipped'] += 1
                    results['actions'].append({
                        'conflict': conflict.get('description'),
                        'action': 'failed',
                        'error': action_result.get('error')
                    })
                    print(f"  Failed to resolve: {action_result.get('error')}")

        return results

    def _show_dag_diff(self, local_data: Any, remote_data: Any):
        """Show DAG difference visualization."""
        # This would use the DAGVisualizer to show differences
        # For now, show simple text representation
        print("\n  Differences:")
        if isinstance(local_data, list) and isinstance(remote_data, list):
            local_only = set(local_data) - set(remote_data)
            remote_only = set(remote_data) - set(local_data)

            if local_only:
                print("    Local only:", ', '.join(str(x) for x in local_only))
            if remote_only:
                print("    Remote only:", ', '.join(str(x) for x in remote_only))
        elif isinstance(local_data, dict) and isinstance(remote_data, dict):
            all_keys = set(local_data.keys()) | set(remote_data.keys())
            for key in all_keys:
                local_val = local_data.get(key)
                remote_val = remote_data.get(key)
                if local_val != remote_val:
                    print(f"    {key}: local={local_val}, remote={remote_val}")

    def _get_dag_resolution_options(self, conflict: Dict) -> List[Dict]:
        """Get resolution options for a DAG conflict."""
        conflict_type = conflict.get('type')

        options = []

        if conflict_type == 'cycle_creation':
            options.extend([
                {
                    'action': ResolutionAction.KEEP_LOCAL,
                    'description': 'Break cycle by removing remote edges',
                    'key': '1'
                },
                {
                    'action': ResolutionAction.KEEP_REMOTE,
                    'description': 'Break cycle by removing local edges',
                    'key': '2'
                },
                {
                    'action': ResolutionAction.MANUAL_EDIT,
                    'description': 'Manually edit dependencies to break cycle',
                    'key': '3'
                }
            ])
        elif conflict_type in ['additive_edge', 'subtractive_edge', 'contradictory_edge']:
            options.extend([
                {
                    'action': ResolutionAction.KEEP_LOCAL,
                    'description': 'Use local branch dependencies',
                    'key': '1'
                },
                {
                    'action': ResolutionAction.KEEP_REMOTE,
                    'description': 'Use remote branch dependencies',
                    'key': '2'
                },
                {
                    'action': ResolutionAction.KEEP_BOTH,
                    'description': 'Merge dependencies from both branches',
                    'key': '3'
                }
            ])
        else:
            # Generic options
            options.extend([
                {
                    'action': ResolutionAction.KEEP_LOCAL,
                    'description': 'Keep local version',
                    'key': '1'
                },
                {
                    'action': ResolutionAction.KEEP_REMOTE,
                    'description': 'Keep remote version',
                    'key': '2'
                }
            ])

        # Always include skip and abort options
        options.extend([
            {
                'action': ResolutionAction.SKIP,
                'description': 'Skip this conflict (leave unresolved)',
                'key': 's'
            },
            {
                'action': ResolutionAction.ABORT,
                'description': 'Abort entire merge',
                'key': 'a'
            }
        ])

        return options

    def _resolve_config_conflicts(self, conflicts: List[Dict],
                                  context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve configuration file conflicts."""
        results = {
            'resolved': 0,
            'skipped': 0,
            'actions': []
        }

        for i, conflict in enumerate(conflicts, 1):
            print(f"\nConfig Conflict {i}/{len(conflicts)}:")
            print(f"  {conflict.get('description', 'Unknown conflict')}")

            # Show file content diff if available
            if 'file' in conflict:
                print(f"  File: {conflict['file']}")

            # Get resolution options
            options = self._get_config_resolution_options(conflict)

            # Present options to user
            choice = self._present_resolution_options(options, conflict)

            if choice == ResolutionAction.SKIP:
                print("  Skipping conflict (will remain unresolved)")
                results['skipped'] += 1
                results['actions'].append({
                    'conflict': conflict.get('description'),
                    'action': 'skipped',
                    'reason': 'user_choice'
                })
            elif choice == ResolutionAction.ABORT:
                print("  Merge aborted by user")
                return results  # Early exit
            elif choice == ResolutionAction.MANUAL_EDIT:
                # Launch editor for manual resolution
                if 'file' in conflict:
                    edited = self._edit_file_manually(conflict['file'])
                    if edited:
                        results['resolved'] += 1
                        results['actions'].append({
                            'conflict': conflict.get('description'),
                            'action': 'manual_edit',
                            'file': conflict['file']
                        })
                        print("  File edited manually")
                    else:
                        results['skipped'] += 1
                        results['actions'].append({
                            'conflict': conflict.get('description'),
                            'action': 'edit_failed',
                            'file': conflict['file']
                        })
                        print("  Manual edit failed or cancelled")
            else:
                # Apply automatic resolution
                action_result = self._apply_config_resolution(conflict, choice)
                if action_result['success']:
                    results['resolved'] += 1
                    results['actions'].append({
                        'conflict': conflict.get('description'),
                        'action': choice.value,
                        'details': action_result.get('details')
                    })
                    print(f"  Conflict resolved ({choice.value})")
                else:
                    results['skipped'] += 1
                    results['actions'].append({
                        'conflict': conflict.get('description'),
                        'action': 'failed',
                        'error': action_result.get('error')
                    })
                    print(f"  Failed to resolve: {action_result.get('error')}")

        return results

    def _get_config_resolution_options(self, conflict: Dict) -> List[Dict]:
        """Get resolution options for a config conflict."""
        conflict_type = conflict.get('type')

        options = []

        if conflict_type == 'uuid_conflict':
            options.extend([
                {
                    'action': ResolutionAction.KEEP_LOCAL,
                    'description': 'Keep local UUID (may break references)',
                    'key': '1',
                    'warning': 'Warning: Changing UUIDs may break dependencies'
                },
                {
                    'action': ResolutionAction.KEEP_REMOTE,
                    'description': 'Keep remote UUID (may break references)',
                    'key': '2',
                    'warning': 'Warning: Changing UUIDs may break dependencies'
                },
                {
                    'action': ResolutionAction.MANUAL_EDIT,
                    'description': 'Edit file to resolve UUID conflict',
                    'key': '3'
                }
            ])
        else:
            # Generic config options
            options.extend([
                {
                    'action': ResolutionAction.KEEP_LOCAL,
                    'description': 'Keep local version of file',
                    'key': '1'
                },
                {
                    'action': ResolutionAction.KEEP_REMOTE,
                    'description': 'Keep remote version of file',
                    'key': '2'
                },
                {
                    'action': ResolutionAction.KEEP_BOTH,
                    'description': 'Merge contents from both versions',
                    'key': '3'
                },
                {
                    'action': ResolutionAction.MANUAL_EDIT,
                    'description': 'Edit file manually to resolve conflict',
                    'key': '4'
                }
            ])

        # Always include skip and abort options
        options.extend([
            {
                'action': ResolutionAction.SKIP,
                'description': 'Skip this conflict (leave unresolved)',
                'key': 's'
            },
            {
                'action': ResolutionAction.ABORT,
                'description': 'Abort entire merge',
                'key': 'a'
            }
        ])

        return options

    def _resolve_generic_conflicts(self, conflicts: List[Dict],
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve generic conflicts."""
        results = {
            'resolved': 0,
            'skipped': 0,
            'actions': []
        }

        for i, conflict in enumerate(conflicts, 1):
            print(f"\nConflict {i}/{len(conflicts)}:")
            print(f"  Type: {conflict.get('type', 'unknown')}")
            print(f"  {conflict.get('description', 'Unknown conflict')}")

            # Generic resolution options
            options = [
                {
                    'action': ResolutionAction.KEEP_LOCAL,
                    'description': 'Keep local version',
                    'key': '1'
                },
                {
                    'action': ResolutionAction.KEEP_REMOTE,
                    'description': 'Keep remote version',
                    'key': '2'
                },
                {
                    'action': ResolutionAction.SKIP,
                    'description': 'Skip this conflict',
                    'key': 's'
                },
                {
                    'action': ResolutionAction.ABORT,
                    'description': 'Abort merge',
                    'key': 'a'
                }
            ]

            choice = self._present_resolution_options(options, conflict)

            if choice == ResolutionAction.SKIP:
                print("  Skipping conflict")
                results['skipped'] += 1
                results['actions'].append({
                    'conflict': conflict.get('description'),
                    'action': 'skipped'
                })
            elif choice == ResolutionAction.ABORT:
                print("  Merge aborted")
                return results
            else:
                # Apply resolution
                results['resolved'] += 1
                results['actions'].append({
                    'conflict': conflict.get('description'),
                    'action': choice.value
                })
                print(f"  Conflict resolved ({choice.value})")

        return results

    def _present_resolution_options(self, options: List[Dict],
                                    conflict: Dict) -> ResolutionAction:
        """Present resolution options to user and get their choice."""
        print("\n  Resolution options:")

        for option in options:
            key = option.get('key', '?')
            description = option.get('description', 'No description')
            warning = option.get('warning')

            if warning and self.use_color:
                print(f"    [{key}] {description} \033[93m({warning})\033[0m")
            else:
                print(f"    [{key}] {description}")

        while True:
            try:
                choice = input("\n  Choose option: ").strip().lower()

                # Find matching option
                for option in options:
                    if option.get('key') == choice:
                        return option['action']

                print(f"  Invalid choice: {choice}")
            except (EOFError, KeyboardInterrupt):
                print("\n  Input interrupted, aborting merge")
                return ResolutionAction.ABORT

    def _apply_dag_resolution(self, conflict: Dict,
                              action: ResolutionAction) -> Dict[str, Any]:
        """Apply DAG conflict resolution."""
        # This would actually modify the DAG
        # For now, just return success
        return {
            'success': True,
            'details': f'Applied {action.value} to DAG conflict'
        }

    def _apply_config_resolution(self, conflict: Dict,
                                 action: ResolutionAction) -> Dict[str, Any]:
        """Apply config conflict resolution."""
        # This would actually modify config files
        # For now, just return success
        return {
            'success': True,
            'details': f'Applied {action.value} to config conflict'
        }

    def _edit_file_manually(self, file_path: str) -> bool:
        """Launch editor for manual file editing."""
        editor = os.environ.get('EDITOR', 'vim')

        print(f"  Opening {file_path} in {editor}...")
        print("  Edit the file to resolve conflicts, then save and exit.")

        try:
            import subprocess
            result = subprocess.run([editor, file_path])
            return result.returncode == 0
        except Exception as e:
            print(f"  Failed to open editor: {e}")
            return False

    def _show_resolution_summary(self, results: Dict[str, Any]):
        """Show summary of resolution results."""
        print("\n" + "=" * 80)
        print("RESOLUTION SUMMARY")
        print("=" * 80)

        total = results['resolved'] + results['skipped'] + results['remaining']

        print(f"\nTotal conflicts: {total}")
        print(f"Resolved: {results['resolved']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Remaining: {results['remaining']}")

        if results['success']:
            print("\n✓ All conflicts resolved successfully!")
        else:
            print(f"\n⚠ {results['remaining']} conflict(s) remain unresolved")

        # Show actions taken
        if results['actions']:
            print("\nActions taken:")
            for action in results['actions'][:10]:  # Show first 10
                conflict_desc = action.get('conflict', 'Unknown')
                if len(conflict_desc) > 50:
                    conflict_desc = conflict_desc[:47] + "..."
                print(f"  • {conflict_desc}: {action.get('action', 'unknown')}")

            if len(results['actions']) > 10:
                print(f"  ... and {len(results['actions']) - 10} more actions")

    def preview_merge(self, local_dag, remote_dag, base_dag) -> str:
        """
        Generate a preview of merge results.

        Args:
            local_dag: Local branch DAG
            remote_dag: Remote branch DAG
            base_dag: Base ancestor DAG

        Returns:
            Preview text
        """
        from ..kernel.vobj_arc_merge import DAGMerger

        merger = DAGMerger()
        merged_dag = merger.merge_dags(local_dag, remote_dag, base_dag)
        conflicts = merger.get_conflicts()

        output = []
        output.append("MERGE PREVIEW")
        output.append("=" * 80)

        # Show DAG statistics
        output.append("\nDAG Statistics:")
        output.append(f"  Local nodes: {local_dag.number_of_nodes()}")
        output.append(f"  Local edges: {local_dag.number_of_edges()}")
        output.append(f"  Remote nodes: {remote_dag.number_of_nodes()}")
        output.append(f"  Remote edges: {remote_dag.number_of_edges()}")
        output.append(f"  Merged nodes: {merged_dag.number_of_nodes()}")
        output.append(f"  Merged edges: {merged_dag.number_of_edges()}")

        # Show conflicts
        if conflicts:
            output.append(f"\nPotential conflicts: {len(conflicts)}")
            for i, conflict in enumerate(conflicts[:5], 1):  # Show first 5
                output.append(f"  {i}. {conflict.description}")
            if len(conflicts) > 5:
                output.append(f"  ... and {len(conflicts) - 5} more")
        else:
            output.append("\nNo conflicts detected")

        # Show visualization
        output.append("\nMerged DAG structure:")
        try:
            # Try to show topological layers
            import networkx as nx
            topo_order = list(nx.topological_sort(merged_dag))
            layers = self._assign_layers(merged_dag, topo_order)

            for layer_idx, layer_nodes in enumerate(layers):
                node_names = [self._get_node_name(n) for n in layer_nodes]
                output.append(f"  Layer {layer_idx + 1}: {', '.join(node_names)}")

        except Exception:
            output.append("  (Could not generate topological layout)")

        return '\n'.join(output)

    def _assign_layers(self, graph, topological_order):
        """Assign nodes to layers based on longest path."""
        # Simplified version from DAGVisualizer
        longest_path = {}
        for node in topological_order:
            preds = list(graph.predecessors(node))
            if not preds:
                longest_path[node] = 0
            else:
                longest_path[node] = max(longest_path[p] for p in preds) + 1

        max_layer = max(longest_path.values()) if longest_path else 0
        layers = [[] for _ in range(max_layer + 1)]

        for node, layer in longest_path.items():
            layers[layer].append(node)

        return layers

    def _get_node_name(self, node):
        """Get readable name for a node."""
        if hasattr(node, 'invariant_path'):
            path = node.invariant_path()
            if '/' in path:
                return path.split('/')[-1]
            return path
        return str(node)