"""Unit tests for merge conflict resolution interface."""
import unittest
from unittest.mock import Mock, patch

from CelebiChrono.interface.merge_resolver import MergeResolver, ResolutionAction


class TestMergeResolver(unittest.TestCase):
    """Test cases for MergeResolver class."""

    def setUp(self):
        """Set up test fixtures."""
        self.resolver = MergeResolver(use_color=False)

    def test_group_conflicts_by_type(self):
        """Test grouping conflicts by type."""
        conflicts = [
            {'type': 'dag_conflict', 'description': 'DAG conflict 1'},
            {'type': 'dag_cycle', 'description': 'Cycle conflict'},
            {'type': 'config_conflict', 'description': 'Config conflict'},
            {'type': 'uuid_conflict', 'description': 'UUID conflict'},
            {'type': 'alias_conflict', 'description': 'Alias conflict'},
            {'type': 'other_conflict', 'description': 'Other conflict'}
        ]

        grouped = self.resolver._group_conflicts_by_type(conflicts)

        # Should have categories: dag, config, uuid, alias, other
        self.assertIn('dag', grouped)
        self.assertIn('config', grouped)
        self.assertIn('uuid', grouped)
        self.assertIn('alias', grouped)
        self.assertIn('other', grouped)

        # Check grouping
        self.assertEqual(len(grouped['dag']), 2)  # dag_conflict + dag_cycle
        self.assertEqual(len(grouped['config']), 1)
        self.assertEqual(len(grouped['uuid']), 1)
        self.assertEqual(len(grouped['alias']), 1)
        self.assertEqual(len(grouped['other']), 1)

    def test_get_dag_resolution_options(self):
        """Test getting DAG conflict resolution options."""
        # Test cycle creation conflict
        cycle_conflict = {'type': 'cycle_creation', 'description': 'Cycle detected'}
        options = self.resolver._get_dag_resolution_options(cycle_conflict)

        self.assertGreater(len(options), 0)
        # Should include cycle-specific options
        option_actions = [opt['action'] for opt in options]
        self.assertIn(ResolutionAction.KEEP_LOCAL, option_actions)
        self.assertIn(ResolutionAction.KEEP_REMOTE, option_actions)
        self.assertIn(ResolutionAction.MANUAL_EDIT, option_actions)
        self.assertIn(ResolutionAction.SKIP, option_actions)
        self.assertIn(ResolutionAction.ABORT, option_actions)

        # Test edge conflict
        edge_conflict = {'type': 'additive_edge', 'description': 'Edge conflict'}
        options = self.resolver._get_dag_resolution_options(edge_conflict)

        option_actions = [opt['action'] for opt in options]
        self.assertIn(ResolutionAction.KEEP_LOCAL, option_actions)
        self.assertIn(ResolutionAction.KEEP_REMOTE, option_actions)
        self.assertIn(ResolutionAction.KEEP_BOTH, option_actions)

    def test_get_config_resolution_options(self):
        """Test getting config conflict resolution options."""
        # Test UUID conflict
        uuid_conflict = {'type': 'uuid_conflict', 'description': 'UUID mismatch'}
        options = self.resolver._get_config_resolution_options(uuid_conflict)

        self.assertGreater(len(options), 0)
        option_actions = [opt['action'] for opt in options]
        self.assertIn(ResolutionAction.KEEP_LOCAL, option_actions)
        self.assertIn(ResolutionAction.KEEP_REMOTE, option_actions)
        self.assertIn(ResolutionAction.MANUAL_EDIT, option_actions)

        # Check for warning in UUID conflict options
        uuid_options = [opt for opt in options if opt['action'] in
                       [ResolutionAction.KEEP_LOCAL, ResolutionAction.KEEP_REMOTE]]
        for option in uuid_options:
            self.assertIn('warning', option)

        # Test generic config conflict
        config_conflict = {'type': 'config_conflict', 'description': 'Config mismatch'}
        options = self.resolver._get_config_resolution_options(config_conflict)

        option_actions = [opt['action'] for opt in options]
        self.assertIn(ResolutionAction.KEEP_LOCAL, option_actions)
        self.assertIn(ResolutionAction.KEEP_REMOTE, option_actions)
        self.assertIn(ResolutionAction.KEEP_BOTH, option_actions)
        self.assertIn(ResolutionAction.MANUAL_EDIT, option_actions)

    @patch('builtins.input')
    def test_present_resolution_options(self, mock_input):
        """Test presenting resolution options to user."""
        options = [
            {'action': ResolutionAction.KEEP_LOCAL, 'description': 'Keep local', 'key': '1'},
            {'action': ResolutionAction.KEEP_REMOTE, 'description': 'Keep remote', 'key': '2'},
            {'action': ResolutionAction.SKIP, 'description': 'Skip', 'key': 's'},
            {'action': ResolutionAction.ABORT, 'description': 'Abort', 'key': 'a'}
        ]

        conflict = {'description': 'Test conflict'}

        # Test valid choice
        mock_input.return_value = '1'
        result = self.resolver._present_resolution_options(options, conflict)
        self.assertEqual(result, ResolutionAction.KEEP_LOCAL)

        # Test skip choice
        mock_input.return_value = 's'
        result = self.resolver._present_resolution_options(options, conflict)
        self.assertEqual(result, ResolutionAction.SKIP)

        # Test abort choice
        mock_input.return_value = 'a'
        result = self.resolver._present_resolution_options(options, conflict)
        self.assertEqual(result, ResolutionAction.ABORT)

    @patch('builtins.input')
    def test_present_resolution_options_invalid(self, mock_input):
        """Test handling invalid user input."""
        options = [
            {'action': ResolutionAction.KEEP_LOCAL, 'description': 'Keep local', 'key': '1'},
            {'action': ResolutionAction.SKIP, 'description': 'Skip', 'key': 's'}
        ]

        conflict = {'description': 'Test conflict'}

        # Simulate invalid input followed by valid input
        mock_input.side_effect = ['x', 'invalid', '1']

        result = self.resolver._present_resolution_options(options, conflict)

        self.assertEqual(result, ResolutionAction.KEEP_LOCAL)
        self.assertEqual(mock_input.call_count, 3)

    @patch('builtins.input', side_effect=KeyboardInterrupt)
    def test_present_resolution_options_interrupt(self, mock_input):
        """Test handling keyboard interrupt."""
        options = [
            {'action': ResolutionAction.KEEP_LOCAL, 'description': 'Keep local', 'key': '1'}
        ]

        conflict = {'description': 'Test conflict'}

        result = self.resolver._present_resolution_options(options, conflict)

        self.assertEqual(result, ResolutionAction.ABORT)

    def test_show_dag_diff(self):
        """Test showing DAG differences."""
        # Test with list data
        local_data = ['task1', 'task2', 'task3']
        remote_data = ['task2', 'task3', 'task4']

        # This should not crash
        self.resolver._show_dag_diff(local_data, remote_data)

        # Test with dict data
        local_dict = {'param1': 'value1', 'param2': 'value2'}
        remote_dict = {'param1': 'different', 'param3': 'value3'}

        self.resolver._show_dag_diff(local_dict, remote_dict)

        # Test with other data types
        self.resolver._show_dag_diff('local', 'remote')

    def test_apply_dag_resolution(self):
        """Test applying DAG conflict resolution."""
        conflict = {'type': 'cycle_creation', 'description': 'Cycle detected'}
        action = ResolutionAction.KEEP_LOCAL

        result = self.resolver._apply_dag_resolution(conflict, action)

        self.assertTrue(result['success'])
        self.assertIn('details', result)

    def test_apply_config_resolution(self):
        """Test applying config conflict resolution."""
        conflict = {'type': 'uuid_conflict', 'description': 'UUID mismatch'}
        action = ResolutionAction.KEEP_REMOTE

        result = self.resolver._apply_config_resolution(conflict, action)

        self.assertTrue(result['success'])
        self.assertIn('details', result)

    @patch('subprocess.run')
    def test_edit_file_manually(self, mock_subprocess):
        """Test manual file editing."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        # Test successful edit
        result = self.resolver._edit_file_manually('/tmp/test.txt')
        self.assertTrue(result)

        # Test failed edit
        mock_subprocess.side_effect = Exception('Editor not found')
        result = self.resolver._edit_file_manually('/tmp/test.txt')
        self.assertFalse(result)

    def test_resolution_action_enum(self):
        """Test ResolutionAction enum values."""
        self.assertEqual(ResolutionAction.KEEP_LOCAL.value, 'keep_local')
        self.assertEqual(ResolutionAction.KEEP_REMOTE.value, 'keep_remote')
        self.assertEqual(ResolutionAction.KEEP_BOTH.value, 'keep_both')
        self.assertEqual(ResolutionAction.MANUAL_EDIT.value, 'manual_edit')
        self.assertEqual(ResolutionAction.SKIP.value, 'skip')
        self.assertEqual(ResolutionAction.ABORT.value, 'abort')

    def test_show_resolution_summary(self):
        """Test showing resolution summary."""
        results = {
            'success': True,
            'resolved': 5,
            'skipped': 2,
            'remaining': 0,
            'actions': [
                {'conflict': 'Conflict 1', 'action': 'keep_local'},
                {'conflict': 'Conflict 2', 'action': 'keep_remote'}
            ]
        }

        # This should not crash
        self.resolver._show_resolution_summary(results)

        # Test with unresolved conflicts
        results['success'] = False
        results['remaining'] = 3
        self.resolver._show_resolution_summary(results)

    @patch('CelebiChrono.interface.merge_resolver.DAGVisualizer')
    @patch('CelebiChrono.kernel.vobj_arc_merge.DAGMerger')
    def test_preview_merge(self, mock_merger, mock_visualizer):
        """Test merge preview generation."""
        # Mock DAGs
        local_dag = Mock()
        remote_dag = Mock()
        base_dag = Mock()

        local_dag.number_of_nodes.return_value = 3
        local_dag.number_of_edges.return_value = 2
        remote_dag.number_of_nodes.return_value = 4
        remote_dag.number_of_edges.return_value = 3

        # Mock merger
        mock_merger_instance = Mock()
        mock_merger.return_value = mock_merger_instance

        merged_dag = Mock()
        merged_dag.number_of_nodes.return_value = 5
        merged_dag.number_of_edges.return_value = 4
        mock_merger_instance.merge_dags.return_value = merged_dag
        mock_merger_instance.get_conflicts.return_value = []

        # Mock topological sort
        merged_dag.predecessors.return_value = []
        try:
            import networkx as nx
            # Mock networkx topological sort if needed
            with patch('networkx.topological_sort') as mock_topo:
                mock_topo.return_value = ['A', 'B', 'C']
                preview = self.resolver.preview_merge(local_dag, remote_dag, base_dag)
        except ImportError:
            # If networkx not available, just test it doesn't crash
            preview = self.resolver.preview_merge(local_dag, remote_dag, base_dag)

        self.assertIsInstance(preview, str)
        self.assertIn('MERGE PREVIEW', preview)


if __name__ == '__main__':
    unittest.main()