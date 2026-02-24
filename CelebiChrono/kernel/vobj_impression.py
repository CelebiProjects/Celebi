""" Module for impression management
"""
import difflib
import os

import filecmp
import time
from logging import getLogger

from ..utils import csys
from ..utils.csys import colorize_diff
from ..utils.format_utils import format_node_display
from ..utils.message import Message
from .vobj_core import Core
from .vimpression import VImpression
from .chern_cache import ChernCache

CHERN_CACHE = ChernCache.instance()
logger = getLogger("ChernLogger")


class ImpressionManagement(Core):
    """ Class for impression management
    """
    def impress(self, consult_id = None): # UnitTest: DONE
        """ Create an impression.
        The impressions are store in a directory .celebi/impressions/[uuid]
        It is organized as following:
            [uuid]
            |------ contents
            |------ config.json
        In the config.json, the tree of the contents as well as
        the dependencies are stored.
        The object_type is also saved in the json file.
        The tree and the dependencies are sorted via name.
        """
        # start_time = time()
        now = time.time()
        if consult_id is None:
            consult_id = now
        else:
            now = consult_id
        logger.debug("VObject impress: %s", self.path)
        object_type = self.object_type()
        if object_type not in ("task", "algorithm"):
            sub_objects = self.sub_objects()
            for sub_object in sub_objects:
                sub_object.impress(now)
            return
        logger.debug("Check whether it is impressed with is_impressed_fast")

        if self.is_impressed_fast(now):
            logger.warning("Already impressed: %s", self.path)
            return
        for pred in self.predecessors():
            if not pred.is_impressed_fast(now):
                pred.impress(now)
        # print(f"Time used for impressing predecessors: {time() - start_time:.6f} seconds")
        impression = VImpression()
        impression.update_uuid(self)
        # print(f"Time used for update_uuid: {time() - start_time:.6f} seconds")
        impression.create(self)
        # print(f"Time used for creating impression: {time() - start_time:.6f} seconds")
        self.config_file.write_variable("impression", impression.uuid)
        # update the impression_consult_table, since the impression is changed
        consult_table = CHERN_CACHE.impression_consult_table
        consult_table[self.path] = (now, True)

    def is_impressed(self, consult_id = None): # pylint: disable=too-many-return-statements, too-many-locals, too-many-branches # UnitTest: DONE
        """ Judge whether the file is impressed
        """
        now = time.time()
        # print(consult_id)
        if consult_id is None:
            consult_id = now
        else:
            now = consult_id
        # count = CHERN_CACHE.count
        # print("Impression check count: ", count, " Time: ", now)
        # CHERN_CACHE.count = count + 1
        logger.debug("VObject is_impressed in %s", self.path)
        # Check whether there is an impression already
        impression = self.impression()

        logger.debug("Impression: %s", impression)
        if impression is None or impression.is_zombie():
            # print("No impression or impression is zombie")
            return False

        # impression_count = CHERN_CACHE.impression_check_count.get(
        #     impression.uuid, 0
        #     )
        # CHERN_CACHE.impression_check_count[impression.uuid] = \
        #     impression_count + 1
        # print("Impression UUID check count:", impression.uuid,
        #       CHERN_CACHE.impression_check_count[impression.uuid])

        # print(f"Checking impression {impression.uuid}...")
        # print(f"Time used for getting impression: {time.time() - start_time:.6f} seconds")

        logger.debug("Check the predecessors is impressed or not")
        # Fast check whether it is impressed
        for pred in self.predecessors():
            if not pred.is_impressed_fast(now):
                # print("Predecessor not impressed:", pred.path)
                return False
        # print(f"Fast check done: {time.time() - start_time:.6f} seconds")

        self_pred_impressions_uuid = [x.uuid for x in self.pred_impressions()]
        impr_pred_impressions_uuid = [
            x.uuid for x in impression.pred_impressions()
        ]
        # Check whether the dependent impressions
        # are the same as the impressed things
        if self_pred_impressions_uuid != impr_pred_impressions_uuid:
            # print("Predecessor mismatch:")
            # print("Current preds:", self_pred_impressions_uuid)
            # print("Impression preds:", impr_pred_impressions_uuid)
            return False

        # print(f"Time used for checking predecessors: {time.time() - start_time:.6f} seconds")
        logger.debug("Check the file change")
        # start_time = time.time()
        # Check the file change: first to check the tree
        file_list = csys.tree_excluded(self.path)
        impression_tree = impression.tree()

        # Check the file list is the same as the impression tree
        # if file_list != impression.tree():
        #     return False
        # FIXME back-compatible patch
        # all the chern.yaml -> celebi.yaml in the impression tree

        # for i in range(len(impression_tree)):
        #     dirpath, dirnames, filenames = impression_tree[i]
        #     new_filenames = []
        #     for f in filenames:
        #         if f == "chern.yaml":
        #             new_filenames.append("celebi.yaml")
        #         else:
        #             new_filenames.append(f)
        #     impression_tree[i] = [dirpath, dirnames, new_filenames]

        if csys.sorted_tree(file_list) != csys.sorted_tree(impression_tree):
            # print("Tree mismatch:")
            # print("Current tree:", csys.sorted_tree(file_list))
            # print("Impression tree:", csys.sorted_tree(impression_tree))
            return False
        # print(f"Time used for checking tree: {time.time() - start_time:.6f} seconds")

        # FIXME Add the Unit Test for this part
        alias_to_path = self.config_file.read_variable("alias_to_path", {})
        for alias in alias_to_path.keys():
            if not impression.has_alias(alias):
                # print("Alias missing in impression:", alias)
                return False
            if not self.alias_to_impression(alias):
                # print("Alias missing in self:", alias)
                return False
            uuid1 = self.alias_to_impression(alias).uuid
            uuid2 = impression.alias_to_impression_uuid(alias)
            if uuid1 != uuid2:
                # print("Alias uuid mismatch:", alias, uuid1, uuid2)
                return False
        # print(f"Time used for checking aliases: {time.time() - start_time:.6f} seconds")

        try:
            impression_root = impression.materialize_contents()
        except FileNotFoundError:
            return False
        for dirpath, dirnames, filenames in file_list: # pylint: disable=unused-variable
            for f in filenames:
                current_file = f"{self.path}/{dirpath}/{f}"
                impression_file = f"{impression_root}/{dirpath}/{f}"
                if not filecmp.cmp(current_file, impression_file):
                    # print("# File difference:")
                    # print(f"cp {impression.path}/contents/{dirpath}/{f}",
                    #       f"{self.path}/{dirpath}/{f} ",
                    #       )
                    return False
        # print(f"Time used for checking file contents: {time.time() - start_time:.6f} seconds")
        return True

    def clean_impressions(self): # UnitTest: DONE
        """ Clean the impressions of the object,
        this is used only when it is copied to a new place and
        needed to remove impression information.
        """
        if not self.is_task_or_algorithm():
            sub_objects = self.sub_objects()
            for sub_object in sub_objects:
                sub_object.clean_impressions()
            return
        self.config_file.write_variable("impressions", [])
        self.config_file.write_variable("impression", "")
        self.config_file.write_variable("output_md5s", {})
        self.config_file.write_variable("output_md5", "")

    def clean_flow(self):
        """ Clean all the alias, predecessors and successors,
        this is used only when it is copied to a new place
        and needed to remove impression information.
        """
        self.config_file.write_variable("alias_to_path", {})
        self.config_file.write_variable("path_to_alias", {})
        self.config_file.write_variable("predecessors", [])
        self.config_file.write_variable("successors", [])

    def is_impressed_fast(self, consult_id = None): # UnitTest: DONE
        """ Judge whether the file is impressed, with timestamp
        """
        logger.debug("VObject is_impressed_fast")
        consult_table = CHERN_CACHE.impression_consult_table
        # FIXME cherncache should be replaced
        # by some function called like cache
        (last_consult_time, is_impressed) = consult_table.get(
            self.path, (-1, -1)
        )
        now, consult_id = csys.update_time(consult_id)
        # print("Cache: ", consult_table)
        if now - last_consult_time < 1:
            # If the last consult time is less than 1 second ago,
            # we can use the cache
            # But honestly, I don't remember why I set it to 1 second
            logger.debug("Time now: %lf", now)
            logger.debug("Last consult time: %lf", last_consult_time)
            return is_impressed
        modification_time_from_cache, modification_consult_time = \
                CHERN_CACHE.project_modification_time
        if modification_time_from_cache is None or now - modification_consult_time > 1:
            modification_time = csys.dir_mtime(self.project_path())
            CHERN_CACHE.project_modification_time = modification_time, now
        else:
            modification_time = modification_time_from_cache
        if modification_time < last_consult_time:
            return is_impressed
        is_impressed = self.is_impressed(now)
        # consult_table[self.path] = (time.time(), is_impressed)
        consult_table[self.path] = (now, is_impressed)
        return is_impressed

    def pred_impressions(self): # UnitTest: DONE
        """ Get the impression dependencies
        """
        # FIXME An assumption is that all the predcessor's are impressed,
        # if they are not, we should impress them first
        # Add check to this
        dependencies = []
        for pred in self.predecessors():
            dependencies.append(pred.impression())
        return sorted(dependencies, key=lambda x: x.uuid)

    def impression(self): # UnitTest: DONE
        """ Get the impression of the current object
        """
        uuid = self.config_file.read_variable("impression", "")
        if not uuid:
            return None
        return VImpression(uuid)

    def search_impression(self, partial_uuid: str) -> Message:
        """ Search for the impression of the current object
            This function will search for the impression
        """
        message = Message()
        project_path = self.project_path()
        impressions_path = f"{project_path}/.celebi/impressions"
        for uuid in os.listdir(impressions_path):
            if uuid.startswith(partial_uuid):
                message.add(f"Found impression {uuid}\n")
        return message

    def status(self, consult_id=None): # UnitTest: DONE
        """ Consult the status of the object
            There should be only two status locally: new|impressed
        """
        # If it is already asked, just give us the answer
        logger.debug("VTask status: Consulting status of %s", self.path)
        if consult_id:
            consult_table = CHERN_CACHE.status_consult_table
            cid, status = consult_table.get(self.path, (-1,-1))
            if cid == consult_id:
                return status

        if not self.is_task_or_algorithm():
            for sub_object in self.sub_objects():
                status = sub_object.status(consult_id)
                if status == "new":
                    return "new"
            return "impressed"

        if not self.is_impressed_fast():
            if consult_id:
                consult_table[self.path] = (consult_id, "new")
            return "new"

        # print("Fast impression check passed.")

        status = "impressed"
        if consult_id:
            consult_table[self.path] = (consult_id, status)
        return status

    # pylint: disable=too-many-locals,too-many-statements,too-many-branches
    def trace(self, impression=None) -> Message:
        """
        Compare the *current* dependency DAG of `self` with the DAG stored in
        a given impression (or the current impression if not provided).
        Return a Message with the differences.

        Output example:

            === DAG Node Differences ===
            Added nodes:   {uuid3}
            Removed nodes: {uuid7}

            === DAG Edge Differences ===
            Added edges:   {(uuid3 -> uuid1)}
            Removed edges: {(uuid7 -> uuid2)}

        """
        logger.debug("Tracing DAG differences for %s", self.path)
        message = Message()

        if impression is None:
            impression = self.impression()
        if impression is None:
            message.add("No impression exists. Object is NEW.", "warning")
            return message
        impression = VImpression(impression)

        # ---------------------------------------------
        # Build DAG from current object state
        # ---------------------------------------------
        def build_current_dag(obj, dag, visited):
            if obj in visited:
                return
            visited.add(obj)

            im = obj.impression()
            uid = im.uuid if im else None
            dag["nodes"].add(uid)

            for p in obj.predecessors():
                pim = p.impression()
                puid = pim.uuid if pim else None
                dag["nodes"].add(puid)
                dag["edges"].add((puid, uid))
                build_current_dag(p, dag, visited)

        current_dag = {"nodes": set(), "edges": set()}
        build_current_dag(self, current_dag, set())

        # ---------------------------------------------
        # Build DAG from stored impression
        # ---------------------------------------------
        def build_impression_dag(impr, dag, visited):
            if impr.uuid in visited:
                return
            visited.add(impr.uuid)

            dag["nodes"].add(impr.uuid)
            for p in impr.pred_impressions():
                dag["nodes"].add(p.uuid)
                dag["edges"].add((p.uuid, impr.uuid))
                build_impression_dag(p, dag, visited)

        stored_dag = {"nodes": set(), "edges": set()}
        build_impression_dag(impression, stored_dag, set())

        # ------------------------------------------------------
        # Compare nodes
        # ------------------------------------------------------
        added_nodes   = current_dag["nodes"] - stored_dag["nodes"]
        removed_nodes = stored_dag["nodes"] - current_dag["nodes"]

        # ------------------------------------------------------
        # Compare edges
        # ------------------------------------------------------
        added_edges   = current_dag["edges"] - stored_dag["edges"]
        removed_edges = stored_dag["edges"] - current_dag["edges"]

        def node_display(uuid):
            """Format node with short UUID and descriptor for readability."""
            if uuid is None:
                return "[NEW] (no impression yet)"
            impression_obj = VImpression(uuid)
            obj_type = impression_obj.object_type()
            descriptor = impression_obj.get_descriptor()
            return format_node_display(uuid, obj_type, descriptor)

        def edge_display(parent_uuid, child_uuid):
            """Format edge with descriptors for readability."""
            parent_impression = VImpression(parent_uuid)
            child_impression = VImpression(child_uuid)
            parent_display = format_node_display(
                parent_uuid,
                parent_impression.object_type(),
                parent_impression.get_descriptor(),
            )
            child_display = format_node_display(
                child_uuid,
                child_impression.object_type(),
                child_impression.get_descriptor(),
            )
            return f"{parent_display} → {child_display}"

        # ------------------------------------------------------
        # Pretty print
        # ------------------------------------------------------
        message.add("\n=== DAG Node Differences ===", "title0")

        if added_nodes:
            message.add(f"\nAdded nodes ({len(added_nodes)}):", "info")
            # Filter out None values before sorting (None can't be sorted with strings)
            for node in sorted([n for n in added_nodes if n is not None]):
                message.add(f"  • {node_display(node)}", "diff")
            # Handle None nodes separately if any exist
            none_nodes = [n for n in added_nodes if n is None]
            if none_nodes:
                message.add("  • [NEW] (no impression yet)", "diff")
        else:
            message.add("\nAdded nodes: none", "info")

        if removed_nodes:
            message.add(f"\nRemoved nodes ({len(removed_nodes)}):", "info")
            # Filter out None values before sorting (None can't be sorted with strings)
            for node in sorted([n for n in removed_nodes if n is not None]):
                message.add(f"  • {node_display(node)}", "diff")
            # Handle None nodes separately if any exist
            none_nodes = [n for n in removed_nodes if n is None]
            if none_nodes:
                message.add("  • [DELETED] (impression missing)", "diff")
        else:
            message.add("\nRemoved nodes: none", "info")

        message.add("\n=== DAG Edge Differences ===", "title0")

        if added_edges:
            message.add(f"\nAdded edges ({len(added_edges)}):", "info")
            # Filter out edges with None values before sorting (None can't be sorted with strings)
            valid_edges = [e for e in added_edges if e[0] is not None and e[1] is not None]
            for parent, child in sorted(valid_edges):
                message.add(f"  • {edge_display(parent, child)}", "diff")
            # Handle edges with None values separately
            none_edges = [e for e in added_edges if e[0] is None or e[1] is None]
            for parent, child in none_edges:
                parent_display = (
                    "[NEW]"
                    if parent is None
                    else node_display(parent)
                )
                child_display = (
                    "[NEW]"
                    if child is None
                    else node_display(child)
                )
                message.add(f"  • {parent_display} → {child_display}", "diff")
        else:
            message.add("\nAdded edges: none", "info")

        if removed_edges:
            message.add(f"\nRemoved edges ({len(removed_edges)}):", "info")
            # Filter out edges with None values before sorting (None can't be sorted with strings)
            valid_edges = [e for e in removed_edges if e[0] is not None and e[1] is not None]
            for parent, child in sorted(valid_edges):
                message.add(f"  • {edge_display(parent, child)}", "diff")
            # Handle edges with None values separately
            none_edges = [e for e in removed_edges if e[0] is None or e[1] is None]
            for parent, child in none_edges:
                parent_display = (
                    "[MISSING]"
                    if parent is None
                    else node_display(parent)
                )
                child_display = (
                    "[MISSING]"
                    if child is None
                    else node_display(child)
                )
                message.add(f"  • {parent_display} → {child_display}", "diff")
        else:
            message.add("\nRemoved edges: none", "info")

        # --------------------------------------------------------
        #  Check parent-child relationships between removed/added
        # --------------------------------------------------------
        message.add("\n=== Detailed Changes (Parent → Child) ===", "title0")


        def is_parent(parent_uuid, child_uuid):
            return parent_uuid in VImpression(child_uuid).parents()

        for r in removed_nodes:
            for a in added_nodes:
                if is_parent(r, a):
                    message.add(f"\nChange: {edge_display(r, a)}", "title1")

                    # --------------------------------------------------------
                    #  Run impression diff
                    # --------------------------------------------------------
                    old_impr = VImpression(r) if r else None
                    new_impr = VImpression(a) if a else None

                    if not (old_impr and new_impr):
                        message.add(
                            "One of the impressions does not exist, skipping diff.",
                            "warning",
                        )
                        continue

                    old_root = old_impr.materialize_contents()
                    new_root = new_impr.materialize_contents()

                    # Compare file lists (sorted, relative paths)
                    old_files = csys.get_files_in_directory(old_root)
                    new_files = csys.get_files_in_directory(new_root)


                    old_files_set = set(old_files)
                    new_files_set = set(new_files)

                    common = old_files_set & new_files_set
                    removed_files = old_files_set - new_files_set
                    added_files   = new_files_set - old_files_set

                    if added_files:
                        message.add(f"  Added files ({len(added_files)}):", "info")
                        for file in sorted(added_files):
                            message.add(f"    • {file}", "diff")
                    if removed_files:
                        message.add(f"  Removed files ({len(removed_files)}):", "info")
                        for file in sorted(removed_files):
                            message.add(f"    • {file}", "diff")

                    # diff the common files
                    for rel in sorted(common):
                        old_f = os.path.join(old_root, rel)
                        new_f = os.path.join(new_root, rel)

                        with open(old_f, 'r', encoding='utf-8',
                                  errors="ignore") as f1:
                            old_txt = f1.readlines()
                        with open(new_f, 'r', encoding='utf-8',
                                  errors="ignore") as f2:
                            new_txt = f2.readlines()

                        diff = list(difflib.unified_diff(
                            old_txt, new_txt,
                            fromfile=f"{r}:{rel}",
                            tofile=f"{a}:{rel}"
                        ))

                        if diff:
                            diff = colorize_diff(diff).splitlines(keepends=True)
                            message.add(f"\n  Diff in file: {rel}", "info")
                            message.add("".join(diff), "diff")


                    # Calculate the changes in incoming edges
                    added_edges_to_a = [e[0] for e in added_edges if e[1] == a]
                    removed_edges_from_r = [e[0] for e in removed_edges if e[0] == r]
                    # estimating the difference in edges
                    edge_diff_a = set(added_edges_to_a) - set(removed_edges_from_r)
                    edge_diff_r = set(removed_edges_from_r) - set(added_edges_to_a)
                    message.add(
                        f"  Changed incoming edges to {node_display(a)}:",
                        "info",
                    )
                    if edge_diff_a:
                        message.add(f"    Added from ({len(edge_diff_a)}):", "info")
                        for parent in sorted(edge_diff_a):
                            message.add(f"      • {node_display(parent)}", "diff")
                    if edge_diff_r:
                        message.add(f"    Removed from ({len(edge_diff_r)}):", "info")
                        for parent in sorted(edge_diff_r):
                            message.add(f"      • {node_display(parent)}", "diff")

        return message

    def history(self) -> Message:
        """Print all the parents of the current impression.
        """
        message = Message()
        current_impression = self.impression()
        descriptor = current_impression.get_descriptor()
        history_header = (
            f"History of impression {current_impression.short_uuid()} "
            f"({descriptor}):(latest->oldest)\n"
        )
        message.add(
            history_header,
            "title0"
            )
        parents = current_impression.parents()
        # reverse the order
        parents.reverse()
        for i, uuid in enumerate(parents):
            impression = VImpression(uuid)
            message.add(f"[{i+1}]. {impression.short_uuid()} ({impression.get_descriptor()})\n")
        return message
