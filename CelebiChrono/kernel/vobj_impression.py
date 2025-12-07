""" Module for impression management
"""
import difflib
import os

import filecmp
import time
from logging import getLogger

from ..utils import csys
from ..utils.csys import colorize_diff
from ..utils.message import Message
from .vobj_core import Core
from .vimpression import VImpression
from .chern_cache import ChernCache

CHERN_CACHE = ChernCache.instance()
logger = getLogger("ChernLogger")


class ImpressionManagement(Core):
    """ Class for impression management
    """
    def impress(self): # UnitTest: DONE
        """ Create an impression.
        The impressions are store in a directory .chern/impressions/[uuid]
        It is organized as following:
            [uuid]
            |------ contents
            |------ config.json
        In the config.json, the tree of the contents as well as
        the dependencies are stored.
        The object_type is also saved in the json file.
        The tree and the dependencies are sorted via name.
        """
        logger.debug("VObject impress: %s", self.path)
        object_type = self.object_type()
        if object_type not in ("task", "algorithm"):
            sub_objects = self.sub_objects()
            for sub_object in sub_objects:
                sub_object.impress()
            return
        logger.debug("Check whether it is impressed with is_impressed_fast")
        if self.is_impressed_fast():
            logger.warning("Already impressed: %s", self.path)
            return
        for pred in self.predecessors():
            if not pred.is_impressed_fast():
                pred.impress()
        impression = VImpression()
        impression.create(self)
        self.config_file.write_variable("impression", impression.uuid)
        # update the impression_consult_table, since the impression is changed
        consult_table = CHERN_CACHE.impression_consult_table
        consult_table[self.path] = (-1, -1)

    def is_impressed(self): # pylint: disable=too-many-return-statements # UnitTest: DONE
        """ Judge whether the file is impressed
        """
        logger.debug("VObject is_impressed in %s", self.path)
        # Check whether there is an impression already
        impression = self.impression()
        logger.debug("Impression: %s", impression)
        if impression is None or impression.is_zombie():
            # print("No impression or impression is zombie")
            return False

        logger.debug("Check the predecessors is impressed or not")
        # Fast check whether it is impressed
        for pred in self.predecessors():
            if not pred.is_impressed_fast():
                # print("Predecessor not impressed:", pred.path)
                return False

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

        logger.debug("Check the file change")
        # Check the file change: first to check the tree
        file_list = csys.tree_excluded(self.path)
        impression_tree = impression.tree()

        # Check the file list is the same as the impression tree
        # if file_list != impression.tree():
        #     return False
        if csys.sorted_tree(file_list) != csys.sorted_tree(impression_tree):
            # print("Tree mismatch:")
            # print("Current tree:", csys.sorted_tree(file_list))
            # print("Impression tree:", csys.sorted_tree(impression_tree))
            return False

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

        for dirpath, dirnames, filenames in file_list: # pylint: disable=unused-variable
            for f in filenames:
                if not filecmp.cmp(f"{self.path}/{dirpath}/{f}",
                                   f"{impression.path}/contents/{dirpath}/{f}"):
                    # print("# File difference:")
                    # print(f"cp {impression.path}/contents/{dirpath}/{f}",
                    #       f"{self.path}/{dirpath}/{f} ",
                    #       )
                    return False
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

    def is_impressed_fast(self): # UnitTest: DONE
        """ Judge whether the file is impressed, with timestamp
        """
        logger.debug("VObject is_impressed_fast")
        consult_table = CHERN_CACHE.impression_consult_table
        # FIXME cherncache should be replaced
        # by some function called like cache
        (last_consult_time, is_impressed) = consult_table.get(
            self.path, (-1, -1)
        )
        now = time.time()
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
        is_impressed = self.is_impressed()
        consult_table[self.path] = (time.time(), is_impressed)
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
        if uuid == "":
            return None
        return VImpression(uuid)

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

        status = "impressed"
        if consult_id:
            consult_table[self.path] = (consult_id, status)
        return status

    # pylint: disable=too-many-locals,too-many-statements
    def trace(self, impression=None):
        """
        Compare the *current* dependency DAG of `self` with the DAG stored in
        a given impression (or the current impression if not provided).
        Print the differences.

        Output example:

            === DAG Node Differences ===
            Added nodes:   {uuid3}
            Removed nodes: {uuid7}

            === DAG Edge Differences ===
            Added edges:   {(uuid3 -> uuid1)}
            Removed edges: {(uuid7 -> uuid2)}

        """
        logger.debug("Tracing DAG differences for %s", self.path)

        if impression is None:
            impression = self.impression()
        if impression is None:
            print("No impression exists. Object is NEW.")
            return
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

        # ------------------------------------------------------
        # Pretty print
        # ------------------------------------------------------
        print("\n=== DAG Node Differences ===")
        print(f"Added nodes:   {added_nodes if added_nodes else '{}'}")
        print(f"Removed nodes: {removed_nodes if removed_nodes else '{}'}")

        print("\n=== DAG Edge Differences ===")
        print(f"Added edges:   {added_edges if added_edges else '{}'}")
        print(f"Removed edges: {removed_edges if removed_edges else '{}'}")

        # --------------------------------------------------------
        #  Check parent-child relationships between removed/added
        # --------------------------------------------------------
        print("\n=== Detailed Diff (removed parent → added child) ===")

        def is_parent(parent_uuid, child_uuid):
            return parent_uuid in VImpression(child_uuid).parents()

        for r in removed_nodes:
            for a in added_nodes:
                if is_parent(r, a):
                    print(f"\n--- Change detected: {r} → {a}")

                    # --------------------------------------------------------
                    #  Run impression diff
                    # --------------------------------------------------------
                    old_impr = VImpression(r) if r else None
                    new_impr = VImpression(a) if a else None

                    if not (old_impr and new_impr):
                        print("One of the impressions does not exist, skipping diff.")
                        continue

                    old_root = old_impr.path + "/contents"
                    new_root = new_impr.path + "/contents"

                    # Compare file lists (sorted, relative paths)
                    old_files = []
                    new_files = []

                    for dirpath, _, files in os.walk(old_root):
                        for f in files:
                            rel = os.path.relpath(os.path.join(dirpath, f), old_root)
                            old_files.append(rel)

                    for dirpath, _, files in os.walk(new_root):
                        for f in files:
                            rel = os.path.relpath(os.path.join(dirpath, f), new_root)
                            new_files.append(rel)

                    old_files_set = set(old_files)
                    new_files_set = set(new_files)

                    common = old_files_set & new_files_set
                    removed_files = old_files_set - new_files_set
                    added_files   = new_files_set - old_files_set

                    print(f"  Added files:   {added_files}")
                    print(f"  Removed files: {removed_files}")

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
                            print(f"\n  Diff in file: {rel}")
                            print("".join(diff))

                    # Calculate the changes in incoming edges
                    added_edges_to_a = [e[0] for e in added_edges if e[1] == a]
                    removed_edges_from_r = [e[0] for e in removed_edges if e[0] == r]
                    # estimating the difference in edges
                    edge_diff_a = set(added_edges_to_a) - set(removed_edges_from_r)
                    edge_diff_r = set(removed_edges_from_r) - set(added_edges_to_a)
                    print(f"  Changed incoming edges to {a}:")
                    print(f"    Added from:   {edge_diff_a if edge_diff_a else '{}'}")
                    print(f"    Removed from: {edge_diff_r if edge_diff_r else '{}'}")

        print("\nTrace complete.\n")

    def history(self) -> Message:
        """Print all the parents of the current impression.
        """
        message = Message()
        message.add(f"History of impression {self.impression().short_uuid()}:(latest->oldest)\n", "title0")
        parents = self.impression().parents()
        # reverse the order
        parents.reverse()
        for i, uuid in enumerate(parents):
            message.add(f"[{i+1}]. {uuid}\n")
        return message
