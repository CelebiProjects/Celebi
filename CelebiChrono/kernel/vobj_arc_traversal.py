""" Traversal and predecessor/successor methods for ArcManagement mixin.
"""
from time import time
from logging import getLogger
from typing import TYPE_CHECKING

from ..utils import csys
from .vobj_core import Core
from .chern_cache import ChernCache

if TYPE_CHECKING:
    from .vobject import VObject

CHERN_CACHE = ChernCache.instance()
logger = getLogger("ChernLogger")


class ArcManagementTraversal(Core):
    """ Traversal and predecessor/successor methods for arc management.
    """
    def successors(self):
        """ The successors of the current object
        Return a list of [object]

        Results are cached similarly to predecessors().
        """
        project_path = CHERN_CACHE.project_path \
                if CHERN_CACHE.project_path \
                else CHERN_CACHE.use_and_cache_project_path(csys.project_path())

        now = time()
        modification_time_from_cache, modification_consult_time = \
                CHERN_CACHE.project_modification_time
        if modification_time_from_cache is None or now - modification_consult_time > 1:
            modification_time = csys.dir_mtime(project_path)
            CHERN_CACHE.project_modification_time = (modification_time, now)
        else:
            modification_time = modification_time_from_cache

        cache_key = f"successors:{self.path}"
        cached = CHERN_CACHE.get(cache_key)
        if cached is not None:
            cached_mtime, cached_succs = cached
            if cached_mtime == modification_time:
                return cached_succs

        succ_str = self.config_file.read_variable("successors", [])
        succs = []
        for path in succ_str:
            succs.append(self.get_vobject(f"{project_path}/{path}", project_path))

        CHERN_CACHE.set(cache_key, (modification_time, succs))
        return succs

    def predecessors(self):
        """ The predecessors of the current object
        Return a list of [object]

        Results are cached keyed by path + project modification time, matching
        the consult_id pattern used by is_impressed_fast / status / job_status.
        """
        project_path = CHERN_CACHE.project_path \
                if CHERN_CACHE.project_path \
                else CHERN_CACHE.use_and_cache_project_path(csys.project_path())

        now = time()
        modification_time_from_cache, modification_consult_time = \
                CHERN_CACHE.project_modification_time
        if modification_time_from_cache is None or now - modification_consult_time > 1:
            modification_time = csys.dir_mtime(project_path)
            CHERN_CACHE.project_modification_time = (modification_time, now)
        else:
            modification_time = modification_time_from_cache

        cache_key = f"predecessors:{self.path}"
        cached = CHERN_CACHE.get(cache_key)
        if cached is not None:
            cached_mtime, cached_preds = cached
            if cached_mtime == modification_time:
                return cached_preds

        pred_str = self.config_file.read_variable("predecessors", [])
        preds = []
        for path in pred_str:
            preds.append(self.get_vobject(f"{project_path}/{path}", project_path))

        CHERN_CACHE.set(cache_key, (modification_time, preds))
        return preds

    def has_successor(self, obj):  # UnitTest: DONE
        """ Judge whether the object has the specific successor
        """
        succ_str = self.config_file.read_variable("successors", [])
        return obj.invariant_path() in succ_str

    def has_predecessor(self, obj):  # UnitTest: DONE
        """ Judge whether the object has the specific predecessor
        """
        pred_str = self.config_file.read_variable("predecessors", [])
        return obj.invariant_path() in pred_str

    def has_predecessor_recursively(self, obj, consult_id=None):  # UnitTest: DONE
        """ Judge whether the object has the specific predecessor recursively
        """
        # start_time = time()
        # print(f">>> Checking if {self} has {obj} as predecessor recursively...")
        # The object itself is the predecessor of itself
        if self.invariant_path() == obj.invariant_path():
            return True

        # print(f"Time stamp 1: {time() - start_time:.2f} seconds.")
        pred_str = self.config_file.read_variable("predecessors", [])
        if obj.invariant_path() in pred_str:
            return True
        # Use cache to avoid infinite loop
        # print(f"Time stamp 2: {time() - start_time:.2f} seconds.")
        consult_table = CHERN_CACHE.predecessor_consult_table
        (last_consult_time, has_predecessor) = consult_table.get(
            self.path, (-1, False)
        )

        now, consult_id = csys.update_time(consult_id)
        # print(f"Time stamp 3: {time() - start_time:.2f} seconds.")

        # project_path = self.project_path()
        project_path = CHERN_CACHE.project_path \
                if CHERN_CACHE.project_path \
                else CHERN_CACHE.use_and_cache_project_path(csys.project_path())

        modification_time_from_cache, modification_consult_time = \
                CHERN_CACHE.project_modification_time
        if modification_time_from_cache is None or now - modification_consult_time > 0.001:
            modification_time = csys.dir_mtime(project_path)
            CHERN_CACHE.project_modification_time = modification_time, now
        else:
            modification_time = modification_time_from_cache

        # modification_time = csys.dir_mtime(project_path)
        if modification_time <= last_consult_time:
            return has_predecessor
        # print(f"Time stamp 4: {time() - start_time:.2f} seconds.")

        # print(f"Checking {len(pred_str)} predecessors...")
        # print(f"time taken so far: {time() - start_time:.2f} seconds.")
        for pred_path in pred_str:
            pred_obj = self.get_vobject(f"{project_path}/{pred_path}", project_path)
            if pred_obj.has_predecessor_recursively(obj, consult_id):
                mtime, _ = CHERN_CACHE.project_modification_time
                if mtime is None:
                    mtime = csys.dir_mtime(project_path)
                    CHERN_CACHE.project_modification_time = (mtime, time())
                consult_table[self.path] = (mtime, True)
                return True
        # print(f"No predecessor found for {obj}. time: {time() - start_time:.2f} seconds.")
        mtime, _ = CHERN_CACHE.project_modification_time
        if mtime is None:
            mtime = csys.dir_mtime(project_path)
            CHERN_CACHE.project_modification_time = (mtime, time())
        consult_table[self.path] = (mtime, False)
        # print(f"<<< Finished checking in {time() - start_time:.2f} seconds.")
        return False
