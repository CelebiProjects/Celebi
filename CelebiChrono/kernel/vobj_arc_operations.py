""" Basic arc operations for ArcManagement mixin.
"""
from logging import getLogger
from typing import TYPE_CHECKING

from .vobj_core import Core
from .chern_cache import ChernCache

if TYPE_CHECKING:
    from .vobject import VObject

CHERN_CACHE = ChernCache.instance()
logger = getLogger("ChernLogger")


class ArcManagementOperations(Core):
    """ Basic arc operations for arc management.
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
