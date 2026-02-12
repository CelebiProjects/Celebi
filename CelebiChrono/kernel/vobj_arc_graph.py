""" Graph building methods for ArcManagement mixin.
"""
import os
import re
from collections import defaultdict
from itertools import combinations
from logging import getLogger

import networkx as nx

from .vobj_core import Core
from .chern_cache import ChernCache

CHERN_CACHE = ChernCache.instance()
logger = getLogger("ChernLogger")


class ArcManagementGraph(Core):
    """ Graph building methods for arc management.
    """
    # pylint: disable=too-many-locals
    def _aggregate_sequential_nodes(self, graph):
        """
        Aggregates nodes like 'path/task_0', 'path/task_1', ... into 'path/task_[0..N]'.
        This logic should be defined as a method of the same class as build_dependency_dag.
        """

        # Matches patterns like 'prefix_number' or 'prefix_number.ext'
        _sequential_pattern = re.compile(r'^(.*?)_(\d+)(\..*)?$')

        groups = defaultdict(lambda: {'nodes': [], 'indices': []})

        # 1. Group nodes by prefix
        for node in list(graph.nodes()):
            path = node.invariant_path() if hasattr(node, 'invariant_path') else str(node)
            match = _sequential_pattern.match(path)

            if match:
                prefix = match.group(1) + '_'
                index = int(match.group(2))

                # Grouping key should include the directory path
                group_key = os.path.dirname(path) + ":" + prefix

                groups[group_key]['nodes'].append(node)
                groups[group_key]['indices'].append(index)

        # 2. Process groups and aggregate
        for group_key, data in groups.items():
            if len(data['nodes']) < 2:
                continue  # Only aggregate groups with 2 or more nodes

            min_idx = min(data['indices'])
            max_idx = max(data['indices'])

            prefix_path = data['nodes'][0].invariant_path()
            prefix = prefix_path[:prefix_path.rfind('_') + 1]

            new_name = f"{prefix}[{min_idx}..{max_idx}]"
            new_node_id = f"AGGREGATE:{new_name}"

            # Get a representative path for spatial grouping
            representative_path = data['nodes'][0].invariant_path()

            # 3. Add the aggregated node
            graph.add_node(new_node_id,
                       node_type='aggregate',
                       label=new_name,
                       aggregated_path=representative_path)

            # 4. Remap Edges
            predecessors_to_add = set()
            successors_to_add = set()

            for node_to_remove in data['nodes']:
                # Collect unique neighbors, excluding the new aggregated node itself
                preds = [p for p in graph.predecessors(node_to_remove)
                         if p != new_node_id]
                predecessors_to_add.update(preds)
                succs = [s for s in graph.successors(node_to_remove)
                         if s != new_node_id]
                successors_to_add.update(succs)

                graph.remove_node(node_to_remove)

            # 5. Add new dependency edges to the aggregate node
            for pred in predecessors_to_add:
                graph.add_edge(pred, new_node_id, weight=1.0, type='dependency')

            for succ in successors_to_add:
                graph.add_edge(new_node_id, succ, weight=1.0, type='dependency')

        return graph

    # ----------------------------------------------------------------------
    # CORE METHOD: GRAPH CONSTRUCTION
    # ----------------------------------------------------------------------

    # pylint: disable=too-many-locals,too-many-branches
    def build_dependency_dag(self, exclude_algorithms=False):
        """
        Builds a NetworkX DiGraph optimized for visualization.
        """
        graph = nx.DiGraph()

        # --- 1. Standard Graph Traversal (with Canonical Node Tracking) ---
        sub_objects = self.sub_objects_recursively()
        queue = [s for s in sub_objects if s.object_type() == "task"]

        # Use visited as the canonical node registry (key=path, value=unique object instance)
        visited = {s.invariant_path(): s for s in queue}
        for s in queue:
            graph.add_node(s)

        while queue:
            current_obj = queue.pop(0)

            # Exclude algorithms logic (omitted for brevity)
            if exclude_algorithms and current_obj.is_algorithm():
                for pred_obj in current_obj.predecessors():
                    pred_path = pred_obj.invariant_path()
                    if pred_path not in visited:
                        visited[pred_path] = pred_obj
                        queue.append(pred_obj)
                continue

            for pred_obj in current_obj.predecessors():
                pred_path = pred_obj.invariant_path()
                is_excluded = exclude_algorithms and pred_obj.is_algorithm()

                if pred_path not in visited:
                    # Node instance is new; register it and add to queue
                    visited[pred_path] = pred_obj
                    queue.append(pred_obj)
                else:
                    # Use the existing, canonical object instance for this path
                    pred_obj = visited[pred_path]

                if not is_excluded:
                    if pred_obj not in graph:
                        graph.add_node(pred_obj)

                    # Add standard dependency (weight=1)
                    graph.add_edge(pred_obj, current_obj, weight=1.0, type='dependency')

        # --- 1.5. NODE AGGREGATION ---
        graph = self._aggregate_sequential_nodes(graph)

        # --- 2. Calculate Spatial Weights (Clustering) ---
        dir_groups = defaultdict(list)
        for node in graph.nodes():
            p = getattr(node, 'path', None)
            if not p:
                if hasattr(node, 'invariant_path'):
                    p = node.invariant_path()
                else:
                    p = str(node)

            # Handle Aggregated Node path retrieval
            if isinstance(p, str) and p.startswith("AGGREGATE:"):
                if graph.nodes[node].get('aggregated_path'):
                    agg_path = graph.nodes[node]['aggregated_path']
                    dir_groups[os.path.dirname(agg_path)].append(node)
                continue

            if p:
                dir_groups[os.path.dirname(p)].append(node)

        # Create 'sibling' cliques for clustering
        for siblings in dir_groups.values():
            if len(siblings) < 2:
                continue
            for node_u, node_v in combinations(siblings, 2):
                if graph.has_edge(node_u, node_v):
                    # Reinforce existing dependency
                    graph[node_u][node_v]['weight'] = 10.0
                elif graph.has_edge(node_v, node_u):
                    # Reinforce existing dependency
                    graph[node_v][node_u]['weight'] = 10.0
                else:
                    # Add high-weight 'sibling' edge for layout clustering
                    graph.add_edge(node_u, node_v, weight=10.0,
                                   type='sibling', style='dashed')

        return graph