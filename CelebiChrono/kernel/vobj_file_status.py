""" Status and utility methods for FileManagement mixin.
"""
import os
from os.path import join
from logging import getLogger
from typing import TYPE_CHECKING, List

from .vobj_core import Core
from .chern_cache import ChernCache

if TYPE_CHECKING:
    from .vobject import VObject

CHERN_CACHE = ChernCache.instance()
logger = getLogger("ChernLogger")


class FileManagementStatus(Core):
    """ Status and utility methods for file management.
    """
    def sub_objects(self) -> List['VObject']:  # UnitTest: DONE
        """ return a list of the sub_objects
        """
        sub_directories = os.listdir(self.path)
        sub_object_list = []
        for item in sub_directories:
            if os.path.isdir(join(self.path, item)):
                obj = self.get_vobject(join(self.path, item), self.project_path())
                if obj.is_zombie():
                    continue
                sub_object_list.append(obj)
        return sub_object_list

    def sub_objects_recursively(self) -> List['VObject']:  # UnitTest: DONE
        """ Return a list of all the sub_objects
        """
        queue = [self]
        index = 0
        while index < len(queue):
            top_object = queue[index]
            queue += top_object.sub_objects()
            index += 1
        return queue

    def sub_objects_recursively_parents(self) -> List['str']:
        """ Return a list of all the parents impression of the sub_objects
        """
        sub_objects = self.sub_objects_recursively()
        parent_impressions = []
        for obj in sub_objects:
            if not obj.is_task_or_algorithm():
                continue
            impr = obj.impression()
            parent_impressions.extend(impr.parents())
        return parent_impressions