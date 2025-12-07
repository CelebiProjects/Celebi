""" The module for arc management of VObject
"""
import os
import re
from collections import defaultdict
from itertools import combinations
from logging import getLogger
from os.path import join
from time import time

import networkx as nx

from ..utils import csys
from .vobj_core import Core
from .chern_cache import ChernCache

CHERN_CACHE = ChernCache.instance()
logger = getLogger("ChernLogger")


class ArcManagement(Core):
    """ The class for arc management of VObject
    """

    def add_arc_from(self, obj):
        """
        Add a link from the object contained in `path` to this object.

        Example:
            o  --*--> (o) ----> o
           (o) --*-->  o

        Args:
            obj: The object to link from.
        """
        succ_str = obj.config_file.read_variable("successors", [])
        succ_str.append(self.invariant_path())
        obj.config_file.write_variable("successors", succ_str)

        pred_str = self.config_file.read_variable("predecessors", [])
        pred_str.append(obj.invariant_path())
        self.config_file.write_variable("predecessors", pred_str)

    def remove_arc_from(self, obj, single=False):
        """
        Remove a link from the object contained in `path`.

        If `single` is set to True, only remove the arc in this object.
        If `single` is set to False, remove the arc globally.

        Example:
            o  --X--> (o) ----> o  (Remove this arc)
           (o) --X-->  o

        Args:
            obj: The object to unlink from.
            single (bool): Whether to remove the arc only in this object.
        """
        if not single:
            config_file = obj.config_file
            succ_str = config_file.read_variable("successors", [])
            succ_str.remove(self.invariant_path())
            config_file.write_variable("successors", succ_str)

        pred_str = self.config_file.read_variable("predecessors", [])
        pred_str.remove(obj.invariant_path())
        self.config_file.write_variable("predecessors", pred_str)

    def add_arc_to(self, obj):
        """
        Add a link from this object to the object contained in `path`.

        Example:
            o  -----> (o) --*-->  o
                       o  --*--> (o)

        Args:
            obj: The object to link to.
        """
        pred_str = obj.config_file.read_variable("predecessors", [])
        pred_str.append(self.invariant_path())
        obj.config_file.write_variable("predecessors", pred_str)

        succ_str = self.config_file.read_variable("successors", [])
        succ_str.append(obj.invariant_path())
        self.config_file.write_variable("successors", succ_str)

    def remove_arc_to(self, obj, single=False):
        """
        Remove a link to the object contained in `path`.

        If `single` is set to True, only remove the arc in this object.
        If `single` is set to False, remove the arc globally.

        Example:
            o  -----> (o) --X-->  o  (Remove this arc)
                       o  --X--> (o)

        Args:
            obj: The object to unlink from.
            single (bool): Whether to remove the arc only in this object.
        """
        if not single:
            config_file = obj.config_file
            pred_str = config_file.read_variable("predecessors", [])
            pred_str.remove(self.invariant_path())
            config_file.write_variable("predecessors", pred_str)

        succ_str = self.config_file.read_variable("successors", [])
        succ_str.remove(obj.invariant_path())
        self.config_file.write_variable("successors", succ_str)

    def successors(self):
        """ The successors of the current object
        Return a list of [object]
        """
        succ_str = self.config_file.read_variable("successors", [])
        successors = []
        project_path = self.project_path()
        for path in succ_str:
            successors.append(self.get_vobject(f"{project_path}/{path}"))
        return successors

    def predecessors(self):
        """ The predecessosr of the current object
        Return a list of [object]
        """
        pred_str = self.config_file.read_variable("predecessors", [])
        predecessors = []
        project_path = self.project_path()
        for path in pred_str:
            predecessors.append(self.get_vobject(f"{project_path}/{path}"))
        return predecessors

    def has_successor(self, obj): # UnitTest: DONE
        """ Judge whether the object has the specific successor
        """
        succ_str = self.config_file.read_variable("successors", [])
        return obj.invariant_path() in succ_str

    def has_predecessor(self, obj): # UnitTest: DONE
        """ Judge whether the object has the specific predecessor
        """
        pred_str = self.config_file.read_variable("predecessors", [])
        return obj.invariant_path() in pred_str

    def has_predecessor_recursively(self, obj): # UnitTest: DONE
        """ Judge whether the object has the specific predecessor recursively
        """
        # The object itself is the predecessor of itself
        if self.invariant_path() == obj.invariant_path():
            return True

        pred_str = self.config_file.read_variable("predecessors", [])
        if obj.invariant_path() in pred_str:
            return True
        # Use cache to avoid infinite loop
        consult_table = CHERN_CACHE.predecessor_consult_table
        (last_consult_time, has_predecessor) = consult_table.get(
            self.path, (-1, False)
        )
        now = time()
        if now - last_consult_time < 1:
            return has_predecessor

        modification_time = csys.dir_mtime(self.project_path())
        if modification_time < last_consult_time:
            return has_predecessor

        for pred_path in pred_str:
            project_path = self.project_path()
            pred_obj = self.get_vobject(f"{project_path}/{pred_path}")
            if pred_obj.has_predecessor_recursively(obj):
                consult_table[self.path] = (time(), True)
                return True
        consult_table[self.path] = (time(), False)
        return False

    def doctor(self):
        """ Try to exam and fix the repository.
        """
        queue = self.sub_objects_recursively()
        for obj in queue:
            if not obj.is_task_or_algorithm():
                continue

            self.doctor_predecessor(obj)
            self.doctor_successor(obj)
            self.doctor_alias(obj)
            self.doctor_path_to_alias(obj)

    def doctor_predecessor(self, obj):
        """ Doctor the predecessors of the object
        """
        for pred_object in obj.predecessors():
            if pred_object.is_zombie() or \
                    not pred_object.has_successor(obj):
                print(f"The predecessor \n\t {pred_object} \n\t "
                      f"does not exist or does not have a link "
                      f"to object {obj}")
                choice = input(
                    "Would you like to remove the input or the algorithm? "
                    "[Y/N]: "
                )
                if choice.upper() == "Y":
                    obj.remove_arc_from(pred_object, single=True)
                    obj.remove_alias(obj.path_to_alias(pred_object.path))
                    obj.impress()


    def doctor_successor(self, obj):
        """ Doctor the successors of the object
        """
        for succ_object in obj.successors():
            if succ_object.is_zombie() or \
                    not succ_object.has_predecessor(obj):
                print("The successor")
                print(f"\t {succ_object}")
                print(f"\t does not exist or does not have a link to object {obj}")
                choice = input("Would you like to remove the output? [Y/N]")
                if choice == "Y":
                    obj.remove_arc_to(succ_object, single=True)

    def doctor_alias(self, obj):
        """ Doctor the alias of the object
        """
        for pred_object in obj.predecessors():
            if obj.path_to_alias(pred_object.invariant_path()) == "" and \
                    not pred_object.is_algorithm():
                print(f"The input {pred_object} of {obj} does not have an alias, "
                      f"it will be removed.")
                choice = input(
                    "Would you like to remove the input or the algorithm? [Y/N]: "
                    )
                if choice.upper() == "Y":
                    obj.remove_arc_from(pred_object)
                    obj.impress()

    def doctor_path_to_alias(self, obj):
        """ Doctor the alias of the object recursively
        """
        path_to_alias = obj.config_file.read_variable("path_to_alias", {})
        for path in path_to_alias.keys():
            project_path = self.project_path()
            pred_obj = self.get_vobject(f"{project_path}/{path}")
            if not obj.has_predecessor(pred_obj):
                print("There seems to be a zombie alias to")
                print(f"{pred_obj} in {obj}")
                choice = input("Would you like to remove it? [Y/N]: ")
                if choice.upper() == "Y":
                    obj.remove_alias(obj.path_to_alias(path))

    def add_input(self, path, alias):
        """ add input
        """
        if not self.is_task_or_algorithm():
            print(f"You are adding input to {self.object_type()} type object. "
                  "The input is required to be a task or an algorithm.")
            return

        obj = self.get_vobject(path)
        if obj.object_type() != self.object_type():
            print(f"You are adding {obj.object_type()} type object as"
                   " input. The input is required to be a {self.object_type()}.")
            return

        if obj.has_predecessor_recursively(self):
            print("The object is already in the dependency diagram of "
                  "the ``input'', which will cause a loop.")
            return

        # if the obj is already an input, reject to add it
        if self.has_predecessor(obj):
            print("The input already exists.")
            return

        if self.has_alias(alias):
            print("The alias already exists. "
                  "The original input and alias will be replaced.")
            project_path = self.project_path()
            original_object = self.get_vobject(
                join(project_path, self.alias_to_path(alias))
            )
            self.remove_arc_from(original_object)
            self.remove_alias(alias)

        self.add_arc_from(obj)
        self.set_alias(alias, obj.invariant_path())

    def remove_input(self, alias):
        """ Remove the input """
        path = self.alias_to_path(alias)
        if path == "":
            print("Alias not found")
            return
        project_path = self.project_path()
        obj = self.get_vobject(join(project_path, path))
        self.remove_arc_from(obj)
        self.remove_alias(alias)

    # def build_dependency_dag(self, exclude_algorithms=False):
    #     """
    #     Builds a NetworkX Directed Acyclic Graph (DAG) containing this object
    #     and all its recursive predecessors.

    #     Nodes in the graph are the VObject objects themselves.
    #     Edges represent the dependency (predecessor -> successor).

    #     Args:
    #         exclude_algorithms (bool): If True, VObjects of type "algorithm"
    #                                    will be excluded from the resulting DAG.

    #     Returns:
    #         nx.DiGraph: The NetworkX DAG representing the dependency graph.
    #     """
    #     G = nx.DiGraph()

    #     # Use a queue for a controlled graph traversal (Breadth-First Search)
    #     # to find all unique predecessors.
    #     # queue = [self]
    #     sub_objects = self.sub_objects_recursively()
    #     queue = [s for s in sub_objects if s.object_type() == "task"]
    #     visited = {s.invariant_path() : s for s in queue}
    #     for s in queue:
    #         G.add_node(s)

    #     # Add the starting node (self)
    #     # if not (exclude_algorithms and self.is_algorithm()):
    #     #   G.add_node(self)

    #     while queue:
    #         current_obj = queue.pop(0)

    #         # If the current node is an excluded algorithm type, skip its processing
    #         # but still process its predecessors if they haven't been visited.
    #         if exclude_algorithms and current_obj.is_algorithm():
    #             # Process predecessors only to find other non-algorithm nodes
    #             # connected further up the chain, but don't add current_obj or its edges.
    #             for pred_obj in current_obj.predecessors():
    #                 pred_path = pred_obj.invariant_path()
    #                 if pred_path not in visited:
    #                     visited[pred_path] = pred_obj
    #                     queue.append(pred_obj)
    #             continue

    #         # Standard processing for non-excluded nodes

    #         # Check if current_obj is in the graph (it should be, unless it's the
    #         # starting node and was excluded, but we checked that above).
    #         if current_obj not in G:
    #              G.add_node(current_obj) # Add if it somehow got here without being added

    #         for pred_obj in current_obj.predecessors():
    #             pred_path = pred_obj.invariant_path()

    #             # Apply the exclusion rule for the predecessor
    #             is_excluded = exclude_algorithms and pred_obj.is_algorithm()

    #             # Add the predecessor to the queue for traversal if not visited
    #             if pred_path not in visited:
    #                 visited[pred_path] = pred_obj
    #                 queue.append(pred_obj)

    #             # Add the predecessor node and the dependency edge only if the
    #             # predecessor is NOT excluded.
    #             if not is_excluded:
    #                 if pred_obj not in G:
    #                     G.add_node(pred_obj)

    #                 # Add the edge: Predecessor (source) -> Successor (target)
    #                 G.add_edge(pred_obj, current_obj)

    #     return G

    # ----------------------------------------------------------------------
    # HELPER METHOD: NODE AGGREGATION
    # ----------------------------------------------------------------------

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
                continue # Only aggregate groups with 2 or more nodes

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
