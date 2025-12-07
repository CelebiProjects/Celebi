# pylint: disable=too-few-public-methods
"""
This module is responsible for saving the cache
used by other parts of the application.
"""
from ..utils import csys

class ChernCache:  # pylint: disable=too-many-instance-attributes
    """
    The class is the cache of the application.
    """
    ins = None  # Singleton instance

    def __init__(self): # UnitTest: DONE
        self.local_config_path = csys.local_config_path()
        self.consult_table = {}
        self.impression_consult_table = {}
        self.predecessor_consult_table = {}
        self.status_consult_table = {}
        self.job_status_consult_table = {}
        self.project_modification_time = (None, -1)
        self.update_table = {}

    @classmethod
    def instance(cls): # UnitTest: DONE
        """Returns the singleton instance of ChernCache."""
        if cls.ins is None:
            cls.ins = ChernCache()
        return cls.ins
