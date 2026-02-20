""" File operations methods for FileManagement mixin.
"""
import os
import shutil
import difflib
from os.path import join, normpath
from logging import getLogger
from typing import TYPE_CHECKING, Tuple, List

from ..utils import csys
from ..utils.message import Message
from ..utils.csys import colorize_diff
from .vobj_core import Core
from .chern_cache import ChernCache

if TYPE_CHECKING:
    from .vobject import VObject

CHERN_CACHE = ChernCache.instance()
logger = getLogger("ChernLogger")


class FileManagementOperations(Core):
    """ File operations methods for file management.
    """
    def copy_to_check(self, new_path: str) -> Tuple[bool, str]:  # UnitTest: DONE
        """ Check if the new path is valid for copying

        Returns:
            Tuple[bool, str]: (success_status, error_message)
        """
        # Check if the destination directory exists
        destination_dir = os.path.dirname(new_path)
        if not csys.exists(destination_dir) and destination_dir:
            rel_dest_dir = os.path.relpath(destination_dir, self.project_path())
            error_msg = f"Destination directory '@/{rel_dest_dir}' does not exist."
            return False, error_msg

        # Check if source and destination paths are the same
        if os.path.abspath(self.path) == os.path.abspath(new_path):
            error_msg = "Source and destination paths are the same."
            return False, error_msg

        # Check if the destination path already exists
        if csys.exists(new_path):
            rel_new_path = os.path.relpath(new_path, self.project_path())
            error_msg = f"Destination path '@/{rel_new_path}' already exists."
            return False, error_msg

        return True, ""

    def copy_to_deal_with_arcs(self, queue: List['VObject'], new_path: str) -> None:
        """ Deal with the arcs when copying
        """
        for obj in queue:
            # Calculate the absolute path of the new directory
            norm_path = normpath(
                join(new_path, self.relative_path(obj.path))
            )
            new_object = self.get_vobject(norm_path, self.project_path())
            new_object.clean_flow()
            new_object.clean_impressions()

        for obj in queue:
            # Calculate the absolute path of the new directory
            norm_path = normpath(
                join(new_path, self.relative_path(obj.path))
            )
            new_object = self.get_vobject(norm_path, self.project_path())
            for pred_object in obj.predecessors():
                # if in the outside directory
                if self.relative_path(pred_object.path).startswith(".."):
                    # FIXME: link the outside object, make it optional?
                    new_object.add_arc_from(pred_object)
                    alias = obj.path_to_alias(pred_object.invariant_path())
                    new_object.set_alias(alias, pred_object.invariant_path())
                else:
                    # if in the same tree
                    relative_path = self.relative_path(pred_object.path)
                    new_object.add_arc_from(self.get_vobject(
                        join(new_path, relative_path), self.project_path())
                    )
                    alias1 = obj.path_to_alias(pred_object.invariant_path())
                    norm_path = normpath(
                        join(new_path, relative_path)
                    )
                    new_object.set_alias(
                        alias1,
                        self.get_vobject(norm_path, self.project_path()).invariant_path()
                    )

            for succ_object in obj.successors():
                if self.relative_path(succ_object.path).startswith(".."):
                    pass

    def copy_to(self, new_path: str) -> Message:  # UnitTest: DONE
        """ Copy the current objects and its containings to a new path.
        """
        is_valid, error_message = self.copy_to_check(new_path)
        if not is_valid:
            message = Message()
            message.add(f"Error: {error_message}", "warning")
            return message

        queue = self.sub_objects_recursively()
        # Make sure the related objects are all impressed
        for obj in queue:
            if not obj.is_task_or_algorithm():
                continue
            if not obj.is_impressed_fast():
                obj.impress()

        shutil.copytree(self.path, new_path)

        self.copy_to_deal_with_arcs(queue, new_path)

         # Deal with the impression
        for obj in queue:
            # Calculate the absolute path of the new directory
            norm_path = normpath(f"{new_path}/{self.relative_path(obj.path)}")
            if obj.object_type() == "directory":
                continue
            new_object = self.get_vobject(norm_path, self.project_path())
            new_object.impress()

        return Message()  # Empty message for success

    def move_to_deal_with_arcs(self, queue: List['VObject'],
                              new_path: str) -> None:
        """ Deal with the arcs when moving
        """
        for obj in queue:
            # Calculate the absolute path of the new directory
            norm_path = normpath(
                join(new_path, self.relative_path(obj.path))
            )
            new_object = self.get_vobject(norm_path, self.project_path())
            new_object.clean_flow()

        for obj in queue:
            # Calculate the absolute path of the new directory
            norm_path = normpath(
                join(new_path, self.relative_path(obj.path))
            )
            new_object = self.get_vobject(norm_path, self.project_path())
            for pred_object in obj.predecessors():
                if self.relative_path(pred_object.path).startswith(".."):
                    # if in the outside directory
                    new_object.add_arc_from(pred_object)
                    alias = obj.path_to_alias(pred_object.invariant_path())
                    new_object.set_alias(alias, pred_object.invariant_path(), ignore_yaml=True)
                else:
                    # if in the same tree
                    relative_path = self.relative_path(pred_object.path)
                    new_object.add_arc_from(
                        self.get_vobject(join(new_path, relative_path), self.project_path())
                    )
                    alias1 = obj.path_to_alias(pred_object.invariant_path())
                    alias2 = pred_object.path_to_alias(obj.invariant_path())
                    norm_path = normpath(
                        join(new_path, relative_path)
                    )
                    new_object.set_alias(
                        alias1,
                        self.get_vobject(norm_path).invariant_path(),
                        ignore_yaml=True
                    )
                    self.get_vobject(norm_path, self.project_path()).set_alias(
                        alias2,
                        new_object.invariant_path(),
                        ignore_yaml=True
                    )

            for succ_object in obj.successors():
                # if in the outside directory
                if self.relative_path(succ_object.path).startswith(".."):
                    new_object.add_arc_to(succ_object)
                    succ_object.remove_arc_from(obj)
                    alias = succ_object.path_to_alias(obj.invariant_path())
                    succ_object.remove_alias(alias, ignore_yaml=True)
                    succ_object.set_alias(alias, new_object.invariant_path(), ignore_yaml=True)

        for obj in queue:
            for pred_object in obj.predecessors():
                if self.relative_path(pred_object.path).startswith(".."):
                    obj.remove_arc_from(pred_object)

            for succ_object in obj.successors():
                if self.relative_path(succ_object.path).startswith(".."):
                    obj.remove_arc_to(succ_object)

    def move_to(self, new_path: str) -> Message:  # UnitTest: DONE
        """ move to another path
        """
        is_valid, error_message = self.move_to_check(new_path)
        if not is_valid:
            message = Message()
            message.add(f"Error: {error_message}", "warning")
            return message

        queue = self.sub_objects_recursively()

        # Make sure the related objects are all impressed
        all_impressed = True
        not_impressed_objects = []
        for obj in queue:
            if not obj.is_task_or_algorithm():
                continue
            if not obj.is_impressed_fast():
                all_impressed = False
                not_impressed_objects.append(obj)

        if not all_impressed:
            message = Message()
            for obj in not_impressed_objects:
                message.add(f"The {obj.object_type()} {obj} is not impressed, "
                           f"please impress it and try again\n", "warning")
            return message

        shutil.copytree(self.path, new_path)

        # self.move_to_deal_with_arcs(queue, new_path)
        self.move_to_deal_with_arcs([x for x in queue if x.object_type() != "directory"], new_path)

        shutil.rmtree(self.path)

        return Message()  # Empty message for success

    def move_to_check(self, new_path: str) -> Tuple[bool, str]:  # UnitTest: DONE
        """ Check if the new path is valid for moving

        Returns:
            Tuple[bool, str]: (success_status, error_message)
        """
        # Perform all validation checks and collect any error
        error_msg = ""

        # Check if the destination directory already exists
        destination_dir = os.path.dirname(new_path)
        if not csys.exists(destination_dir) and destination_dir:
            rel_dest_dir = os.path.relpath(destination_dir, self.project_path())
            error_msg = f"Destination directory '@/{rel_dest_dir}' does not exist."

        # Check if the destination path already exists
        elif csys.exists(new_path):
            rel_new_path = os.path.relpath(new_path, self.project_path())
            error_msg = f"Destination path '@/{rel_new_path}' already exists."

        # Check if the destination directory is a subdirectory of the source
        elif os.path.commonpath([self.path, new_path]) == self.path:
            rel_new_path = os.path.relpath(new_path, self.project_path())
            rel_source_path = os.path.relpath(self.path, self.project_path())
            error_msg = (f"Destination path '@/{rel_new_path}' is a subdirectory "
                        f"of the source path '@/{rel_source_path}'.")

        # Check if source and destination paths are the same
        elif self.path.lower() == new_path.lower():
            error_msg = "The source and destination paths are the same."

        else:
            # Check if the destination parent directory is a valid vdirectory or vproject
            parent_dir = normpath(os.path.join(new_path, ".."))
            parent_object = self.get_vobject(parent_dir, self.project_path())

            # Check if the parent object is a zombie (invalid/non-existent vobject)
            if parent_object.is_zombie():
                rel_new_path = os.path.relpath(new_path, self.project_path())
                error_msg = (f"The destination path '@/{rel_new_path}' has an "
                            f"invalid parent directory.")

            # Check if the parent object is a valid vdirectory or vproject
            elif parent_object.object_type() not in ("directory", "project"):
                rel_new_path = os.path.relpath(new_path, self.project_path())
                error_msg = (f"The destination path '@/{rel_new_path}' is not "
                            f"within a vdirectory or vproject.")

        return (False, error_msg) if error_msg else (True, "")

    def rm(self) -> Message:  # UnitTest: DONE
        """ Remove this object.
        The important thing is to unalias.
        """
        queue = self.sub_objects_recursively()
        for obj in queue:
            for pred_object in obj.predecessors():
                if self.relative_path(pred_object.path).startswith(".."):
                    obj.remove_arc_from(pred_object)
                    alias = pred_object.path_to_alias(pred_object.path)
                    pred_object.remove_alias(alias)

            for succ_object in obj.successors():
                if self.relative_path(succ_object.path).startswith(".."):
                    obj.remove_arc_to(succ_object)
                    alias = succ_object.path_to_alias(succ_object.path)
                    succ_object.remove_alias(alias)

        shutil.rmtree(self.path)

        return Message()  # Empty message for success

    def import_file(self, path: str) -> Message:
        """
        Import the file to this task directory
        """
        message = Message()

        if not self.is_task_or_algorithm():
            message.add("This function is only available for task or algorithm.", "warning")
            return message

        if not csys.exists(path):
            message.add("File does not exist.", "warning")
            return message

        filename = os.path.basename(path)
        if csys.exists(self.path + "/" + filename):
            message.add("File already exists.", "warning")
            return message

        if os.path.isdir(path):
            csys.copy_tree(path, self.path + "/" + filename)
        else:
            csys.copy(path, self.path + "/" + filename)

        return message  # Empty message for success

    def rm_file(self, file: str) -> Message:
        """
        Remove the files within a task or an algorithm
        """
        message = Message()

        if not self.is_task_or_algorithm():
            message.add("This function is only available for task or algorithm.", "warning")
            return message

        abspath = self.path + "/" + file

        if not csys.exists(abspath):
            message.add("File does not exist.", "warning")
            return message

        # protect: the file should not go out of the task directory
        if self.relative_path(abspath).startswith(".."):
            message.add("The file should not go out of the task directory.", "warning")
            return message

        # protect: the file should not be the task directory
        if self.relative_path(abspath) == ".":
            message.add("The file should not be the task directory.", "warning")
            return message

        # protect: should not remove the .celebi and celebi.yaml
        if self.relative_path(abspath) in (".celebi", "celebi.yaml"):
            message.add("The file should not be the .celebi or celebi.yaml.", "warning")
            return message

        if os.path.isdir(abspath):
            csys.rm_tree(abspath)
        else:
            os.remove(abspath)

        return message  # Empty message for success

    def move_file(self, file: str, dest_file: str) -> Message:
        """
        Move the files within a task or an algorithm
        """
        message = Message()

        # Perform validation checks
        if not self.is_task_or_algorithm():
            message.add("This function is only available for task or algorithm.", "warning")
        else:
            abspath = self.path + "/" + file

            if not csys.exists(abspath):
                message.add("File does not exist.", "warning")
            elif self.relative_path(abspath).startswith(".."):
                message.add("The file should not go out of the task directory.", "warning")
            elif self.relative_path(abspath) == ".":
                message.add("The file should not be the task directory.", "warning")
            elif self.relative_path(abspath) in (".celebi", "celebi.yaml"):
                message.add("The file should not be the .celebi or celebi.yaml.", "warning")
            else:
                # Check if the destination directory exists
                dest = self.path + "/" + dest_file
                if not csys.exists(os.path.dirname(dest)):
                    rel_dest_dir = os.path.relpath(os.path.dirname(dest),
                                                 self.project_path())
                    message.add(f"Error: Destination directory '@/{rel_dest_dir}' "
                               f"does not exist.", "warning")
                else:
                    # All validations passed, perform the move
                    csys.move(abspath, dest)

        return message

    def changes(self):  # pylint: disable=too-many-locals
        """
        Get the changes with respect to the latest impression
        """
        if not self.is_task_or_algorithm():
            message = Message()
            message.add("This function is only available for task or algorithm.", "warning")
            return message

        message = Message()
        impression = self.impression()

        if impression.is_zombie():
            message.add("The object has no history impressed yet.", "warning")
            return message

        # --------------------------------------------------------
        #  Run impression diff
        # --------------------------------------------------------
        old_impr = impression

        old_root = os.path.join(old_impr.path, "contents")
        new_root = self.path

        # --------------------------------------------------------
        #  Compare file lists (sorted, relative paths)
        # --------------------------------------------------------
        old_files = csys.get_files_in_directory(old_root)
        new_files = csys.get_files_in_directory(new_root, exclude=".celebi")

        old_files_set = set(old_files)
        new_files_set = set(new_files)

        common = sorted(old_files_set & new_files_set)
        removed_files = sorted(old_files_set - new_files_set)
        added_files   = sorted(new_files_set - old_files_set)

        if added_files != removed_files:
            message.add("Added files: ", "title0")
            message.add(f"{added_files}\n", "info")
            message.add("Removed files: ", "title0")
            message.add(f"{removed_files}\n", "info")

        # --------------------------------------------------------
        #  Diff common files
        # --------------------------------------------------------
        for rel in common:
            old_f = os.path.join(old_root, rel)
            new_f = os.path.join(new_root, rel)

            try:
                with open(old_f, "r", encoding="utf-8", errors="ignore") as f1:
                    old_txt = f1.readlines()
                with open(new_f, "r", encoding="utf-8", errors="ignore") as f2:
                    new_txt = f2.readlines()
            except (IOError, ValueError) as e:  # Be specific
                message.add(f"Failed to read file {rel}: {e}", "warning")
                continue

            diff = list(difflib.unified_diff(
                old_txt,
                new_txt,
                fromfile=f"impressed:{rel}",   # ✅ fixed
                tofile=f"current:{rel}"       # ✅ fixed
            ))

            if diff:
                diff = colorize_diff(diff).splitlines(keepends=True)
                message.add(f"\nDiff in file: {rel}\n", "title0")
                message.add("".join(diff), "raw")

        return message
