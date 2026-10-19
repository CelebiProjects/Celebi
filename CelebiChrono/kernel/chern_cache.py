"""
This module is responsible for saving the cache
used by other parts of the application.
"""
from contextlib import contextmanager
import os

from ..utils import csys

class ChernCache:  # pylint: disable=too-many-instance-attributes
    """
    The class is the cache of the application.
    """
    ins = None  # Singleton instance

    def __init__(self): # UnitTest: DONE
        """Init."""
        self.local_config_path = csys.local_config_path()
        self.consult_table = {}
        self.impression_consult_table = {}
        self.predecessor_consult_table = {}
        self.status_consult_table = {}
        self.job_status_consult_table = {}
        self.project_modification_time = (None, -1)
        self.update_table = {}
        self.project_path = ""
        self.deposit_consult_table = {}
        self.file_status_cache = {}
        self.count = 0
        self.impression_check_count = {}
        self.generic_cache = {}

    @classmethod
    def instance(cls): # UnitTest: DONE
        """Returns the singleton instance of ChernCache."""
        if cls.ins is None:
            cls.ins = ChernCache()
        return cls.ins

    def use_and_cache_project_path(self, path):
        """Gets and caches the project path."""
        if not self.project_path:
            self.project_path = path
        return self.project_path

    def get(self, key):
        """Get a value from the generic cache."""
        return self.generic_cache.get(key)

    def set(self, key, value):
        """Set a value in the generic cache."""
        self.generic_cache[key] = value

    @contextmanager
    def freeze_project_modification_time(self, project_path):
        """Use one project mtime snapshot for a high-level operation."""
        if not isinstance(project_path, str) or not os.path.isdir(project_path):
            yield None
            return

        initial_mtime = csys.dir_mtime(project_path)
        previous = self.project_modification_time
        self.project_modification_time = (initial_mtime, float("inf"))
        try:
            yield initial_mtime
        finally:
            if previous[1] == float("inf"):
                self.project_modification_time = previous
            else:
                # Local impression pointers may have changed. Force the next
                # independent operation to establish a fresh snapshot.
                self.project_modification_time = (None, -1)
