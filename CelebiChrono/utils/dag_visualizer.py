"""DAG visualization for merge conflict resolution.

This module provides ASCII/Unicode graph visualization for DAG conflicts
to help users understand and resolve merge conflicts.
"""
import networkx as nx
from typing import Dict, List, Set, Tuple, Any, Optional
from collections import defaultdict
from enum import Enum
from logging import getLogger

logger = getLogger("ChernLogger")


class EdgeType(Enum):
    """Types of edges in visualization."""
    LOCAL_ONLY = "local_only"  # Edge only in local branch
    REMOTE_ONLY = "remote_only"  # Edge only in remote branch
    BOTH = "both"  # Edge in both branches
    CONFLICT = "conflict"  # Edge with conflict
    CYCLE = "cycle"  # Edge that creates cycle


class DAGVisualizer:
    """Visualizes DAGs and merge conflicts in ASCII/Unicode format."""

    def __init__(self, use_unicode: bool = True):
        self.use_unicode = use_unicode
        self.node_labels: Dict[Any, str] = {}
        self.edge_types: Dict[Tuple[Any, Any], EdgeType] = {}

    def visualize_merge_conflict(self, local_dag: nx.DiGraph,
                                 remote_dag: nx.DiGraph,
                                 base_dag: nx.DiGraph,
                                 conflicts: List[Dict]) -> str:
        """
        Create a visualization showing merge conflicts between DAGs.

        Args:
            local_dag: DAG from local branch
            remote_dag: DAG from remote branch
            base_dag: DAG from common ancestor
            conflicts: List of merge conflicts

        Returns:
            ASCII/Unicode visualization string
        """
        # Build combined graph for visualization
        combined = nx.DiGraph()

        # Add all nodes
        all_nodes = set(local_dag.nodes()) | set(remote_dag.nodes()) | set(base_dag.nodes())
        for node in all_nodes:
            combined.add_node(node)
            self.node_labels[node] = self._get_node_label(node)

        # Classify edges
        self._classify_edges(local_dag, remote_dag, base_dag)

        # Add edges to combined graph with types
        for (u, v), edge_type in self.edge_types.items():
            combined.add_edge(u, v, type=edge_type)

        # Generate visualization
        output = []
        output.append("=" * 80)
        output.append("DAG MERGE CONFLICT VISUALIZATION")
        output.append("=" * 80)
        output.append("")

        # Legend
        output.append("LEGEND:")
        if self.use_unicode:
            output.append("  ────►  Edge in both branches")
            output.append("  ───L►  Edge only in local branch")
            output.append("  ───R►  Edge only in remote branch")
            output.append("  ════►  Conflicting edge")
            output.append("  ───◯─►  Edge that creates cycle")
        else:
            output.append("  ---->  Edge in both branches")
            output.append("  ---L>  Edge only in local branch")
            output.append("  ---R>  Edge only in remote branch")
            output.append("  ====>  Conflicting edge")
            output.append("  ---O->  Edge that creates cycle")
        output.append("")

        # Show conflicts summary
        if conflicts:
            output.append("CONFLICTS FOUND:")
            for i, conflict in enumerate(conflicts, 1):
                output.append(f"  {i}. {conflict.get('description', 'Unknown conflict')}")
            output.append("")

        # Generate topological layout for visualization
        try:
            # Try to get topological order
            topological_order = list(nx.topological_sort(combined))
            layers = self._assign_layers(combined, topological_order)

            # Visualize by layers
            output.append("DEPENDENCY GRAPH (topological layers):")
            output.append("")

            for layer_idx, layer_nodes in enumerate(layers):
                output.append(f"Layer {layer_idx + 1}:")
                for node in layer_nodes:
                    node_str = self._format_node(node, combined)
                    output.append(f"  {node_str}")

                    # Show outgoing edges
                    for succ in combined.successors(node):
                        edge_type = combined.edges[node, succ]['type']
                        edge_str = self._format_edge(edge_type)
                        succ_label = self.node_labels.get(succ, str(succ))
                        output.append(f"    {edge_str} {succ_label}")
                output.append("")

        except nx.NetworkXUnfeasible:
            # Graph has cycles - use spring layout approximation
            output.append("WARNING: Graph contains cycles (invalid DAG)")
            output.append("Showing approximate layout:")
            output.append("")

            # Use simple depth-first traversal
            visited = set()
            for node in combined.nodes():
                if node not in visited:
                    self._visualize_subgraph(node, combined, visited, 0, output)

        # Show detailed conflict information
        if conflicts:
            output.append("DETAILED CONFLICT INFORMATION:")
            output.append("")
            for i, conflict in enumerate(conflicts, 1):
                output.append(f"Conflict {i}:")
                output.append(f"  Type: {conflict.get('type', 'unknown')}")
                output.append(f"  Description: {conflict.get('description', 'No description')}")

                if 'local' in conflict:
                    output.append(f"  Local: {conflict['local']}")
                if 'remote' in conflict:
                    output.append(f"  Remote: {conflict['remote']}")
                if 'base' in conflict:
                    output.append(f"  Base: {conflict['base']}")

                if 'resolution_options' in conflict:
                    output.append("  Resolution options:")
                    for j, option in enumerate(conflict['resolution_options'], 1):
                        output.append(f"    {j}. {option.get('description', 'No description')}")
                output.append("")

        return '\n'.join(output)

    def _classify_edges(self, local_dag: nx.DiGraph,
                        remote_dag: nx.DiGraph,
                        base_dag: nx.DiGraph):
        """Classify edges by their presence in each DAG."""
        all_edges = set()

        # Collect all edges
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

            if in_local and in_remote:
                self.edge_types[(u, v)] = EdgeType.BOTH
            elif in_local and not in_remote:
                if in_base:
                    self.edge_types[(u, v)] = EdgeType.CONFLICT  # Removed in remote
                else:
                    self.edge_types[(u, v)] = EdgeType.LOCAL_ONLY  # Added in local
            elif not in_local and in_remote:
                if in_base:
                    self.edge_types[(u, v)] = EdgeType.CONFLICT  # Removed in local
                else:
                    self.edge_types[(u, v)] = EdgeType.REMOTE_ONLY  # Added in remote
            else:
                # Edge only in base (should be rare)
                self.edge_types[(u, v)] = EdgeType.CONFLICT

    def _assign_layers(self, graph: nx.DiGraph,
                       topological_order: List) -> List[List[Any]]:
        """Assign nodes to layers based on topological order and longest path."""
        # Calculate longest path to each node
        longest_path = {}
        for node in topological_order:
            preds = list(graph.predecessors(node))
            if not preds:
                longest_path[node] = 0
            else:
                longest_path[node] = max(longest_path[p] for p in preds) + 1

        # Group nodes by layer
        max_layer = max(longest_path.values()) if longest_path else 0
        layers = [[] for _ in range(max_layer + 1)]

        for node, layer in longest_path.items():
            layers[layer].append(node)

        return layers

    def _visualize_subgraph(self, node: Any, graph: nx.DiGraph,
                            visited: Set, depth: int,
                            output: List[str]):
        """Visualize subgraph starting from node with depth-first traversal."""
        if node in visited:
            return

        visited.add(node)
        indent = "  " * depth

        node_str = self._format_node(node, graph)
        output.append(f"{indent}{node_str}")

        # Show successors
        for succ in graph.successors(node):
            if succ not in visited:
                edge_type = graph.edges[node, succ]['type']
                edge_str = self._format_edge(edge_type)
                succ_label = self.node_labels.get(succ, str(succ))
                output.append(f"{indent}  {edge_str} {succ_label}")
                self._visualize_subgraph(succ, graph, visited, depth + 2, output)

    def _format_node(self, node: Any, graph: nx.DiGraph) -> str:
        """Format a node for display."""
        label = self.node_labels.get(node, str(node))

        # Check if node is involved in conflicts
        conflict_edges = []
        for (u, v), edge_type in self.edge_types.items():
            if edge_type == EdgeType.CONFLICT and (u == node or v == node):
                conflict_edges.append((u, v))

        if conflict_edges:
            return f"[{label}] (CONFLICT)"
        else:
            return f"[{label}]"

    def _format_edge(self, edge_type: EdgeType) -> str:
        """Format an edge for display based on its type."""
        if self.use_unicode:
            if edge_type == EdgeType.BOTH:
                return "────►"
            elif edge_type == EdgeType.LOCAL_ONLY:
                return "────L►"
            elif edge_type == EdgeType.REMOTE_ONLY:
                return "────R►"
            elif edge_type == EdgeType.CONFLICT:
                return "════►"
            elif edge_type == EdgeType.CYCLE:
                return "────◯─►"
            else:
                return "────►"
        else:
            if edge_type == EdgeType.BOTH:
                return "---->"
            elif edge_type == EdgeType.LOCAL_ONLY:
                return "---L>"
            elif edge_type == EdgeType.REMOTE_ONLY:
                return "---R>"
            elif edge_type == EdgeType.CONFLICT:
                return "====>"
            elif edge_type == EdgeType.CYCLE:
                return "---O->"
            else:
                return "---->"

    def _get_node_label(self, node: Any) -> str:
        """Get a readable label for a node."""
        if hasattr(node, 'invariant_path'):
            path = node.invariant_path()
            # Extract just the task/object name
            if '/' in path:
                return path.split('/')[-1]
            return path
        elif hasattr(node, '__str__'):
            return str(node)
        else:
            return repr(node)

    def visualize_simple_dag(self, dag: nx.DiGraph, title: str = "DAG") -> str:
        """
        Create a simple visualization of a single DAG.

        Args:
            dag: The DAG to visualize
            title: Title for the visualization

        Returns:
            ASCII/Unicode visualization string
        """
        output = []
        output.append("=" * 80)
        output.append(title)
        output.append("=" * 80)
        output.append("")

        # Generate topological layout
        try:
            topological_order = list(nx.topological_sort(dag))
            layers = self._assign_layers(dag, topological_order)

            output.append("Topological layers:")
            output.append("")

            for layer_idx, layer_nodes in enumerate(layers):
                output.append(f"Layer {layer_idx + 1}:")
                for node in layer_nodes:
                    label = self._get_node_label(node)
                    output.append(f"  [{label}]")

                    # Show successors
                    for succ in dag.successors(node):
                        succ_label = self._get_node_label(succ)
                        if self.use_unicode:
                            output.append(f"    ────► [{succ_label}]")
                        else:
                            output.append(f"    ----> [{succ_label}]")
                output.append("")

        except nx.NetworkXUnfeasible:
            output.append("ERROR: Graph contains cycles (not a valid DAG)")
            output.append("")

            # Show cycles
            try:
                cycles = list(nx.simple_cycles(dag))
                output.append(f"Found {len(cycles)} cycle(s):")
                for i, cycle in enumerate(cycles, 1):
                    cycle_str = " -> ".join(self._get_node_label(n) for n in cycle)
                    output.append(f"  Cycle {i}: {cycle_str} -> {self._get_node_label(cycle[0])}")
            except nx.NetworkXNoCycle:
                output.append("(No cycles detected but topological sort failed)")

        # Basic statistics
        output.append("")
        output.append("STATISTICS:")
        output.append(f"  Nodes: {dag.number_of_nodes()}")
        output.append(f"  Edges: {dag.number_of_edges()}")
        output.append(f"  Is DAG: {nx.is_directed_acyclic_graph(dag)}")

        return '\n'.join(output)

    def highlight_conflicts(self, conflicts: List[Dict]) -> str:
        """
        Create a focused visualization of specific conflicts.

        Args:
            conflicts: List of conflict dictionaries

        Returns:
            Conflict-focused visualization
        """
        output = []
        output.append("=" * 80)
        output.append("CONFLICT HIGHLIGHTS")
        output.append("=" * 80)
        output.append("")

        for i, conflict in enumerate(conflicts, 1):
            output.append(f"Conflict {i}: {conflict.get('type', 'unknown')}")
            output.append(f"  {conflict.get('description', 'No description')}")
            output.append("")

            # Try to extract node information
            if 'local' in conflict and 'remote' in conflict:
                local = conflict['local']
                remote = conflict['remote']

                if isinstance(local, (list, tuple)) and isinstance(remote, (list, tuple)):
                    output.append("  Local changes:")
                    for item in local:
                        output.append(f"    • {item}")
                    output.append("  Remote changes:")
                    for item in remote:
                        output.append(f"    • {item}")
                elif isinstance(local, dict) and isinstance(remote, dict):
                    output.append("  Differences:")
                    all_keys = set(local.keys()) | set(remote.keys())
                    for key in all_keys:
                        if key in local and key in remote and local[key] != remote[key]:
                            output.append(f"    {key}: local='{local[key]}', remote='{remote[key]}'")
                        elif key in local and key not in remote:
                            output.append(f"    {key}: local='{local[key]}', remote=<missing>")
                        elif key not in local and key in remote:
                            output.append(f"    {key}: local=<missing>, remote='{remote[key]}'")
                else:
                    output.append(f"  Local: {local}")
                    output.append(f"  Remote: {remote}")

            output.append("")

        return '\n'.join(output)