""" DAG merging algorithms for Celebi git integration.

This module provides specialized algorithms for merging dependency graphs
with cycle detection and conflict resolution.
"""
import networkx as nx
from collections import defaultdict
from enum import Enum
from typing import Dict, List, Set, Tuple, Optional, Any
from logging import getLogger

logger = getLogger("ChernLogger")


class MergeConflictType(Enum):
    """Types of merge conflicts that can occur during DAG merging."""
    ADDITIVE_EDGE = "additive_edge"  # Edge added in one branch but not the other
    SUBTRACTIVE_EDGE = "subtractive_edge"  # Edge removed in one branch but not the other
    MODIFIED_EDGE = "modified_edge"  # Edge changed differently in both branches
    CONTRADICTORY_EDGE = "contradictory_edge"  # Same source, different targets
    CYCLE_CREATION = "cycle_creation"  # Merge would create a cycle
    MISSING_NODE = "missing_node"  # Node referenced but missing in one branch
    UUID_CONFLICT = "uuid_conflict"  # Same UUID with different content


class MergeResolutionStrategy(Enum):
    """Strategies for resolving merge conflicts."""
    UNION = "union"  # Keep both changes if possible
    LOCAL_PREFERENCE = "local_preference"  # Prefer local branch changes
    REMOTE_PREFERENCE = "remote_preference"  # Prefer remote branch changes
    INTERACTIVE = "interactive"  # Ask user to choose
    AUTO_MERGE = "auto_merge"  # Automatic resolution based on heuristics


class MergeConflict:
    """Represents a merge conflict with resolution options."""

    def __init__(self, conflict_type: MergeConflictType,
                 description: str,
                 local_data: Any = None,
                 remote_data: Any = None,
                 base_data: Any = None,
                 resolution_options: List[Dict] = None):
        self.conflict_type = conflict_type
        self.description = description
        self.local_data = local_data
        self.remote_data = remote_data
        self.base_data = base_data
        self.resolution_options = resolution_options or []
        self.resolution = None
        self.resolved = False

    def add_resolution_option(self, option: Dict):
        """Add a resolution option to this conflict."""
        self.resolution_options.append(option)

    def resolve(self, option_index: int):
        """Resolve the conflict using the specified option."""
        if 0 <= option_index < len(self.resolution_options):
            self.resolution = self.resolution_options[option_index]
            self.resolved = True
            return True
        return False

    def __str__(self):
        return f"{self.conflict_type.value}: {self.description}"


