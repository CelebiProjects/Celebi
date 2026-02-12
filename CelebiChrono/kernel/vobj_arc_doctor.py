""" Doctor methods for ArcManagement mixin.
"""
import os
from os.path import join
from logging import getLogger
from typing import TYPE_CHECKING

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
            if obj.path_to_alias(pred_object.invariant_path()) == "" and \
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