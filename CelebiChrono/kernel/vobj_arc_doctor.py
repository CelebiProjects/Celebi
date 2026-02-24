""" Doctor methods for ArcManagement mixin.
"""
from logging import getLogger
from typing import TYPE_CHECKING

import networkx as nx

from ..utils import csys
from .vobj_core import Core
from .chern_cache import ChernCache

if TYPE_CHECKING:
    from .vobject import VObject

CHERN_CACHE = ChernCache.instance()
logger = getLogger("ChernLogger")


class ArcManagementDoctor(Core):
    """ Doctor methods for arc management.
    """
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
                    print("Removing arc and alias...")
                    print(f"Removing arc from {pred_object} to {obj}")
                    print(f"Removing alias {obj.path_to_alias(pred_object.path)}")
                    obj.remove_arc_from(pred_object, single=True)
                    print("Remove finished")
                    obj.remove_alias(obj.path_to_alias(pred_object.path))
                    # obj.impress()

    def doctor_successor(self, obj):
        """ Doctor the successors of the object
        """
        for succ_object in obj.successors():
            print(f"Checking successor {succ_object} of {obj}")
            print(f"Is zombie: {succ_object.is_zombie()}")
            print(f"Has predecessor: {succ_object.has_predecessor(obj)}")
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
            if not obj.path_to_alias(pred_object.invariant_path()) and \
                    not pred_object.is_algorithm():
                print(f"The input {pred_object} of {obj} does not have an alias, "
                      f"it will be removed.")
                choice = input(
                    "Would you like to remove the input or the algorithm? [Y/N]: "
                    )
                if choice.upper() == "Y":
                    obj.remove_arc_from(pred_object)
                    # obj.impress()

    def doctor_path_to_alias(self, obj):
        """ Doctor the alias of the object recursively
        """
        path_to_alias = obj.config_file.read_variable("path_to_alias", {})
        # project_path = self.project_path()
        project_path = CHERN_CACHE.project_path \
                if CHERN_CACHE.project_path \
                else CHERN_CACHE.use_and_cache_project_path(csys.project_path())
        for path in path_to_alias.keys():
            pred_obj = self.get_vobject(f"{project_path}/{path}", project_path)
            if not obj.has_predecessor(pred_obj):
                print("There seems to be a zombie alias to")
                print(f"{pred_obj} in {obj}")
                choice = input("Would you like to remove it? [Y/N]: ")
                if choice.upper() == "Y":
                    obj.remove_alias(obj.path_to_alias(path))

    # ----------------------------------------------------------------------
    # MERGE-SPECIFIC VALIDATION METHODS
    # ----------------------------------------------------------------------

    def validate_merge(  # pylint: disable=too-many-locals
        self,
        local_dag=None,
        remote_dag=None,
        base_dag=None,
    ):
        """
        Validate that a merge result maintains DAG consistency.

        Args:
            local_dag: Optional local branch DAG for comparison
            remote_dag: Optional remote branch DAG for comparison
            base_dag: Optional base ancestor DAG for comparison

        Returns:
            Tuple of (is_valid, issues, conflicts)
        """
        from .vobj_arc_merge import DAGMerger

        issues = []
        conflicts = []

        # Build current DAG (filter to dependency edges only)
        current_dag = self.build_dependency_dag()  # pylint: disable=no-member
        dep_edges = [
            (u, v) for u, v, data in current_dag.edges(data=True)
            if data.get('type') == 'dependency'
        ]
        dep_dag = nx.DiGraph()
        dep_dag.add_nodes_from(current_dag.nodes())
        dep_dag.add_edges_from(dep_edges)

        # Check for cycles
        try:
            nx.find_cycle(dep_dag, orientation='original')
            issues.append("DAG contains cycles after merge")
        except nx.NetworkXNoCycle:
            pass  # Good - no cycles

        # Check for missing node references
        for u, v in dep_dag.edges():
            if u not in dep_dag.nodes():
                issues.append(f"Edge source node missing: {u}")
            if v not in dep_dag.nodes():
                issues.append(f"Edge target node missing: {v}")

        # If we have comparison DAGs, check for merge-specific issues
        if local_dag and remote_dag and base_dag:
            merger = DAGMerger()
            merged_dag = merger.merge_dags(local_dag, remote_dag, base_dag)

            # Compare with current DAG
            current_edges = set(dep_dag.edges())
            merged_edges = set(merged_dag.edges())

            extra_edges = current_edges - merged_edges
            missing_edges = merged_edges - current_edges

            if extra_edges:
                issues.append(f"Extra edges in current DAG: {extra_edges}")
            if missing_edges:
                issues.append(f"Missing edges in current DAG: {missing_edges}")

            # Get conflicts from merger
            for conflict in merger.get_conflicts():
                conflicts.append({
                    'type': conflict.conflict_type.value,
                    'description': conflict.description,
                    'local': conflict.local_data,
                    'remote': conflict.remote_data
                })

        is_valid = not issues

        return is_valid, issues, conflicts

    def repair_merge_conflicts(
        self,
        conflicts=None,
        strategy="interactive",
    ):
        """
        Repair merge conflicts in the current project.

        Args:
            conflicts: Optional list of conflicts to repair
            strategy: Repair strategy ("interactive", "auto", "local", "remote")

        Returns:
            Tuple of (repaired_count, remaining_conflicts)
        """
        if not conflicts:
            # For now, just validate
            is_valid, issues, _ = self.validate_merge()
            if not is_valid:
                print(f"Found {len(issues)} issues:")
                for issue in issues:
                    print(f"  - {issue}")

                if strategy == "interactive":
                    choice = input("Attempt automatic repair? [Y/N]: ")
                    if choice.upper() == "Y":
                        return self._auto_repair_issues(issues)
                elif strategy == "auto":
                    return self._auto_repair_issues(issues)

            return 0, []

        # Repair specific conflicts
        repaired = 0
        remaining = []

        for conflict in conflicts:
            description = conflict.get('description', 'Unknown conflict')

            print(f"\nConflict: {description}")

            if strategy == "interactive":
                print("Resolution options:")
                # For now, just log the conflict
                print("  (Manual resolution required)")
                remaining.append(conflict)
            elif strategy == "auto":
                # Attempt automatic repair based on conflict type
                if self._auto_repair_conflict(conflict):
                    repaired += 1
                else:
                    remaining.append(conflict)
            else:
                remaining.append(conflict)

        return repaired, remaining

    def reconcile_arc_relations(self, verbose: bool = False):  # pylint: disable=too-many-locals
        """
        Rebuild and reconcile predecessor/successor links across all objects.

        This method:
        - Removes links to missing objects
        - Ensures successor/predecessor lists are symmetric
        - Deduplicates and stabilizes ordering

        Returns:
            Dict with counts of updates performed.
        """
        objects = [obj for obj in self.sub_objects_recursively()
                   if obj.is_task_or_algorithm()]
        obj_by_path = {obj.invariant_path(): obj for obj in objects}

        edges_before = set()
        edges = set()
        missing_refs = 0
        for obj in objects:
            obj_path = obj.invariant_path()
            pred_list = obj.config_file.read_variable("predecessors", [])
            succ_list = obj.config_file.read_variable("successors", [])

            for pred in pred_list:
                edges_before.add((pred, obj_path))
                if pred in obj_by_path:
                    edges.add((pred, obj_path))
                else:
                    missing_refs += 1
            for succ in succ_list:
                edges_before.add((obj_path, succ))
                if succ in obj_by_path:
                    edges.add((obj_path, succ))
                else:
                    missing_refs += 1

        update_counts = {
            "predecessors_updated": 0,
            "successors_updated": 0,
            "missing_refs": missing_refs,
            "edges_before": len(edges_before),
            "edges_after": len(edges),
        }

        for obj in objects:
            obj_path = obj.invariant_path()
            new_preds = sorted({u for (u, v) in edges if v == obj_path})
            new_succs = sorted({v for (u, v) in edges if u == obj_path})

            old_preds = obj.config_file.read_variable("predecessors", [])
            old_succs = obj.config_file.read_variable("successors", [])

            if old_preds != new_preds:
                obj.config_file.write_variable("predecessors", new_preds)
                update_counts["predecessors_updated"] += 1
            if old_succs != new_succs:
                obj.config_file.write_variable("successors", new_succs)
                update_counts["successors_updated"] += 1

        if verbose:
            print("Dag reconciliation:")
            print(f"  edges before: {update_counts['edges_before']}")
            print(f"  edges after:  {update_counts['edges_after']}")
            print(f"  missing refs: {update_counts['missing_refs']}")
            print(f"  preds updated: {update_counts['predecessors_updated']}")
            print(f"  succs updated: {update_counts['successors_updated']}")

        return update_counts

    def _auto_repair_issues(self, issues):
        """Attempt automatic repair of validation issues."""
        repaired = 0
        remaining = []

        for issue in issues:
            print(f"\nAttempting to repair: {issue}")

            # Simple heuristics for common issues
            if "contains cycles" in issue:
                if self._attempt_cycle_repair():
                    repaired += 1
                else:
                    remaining.append(issue)
            elif "node missing" in issue:
                # Extract node name from issue message
                # This is a simplified approach
                print("  (Manual repair required for missing nodes)")
                remaining.append(issue)
            else:
                remaining.append(issue)

        return repaired, remaining

    def _attempt_cycle_repair(self):
        """Attempt to repair cycles in the DAG."""
        current_dag = self.build_dependency_dag()  # pylint: disable=no-member

        try:
            cycles = list(nx.simple_cycles(current_dag))
        except nx.NetworkXNoCycle:
            return True  # No cycles found

        print(f"Found {len(cycles)} cycle(s)")

        # Simple heuristic: remove the last edge in each cycle
        for cycle in cycles:
            if len(cycle) >= 2:
                u = cycle[-2]
                v = cycle[-1]
                print(f"  Removing edge {u} -> {v} to break cycle")

                # This would need actual edge removal logic
                # For now, just report
                print("  (Edge removal not implemented in this prototype)")

        return False  # Not actually repaired in this prototype

    def _auto_repair_conflict(self, conflict):
        """Attempt automatic repair of a specific conflict."""
        conflict_type = conflict.get('type')

        # Simple heuristics for automatic repair
        if conflict_type == "additive_edge":
            # Keep additive edges
            return True
        if conflict_type == "subtractive_edge":
            # Keep edge (don't remove)
            return True
        if conflict_type == "contradictory_edge":
            # Use union strategy
            return True
        return False
