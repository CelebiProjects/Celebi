""" Input management methods for ArcManagement mixin.
"""
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


class ArcManagementInput(Core):
    """ Input management methods for arc management.
    """
    def add_input(self, path, alias):
        """ add input
        """
        # start_time = time()
        if not self.is_task_or_algorithm():
            print(f"You are adding input to {self.object_type()} type object. "
                  "The input is required to be a task or an algorithm.")
            return

        project_path = CHERN_CACHE.project_path \
                if CHERN_CACHE.project_path \
                else CHERN_CACHE.use_and_cache_project_path(csys.project_path())
        obj = self.get_vobject(path, project_path)
        if obj.object_type() != self.object_type():
            print(f"You are adding {obj.object_type()} type object as"
                   " input. The input is required to be a {self.object_type()}.")
            return

        if obj.has_predecessor_recursively(self):
            print("The object is already in the dependency diagram of "
                  "the ``input'', which will cause a loop.")
            return

        # print(f"Time taken to validate input: {time() - start_time:.2f} seconds.")

        # if the obj is already an input, reject to add it
        if self.has_predecessor(obj):
            print("The input already exists.")
            return

        # project_path = self.project_path()
        project_path = CHERN_CACHE.project_path \
                if CHERN_CACHE.project_path \
                else CHERN_CACHE.use_and_cache_project_path(csys.project_path())
        if self.has_alias(alias):
            print("The alias already exists. "
                  "The original input and alias will be replaced.")
            original_object = self.get_vobject(
                join(project_path, self.alias_to_path(alias)),
                project_path
            )
            self.remove_arc_from(original_object)
            self.remove_alias(alias)

        # print(f"Time taken before adding arc: {time() - start_time:.2f} seconds.")

        self.add_arc_from(obj)
        self.set_alias(alias, obj.invariant_path())

        # print(f"Input added successfully. "
        #       f"Total time taken: {time() - start_time:.2f} seconds.")

    def remove_input(self, alias):
        """ Remove the input """
        path = self.alias_to_path(alias)
        if not path:
            print("Alias not found")
            return
        # project_path = self.project_path()
        project_path = CHERN_CACHE.project_path \
                if CHERN_CACHE.project_path \
                else CHERN_CACHE.use_and_cache_project_path(csys.project_path())
        obj = self.get_vobject(join(project_path, path), project_path)
        self.remove_arc_from(obj)
        self.remove_alias(alias)