class DAGMerger:
    """Specialized algorithm for merging dependency graphs with cycle detection."""

    def __init__(self, strategy: MergeResolutionStrategy = MergeResolutionStrategy.AUTO_MERGE):
        self.strategy = strategy
        self.conflicts: List[MergeConflict] = []
        self.merged_graph: Optional[nx.DiGraph] = None

    def merge_dags(self, local_dag: nx.DiGraph, remote_dag: nx.DiGraph,
                   base_dag: nx.DiGraph) -> nx.DiGraph:
        """
        Perform a three-way merge of dependency DAGs.

        Args:
            local_dag: DAG from local/master branch
            remote_dag: DAG from remote/feature branch
            base_dag: DAG from common ancestor

        Returns:
            Merged DAG with conflicts resolved according to strategy
        """
        logger.info("Starting DAG merge with %s strategy", self.strategy.value)

        # Step 1: Node union - include all nodes from both branches
        merged_nodes = self._union_nodes(local_dag, remote_dag)

        # Step 2: Create initial merged graph with all nodes
        self.merged_graph = nx.DiGraph()
        for node in merged_nodes:
            self.merged_graph.add_node(node)

        # Step 3: Classify and merge edges
        self._classify_and_merge_edges(local_dag, remote_dag, base_dag)

        # Step 4: Detect and resolve cycles
        self._detect_and_resolve_cycles()

        # Step 5: Apply conflict resolution strategy
        self._apply_resolution_strategy()

        # Step 6: Validate merged DAG
        self._validate_merged_dag()

        logger.info("DAG merge completed with %d conflicts", len(self.conflicts))
        return self.merged_graph

    def _union_nodes(self, local_dag: nx.DiGraph, remote_dag: nx.DiGraph) -> Set:
        """Create union of nodes from both DAGs."""
        local_nodes = set(local_dag.nodes())
        remote_nodes = set(remote_dag.nodes())
        return local_nodes.union(remote_nodes)

    def _classify_and_merge_edges(self, local_dag: nx.DiGraph,
                                  remote_dag: nx.DiGraph,
                                  base_dag: nx.DiGraph):
        """Classify edges and add them to merged graph with conflict detection."""
        all_edges = set()

        # Collect all edges from all graphs
        for u, v in local_dag.edges():
            all_edges.add((u, v))
        for u, v in remote_dag.edges():
            all_edges.add((u, v))
        for u, v in base_dag.edges():
            all_edges.add((u, v))

        # Classify each edge
        for u, v in all_edges:
            in_local = local_dag.has_edge(u, v)
            in_remote = remote_dag.has_edge(u, v)
            in_base = base_dag.has_edge(u, v)

            edge_info = {
                'source': u,
                'target': v,
                'in_local': in_local,
                'in_remote': in_remote,
                'in_base': in_base
            }

            # Classify edge type
            if in_local and in_remote:
                # Edge in both branches - add to merged graph
                self.merged_graph.add_edge(u, v)
            elif in_local and not in_remote:
                # Edge only in local branch
                if in_base:
                    # Edge removed in remote - subtractive conflict
                    conflict = MergeConflict(
                        MergeConflictType.SUBTRACTIVE_EDGE,
                        f"Edge {u} -> {v} removed in remote branch",
                        local_data=edge_info,
                        remote_data=None,
                        base_data=edge_info
                    )
                    conflict.add_resolution_option({
                        'description': 'Keep edge (prefer local)',
                        'action': 'add_edge',
                        'data': (u, v)
                    })
                    conflict.add_resolution_option({
                        'description': 'Remove edge (prefer remote)',
                        'action': 'skip_edge',
                        'data': (u, v)
                    })
                    self.conflicts.append(conflict)
                else:
                    # Edge added in local - additive change
                    self.merged_graph.add_edge(u, v)
            elif not in_local and in_remote:
                # Edge only in remote branch
                if in_base:
                    # Edge removed in local - subtractive conflict
                    conflict = MergeConflict(
                        MergeConflictType.SUBTRACTIVE_EDGE,
                        f"Edge {u} -> {v} removed in local branch",
                        local_data=None,
                        remote_data=edge_info,
                        base_data=edge_info
                    )
                    conflict.add_resolution_option({
                        'description': 'Keep edge (prefer remote)',
                        'action': 'add_edge',
                        'data': (u, v)
                    })
                    conflict.add_resolution_option({
                        'description': 'Remove edge (prefer local)',
                        'action': 'skip_edge',
                        'data': (u, v)
                    })
                    self.conflicts.append(conflict)
                else:
                    # Edge added in remote - additive change
                    self.merged_graph.add_edge(u, v)
            else:
                # Edge only in base (should have been caught above)
                pass

            # Check for contradictory edges (same source, different targets)
            self._detect_contradictory_edges(local_dag, remote_dag, u, v)

    def _detect_contradictory_edges(self, local_dag: nx.DiGraph,
                                    remote_dag: nx.DiGraph,
                                    u: Any, v: Any):
        """Detect contradictory edges where same source has different targets."""
        local_targets = set(local_dag.successors(u))
        remote_targets = set(remote_dag.successors(u))

        # Find targets that exist in only one branch
        only_local = local_targets - remote_targets
        only_remote = remote_targets - local_targets

        if only_local and only_remote:
            # Contradictory edges detected
            conflict = MergeConflict(
                MergeConflictType.CONTRADICTORY_EDGE,
                f"Source node {u} has different target sets in each branch",
                local_data=list(only_local),
                remote_data=list(only_remote),
                base_data=None
            )
            conflict.add_resolution_option({
                'description': 'Union - keep all targets',
                'action': 'union_targets',
                'data': {'source': u, 'targets': list(local_targets.union(remote_targets))}
            })
            conflict.add_resolution_option({
                'description': 'Prefer local targets',
                'action': 'prefer_local_targets',
                'data': {'source': u, 'targets': list(local_targets)}
            })
            conflict.add_resolution_option({
                'description': 'Prefer remote targets',
                'action': 'prefer_remote_targets',
                'data': {'source': u, 'targets': list(remote_targets)}
            })
            self.conflicts.append(conflict)

    def _detect_and_resolve_cycles(self):
        """Detect cycles in merged graph and create conflicts for them."""
        if not self.merged_graph:
            return

        try:
            # NetworkX raises NetworkXUnfeasible if graph has cycles
            nx.find_cycle(self.merged_graph, orientation='original')
            # If we get here, there's a cycle
            cycles = list(nx.simple_cycles(self.merged_graph))

            for cycle in cycles:
                conflict = MergeConflict(
                    MergeConflictType.CYCLE_CREATION,
                    f"Cycle detected: {' -> '.join(str(n) for n in cycle)} -> {cycle[0]}",
                    local_data=cycle,
                    remote_data=cycle,
                    base_data=None
                )

                # Generate resolution options - suggest removing each edge in cycle
                for i in range(len(cycle)):
                    u = cycle[i]
                    v = cycle[(i + 1) % len(cycle)]
                    conflict.add_resolution_option({
                        'description': f'Remove edge {u} -> {v} to break cycle',
                        'action': 'remove_edge',
                        'data': (u, v)
                    })

                self.conflicts.append(conflict)

        except nx.NetworkXNoCycle:
            # No cycles - good!
            pass

    def _apply_resolution_strategy(self):
        """Apply the configured resolution strategy to all conflicts."""
        if self.strategy == MergeResolutionStrategy.AUTO_MERGE:
            self._apply_auto_merge()
        elif self.strategy == MergeResolutionStrategy.LOCAL_PREFERENCE:
            self._apply_local_preference()
        elif self.strategy == MergeResolutionStrategy.REMOTE_PREFERENCE:
            self._apply_remote_preference()
        elif self.strategy == MergeResolutionStrategy.UNION:
            self._apply_union_strategy()
        # INTERACTIVE strategy requires user input, handled separately

    def _apply_auto_merge(self):
        """Apply automatic merge heuristics."""
        for conflict in self.conflicts:
            if conflict.resolved:
                continue

            if conflict.conflict_type == MergeConflictType.ADDITIVE_EDGE:
                # For additive edges, keep both (union)
                conflict.resolve(0)  # First option is usually "keep"
            elif conflict.conflict_type == MergeConflictType.SUBTRACTIVE_EDGE:
                # For subtractive edges, remove only if removed in both branches
                # Since this is a subtractive conflict, edge was removed in one branch
                # Auto-merge: keep the edge (don't remove)
                conflict.resolve(0)  # Keep edge
            elif conflict.conflict_type == MergeConflictType.CONTRADICTORY_EDGE:
                # For contradictory edges, prefer union if no cycles
                conflict.resolve(0)  # Union option
            elif conflict.conflict_type == MergeConflictType.CYCLE_CREATION:
                # For cycles, remove the newest edge (heuristic)
                conflict.resolve(0)  # First suggested edge removal

    def _apply_local_preference(self):
        """Prefer local branch changes."""
        for conflict in self.conflicts:
            if conflict.resolved:
                continue

            # Find option that prefers local
            for i, option in enumerate(conflict.resolution_options):
                if 'prefer_local' in option.get('description', '').lower():
                    conflict.resolve(i)
                    break
            else:
                # Default to first option
                conflict.resolve(0)

    def _apply_remote_preference(self):
        """Prefer remote branch changes."""
        for conflict in self.conflicts:
            if conflict.resolved:
                continue

            # Find option that prefers remote
            for i, option in enumerate(conflict.resolution_options):
                if 'prefer_remote' in option.get('description', '').lower():
                    conflict.resolve(i)
                    break
            else:
                # Default to first option
                conflict.resolve(0)

    def _apply_union_strategy(self):
        """Apply union strategy - keep changes from both branches when possible."""
        for conflict in self.conflicts:
            if conflict.resolved:
                continue

            # Find union option
            for i, option in enumerate(conflict.resolution_options):
                if 'union' in option.get('description', '').lower():
                    conflict.resolve(i)
                    break
            else:
                # Default to first option
                conflict.resolve(0)

    def _validate_merged_dag(self):
        """Validate that merged graph is a valid DAG."""
        if not self.merged_graph:
            raise ValueError("No merged graph to validate")

        # Check for cycles
        try:
            nx.find_cycle(self.merged_graph, orientation='original')
            raise ValueError("Merged graph contains cycles")
        except nx.NetworkXNoCycle:
            pass  # Good - no cycles

        # Check for missing node references
        for u, v in self.merged_graph.edges():
            if u not in self.merged_graph.nodes() or v not in self.merged_graph.nodes():
                raise ValueError(f"Edge references missing node: {u} -> {v}")

    def get_conflicts(self) -> List[MergeConflict]:
        """Get list of unresolved conflicts."""
        return [c for c in self.conflicts if not c.resolved]

    def has_conflicts(self) -> bool:
        """Check if there are unresolved conflicts."""
        return any(not c.resolved for c in self.conflicts)

    def resolve_conflict_interactively(self, conflict_index: int, option_index: int) -> bool:
        """Resolve a specific conflict interactively."""
        if 0 <= conflict_index < len(self.conflicts):
            conflict = self.conflicts[conflict_index]
            return conflict.resolve(option_index)
        return False

    def apply_resolutions_to_graph(self):
        """Apply all conflict resolutions to the merged graph."""
        if not self.merged_graph:
            return

        for conflict in self.conflicts:
            if not conflict.resolved or not conflict.resolution:
                continue

            action = conflict.resolution['action']
            data = conflict.resolution['data']

            if action == 'add_edge':
                u, v = data
                self.merged_graph.add_edge(u, v)
            elif action == 'skip_edge':
                u, v = data
                if self.merged_graph.has_edge(u, v):
                    self.merged_graph.remove_edge(u, v)
            elif action == 'remove_edge':
                u, v = data
                if self.merged_graph.has_edge(u, v):
                    self.merged_graph.remove_edge(u, v)
            elif action == 'union_targets':
                source = data['source']
                targets = data['targets']
                # Remove existing edges from this source
                existing_targets = list(self.merged_graph.successors(source))
                for target in existing_targets:
                    self.merged_graph.remove_edge(source, target)
                # Add union edges
                for target in targets:
                    self.merged_graph.add_edge(source, target)
            elif action == 'prefer_local_targets' or action == 'prefer_remote_targets':
                source = data['source']
                targets = data['targets']
                # Remove existing edges from this source
                existing_targets = list(self.merged_graph.successors(source))
                for target in existing_targets:
                    self.merged_graph.remove_edge(source, target)
                # Add preferred edges
                for target in targets:
                    self.merged_graph.add_edge(source, target)