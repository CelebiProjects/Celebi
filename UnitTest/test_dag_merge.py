"""Unit tests for DAG merging algorithms."""
import unittest
import networkx as nx

from CelebiChrono.kernel.vobj_arc_merge import (
    DAGMerger, MergeConflictType, MergeResolutionStrategy
)


class TestDAGMerger(unittest.TestCase):
    """Test cases for DAGMerger class."""

    def setUp(self):
        """Set up test fixtures."""
        self.merger = DAGMerger()

    def test_simple_merge_no_conflicts(self):
        """Test merging DAGs with no conflicts."""
        # Create simple DAGs
        local_dag = nx.DiGraph()
        local_dag.add_edges_from([('A', 'B'), ('B', 'C')])

        remote_dag = nx.DiGraph()
        remote_dag.add_edges_from([('A', 'B'), ('B', 'C')])

        base_dag = nx.DiGraph()
        base_dag.add_edges_from([('A', 'B'), ('B', 'C')])

        # Merge
        merged = self.merger.merge_dags(local_dag, remote_dag, base_dag)

        # Check result
        self.assertEqual(set(merged.nodes()), {'A', 'B', 'C'})
        self.assertEqual(set(merged.edges()), {('A', 'B'), ('B', 'C')})
        self.assertFalse(self.merger.has_conflicts())

    def test_additive_edge_merge(self):
        """Test merging with additive edges (edges added in one branch)."""
        # Base: A -> B
        base_dag = nx.DiGraph()
        base_dag.add_edges_from([('A', 'B')])

        # Local: A -> B, B -> C (added C)
        local_dag = nx.DiGraph()
        local_dag.add_edges_from([('A', 'B'), ('B', 'C')])

        # Remote: A -> B (no changes)
        remote_dag = nx.DiGraph()
        remote_dag.add_edges_from([('A', 'B')])

        # Merge with auto strategy (should keep additive edge)
        self.merger.strategy = MergeResolutionStrategy.AUTO_MERGE
        merged = self.merger.merge_dags(local_dag, remote_dag, base_dag)

        # Should include additive edge
        self.assertIn(('B', 'C'), merged.edges())
        self.assertFalse(self.merger.has_conflicts())

    def test_subtractive_edge_conflict(self):
        """Test merging with subtractive edges (edges removed in one branch)."""
        # Base: A -> B, B -> C
        base_dag = nx.DiGraph()
        base_dag.add_edges_from([('A', 'B'), ('B', 'C')])

        # Local: A -> B (removed B -> C)
        local_dag = nx.DiGraph()
        local_dag.add_edges_from([('A', 'B')])

        # Remote: A -> B, B -> C (no changes)
        remote_dag = nx.DiGraph()
        remote_dag.add_edges_from([('A', 'B'), ('B', 'C')])

        # Merge
        merged = self.merger.merge_dags(local_dag, remote_dag, base_dag)

        # Should have conflict
        self.assertTrue(self.merger.has_conflicts())
        conflicts = self.merger.get_conflicts()
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].conflict_type, MergeConflictType.SUBTRACTIVE_EDGE)

    def test_cycle_detection(self):
        """Test detection of cycles created by merge."""
        # Base: A -> B
        base_dag = nx.DiGraph()
        base_dag.add_edges_from([('A', 'B')])

        # Local: A -> B, B -> C
        local_dag = nx.DiGraph()
        local_dag.add_edges_from([('A', 'B'), ('B', 'C')])

        # Remote: A -> B, C -> A (creates cycle A->B->C->A)
        remote_dag = nx.DiGraph()
        remote_dag.add_edges_from([('A', 'B'), ('C', 'A')])

        # Merge
        merged = self.merger.merge_dags(local_dag, remote_dag, base_dag)

        # Should detect cycle conflict
        self.assertTrue(self.merger.has_conflicts())
        conflicts = self.merger.get_conflicts()
        cycle_conflicts = [c for c in conflicts if c.conflict_type == MergeConflictType.CYCLE_CREATION]
        self.assertGreater(len(cycle_conflicts), 0)

    def test_contradictory_edges(self):
        """Test merging with contradictory edges (same source, different targets)."""
        # Base: A -> B
        base_dag = nx.DiGraph()
        base_dag.add_edges_from([('A', 'B')])

        # Local: A -> B, A -> C (added C as alternative to B)
        local_dag = nx.DiGraph()
        local_dag.add_edges_from([('A', 'B'), ('A', 'C')])

        # Remote: A -> B, A -> D (added D as alternative to B)
        remote_dag = nx.DiGraph()
        remote_dag.add_edges_from([('A', 'B'), ('A', 'D')])

        # Merge
        merged = self.merger.merge_dags(local_dag, remote_dag, base_dag)

        # Should have contradictory edge conflict
        self.assertTrue(self.merger.has_conflicts())
        conflicts = self.merger.get_conflicts()
        contradictory_conflicts = [
            c for c in conflicts
            if c.conflict_type == MergeConflictType.CONTRADICTORY_EDGE
        ]
        self.assertGreater(len(contradictory_conflicts), 0)

    def test_local_preference_strategy(self):
        """Test local preference merge strategy."""
        # Base: A -> B
        base_dag = nx.DiGraph()
        base_dag.add_edges_from([('A', 'B')])

        # Local: A -> B, A -> C (added C)
        local_dag = nx.DiGraph()
        local_dag.add_edges_from([('A', 'B'), ('A', 'C')])

        # Remote: A -> B, A -> D (added D instead of C)
        remote_dag = nx.DiGraph()
        remote_dag.add_edges_from([('A', 'B'), ('A', 'D')])

        # Merge with local preference
        self.merger.strategy = MergeResolutionStrategy.LOCAL_PREFERENCE
        merged = self.merger.merge_dags(local_dag, remote_dag, base_dag)

        # Should prefer local changes
        self.assertIn(('A', 'C'), merged.edges())
        self.assertNotIn(('A', 'D'), merged.edges())

    def test_union_strategy(self):
        """Test union merge strategy."""
        # Base: A -> B
        base_dag = nx.DiGraph()
        base_dag.add_edges_from([('A', 'B')])

        # Local: A -> B, A -> C
        local_dag = nx.DiGraph()
        local_dag.add_edges_from([('A', 'B'), ('A', 'C')])

        # Remote: A -> B, A -> D
        remote_dag = nx.DiGraph()
        remote_dag.add_edges_from([('A', 'B'), ('A', 'D')])

        # Merge with union strategy
        self.merger.strategy = MergeResolutionStrategy.UNION
        merged = self.merger.merge_dags(local_dag, remote_dag, base_dag)

        # Should include both C and D
        self.assertIn(('A', 'C'), merged.edges())
        self.assertIn(('A', 'D'), merged.edges())

    def test_apply_resolutions(self):
        """Test applying conflict resolutions to graph."""
        # Create a merge with conflicts
        base_dag = nx.DiGraph()
        base_dag.add_edges_from([('A', 'B')])

        local_dag = nx.DiGraph()
        local_dag.add_edges_from([('A', 'B')])  # Removed in remote

        remote_dag = nx.DiGraph()
        remote_dag.add_edges_from([])  # Removed A -> B

        # Merge
        merged = self.merger.merge_dags(local_dag, remote_dag, base_dag)

        # Should have conflict
        self.assertTrue(self.merger.has_conflicts())

        # Resolve conflict (choose to keep edge)
        conflicts = self.merger.get_conflicts()
        if conflicts:
            self.merger.resolve_conflict_interactively(0, 0)  # Choose first option (keep)
            self.merger.apply_resolutions_to_graph()

            # Edge should be kept
            self.assertIn(('A', 'B'), merged.edges())

    def test_dag_validation(self):
        """Test DAG validation after merge."""
        # Create valid DAG
        dag = nx.DiGraph()
        dag.add_edges_from([('A', 'B'), ('B', 'C'), ('C', 'D')])

        # Should not raise
        try:
            self.merger.merged_graph = dag
            self.merger._validate_merged_dag()
        except ValueError:
            self.fail("Valid DAG should not raise validation error")

        # Create invalid DAG with cycle
        cyclic_dag = nx.DiGraph()
        cyclic_dag.add_edges_from([('A', 'B'), ('B', 'C'), ('C', 'A')])

        # Should raise
        with self.assertRaises(ValueError):
            self.merger.merged_graph = cyclic_dag
            self.merger._validate_merged_dag()


if __name__ == '__main__':
    unittest.main()