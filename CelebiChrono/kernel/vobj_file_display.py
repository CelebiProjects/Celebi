""" Display-related methods for FileManagement mixin.
"""
import os
import time
from os.path import join
from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING, List

from ..utils import csys
from ..utils.message import Message
from ..utils.csys import colorize_diff
from ..utils import metadata
from .vobj_core import Core
from .chern_cache import ChernCache
from .chern_communicator import ChernCommunicator

if TYPE_CHECKING:
    from .vobject import VObject

CHERN_CACHE = ChernCache.instance()
logger = getLogger("ChernLogger")


@dataclass
class LsParameters:
    """ Light weighted data class to store the parameters of ls
    """
    readme: bool = True
    predecessors: bool = True
    sub_objects: bool = True
    status: bool = False
    successors: bool = False
    task_info: bool = True


class FileManagementDisplay(Core):  # pylint: disable=too-many-public-methods
    """ Display-related methods for file management.
    """
    def ls(self, show_info: 'LsParameters' = LsParameters()) -> Message:
        """ Print the subdirectory of the object
        I recommend to print also the README
        and the parameters|inputs|outputs ...
        """

        logger.debug("VObject ls: %s", self.invariant_path())

        message = self.printed_dite_status()

        if show_info.readme:
            message.add("README: \n", "comment")
            message.add(self.readme(), "comment")
            message.add("\n")

        sub_objects = self.sub_objects()
        if show_info.sub_objects:
            message.append(self.show_sub_objects(sub_objects, show_info))

        total = len(sub_objects)
        predecessors = self.predecessors()
        if predecessors and show_info.predecessors:
            message.append(self.show_predecessors(predecessors, total))

        total += len(predecessors)
        successors = self.successors()
        if successors and show_info.successors:
            message.append(self.show_successors(successors, total))

        return message

    def show_status(self) -> Message:
        """ Show the status of the task.
        """
        status = self.status()
        status_color_map = {
            "new": "normal",
            "impressed": "success"
        }

        status_color = status_color_map.get(status, "")

        message = Message()
        message.add("**** STATUS: ", "title0")
        message.add(f"[{status}]", status_color)
        message.add("\n")
        return message

    def printed_status(self) -> Message:  # pylint: disable=too-many-branches,too-many-statements
        """ Printed the status of the object"""

        message = Message()

        message.add(f"Status of : {self.invariant_path()}\n")
        if self.is_task_or_algorithm():
            if self.status() == "impressed":
                message.add("Impression: ")
                message.add(f"{'['+self.impression().uuid+']'}", 'success')
                message.add("\n")
            else:
                message.add("Impression: ")
                message.add("[new]")
                message.add("\n")
                return message
        else:
            if self.status() == "impressed":
                message.add("All the subobjects are ")
                message.add("[impressed]", 'success')
                message.add(".\n")
            else:
                message.add("Some subobjects are ")
                message.add("[not impressed]", 'normal')
                message.add(".\n")
                # ---- Testing the parallelization speedup ----
                # Parallelized subobject status checks

                sub_objects = self.sub_objects()
                # sort the objects according to (object_type: directory < algorithm < task, path)
                # need to map the object_type to a sortable value
                object_type_order = {"directory": 0, "algorithm": 1, "task": 2}
                sub_objects.sort(key=lambda x: (object_type_order.get(x.object_type(), 99), x.path))

                # Parallel check of subobject statuses (CPU-bound)
                # with ProcessPoolExecutor(max_workers=8) as executor:
                #     futures = [executor.submit(_check_sub_status, sub) for sub in sub_objects]
                #     for fut in as_completed(futures):
                #         name, sub_status = fut.result()
                #         if sub_status == "new":
                #             message.add(f"Subobject {name} is [not impressed]\n", "normal")
                # ----------------------------------------------

                # ---- Original serial subobject status checks ----
                for sub_object in sub_objects:
                    if sub_object.status() == "new":
                        message.add(f"Subobject {sub_object} is ")
                        message.add("[not impressed]", 'normal')
                        message.add("\n")
                # -------------------------------------------------
                return message

        cherncc = ChernCommunicator.instance()
        dite_status = cherncc.dite_status()
        if dite_status == "connected":
            message.add("DITE: ")
            message.add("[connected]")
            message.add("\n")
        else:
            message.add("DITE: ")
            message.add("[unconnected]", "warning")
            message.add("\n")
            return message

        if self.is_task_or_algorithm():
            deposited = cherncc.is_deposited(self.impression())
            if deposited == "FALSE":
                message.add("Impression not deposited in DITE\n")
                return message

        now = time.time()
        if not self.is_task_or_algorithm():
            job_status = self.job_status(now)
            message.add(f"{'Job status':<10}: ")
            message.add(f"{'['+job_status+']'}")
            message.add("\n---------------\n")
            objects = []
            sub_objects = self.sub_objects()
            object_type_order = {"directory": 0, "algorithm": 1, "task": 2}
            # Make the sort even smarter
            # If the object is in the format of xxx_aaa_xxx_bbb, where some part is a number,
            # we can sort according to the number
            sub_objects.sort(key=lambda x: (object_type_order.get(x.object_type(), 99),
                                                [int(part) if part.isdigit() else part
                                                for part in os.path.basename(x.path).split('_')]))
            for sub_object in sub_objects:
                # only append the base name
                objects.append((os.path.basename(sub_object.path),
                                sub_object.job_status(now)))

            max_width = 0
            if objects:
                max_width = max(len(name) for name, _ in objects)

            for name, status in objects:
                message.add(f"{name:<{max_width}}: ")
                message.add(f"[{status}]")
                message.add("\n")

        return message

    def printed_dite_status(self) -> Message:
        """ Print the status of the DITE"""
        cherncc = ChernCommunicator.instance()
        message = Message()
        message.add(">>>> DITE: ", "title0")
        status = cherncc.dite_status()
        if status == "connected":
            message.add("[connected]", "success")
        elif status == "unconnected":
            message.add("[unconnected]", "warning")
        message.add("\n")
        return message

    def show_sub_objects(self,  # pylint: disable=too-many-locals
                         sub_objects: List['VObject'],
                         show_info: LsParameters) -> Message:
        """ Show the sub_objects with dynamic alignment """
        message = Message()
        # sub_objects = self.sub_objects()
        sub_objects.sort(key=lambda x: (x.object_type(), x.path))

        if not sub_objects:
            return message

        message.add(">>>> Subobjects:\n", "title0")

        # 1. Pre-calculate the relative paths and the max widths for alignment
        processed_objects = []
        max_idx_w = len(str(len(sub_objects) - 1))
        max_type_w = 0
        max_path_w = 0

        for obj in sub_objects:
            path = self.relative_path(obj.path)
            obj_type = f"({obj.object_type()})"

            processed_objects.append((obj_type, path, obj))

            # Track maximum lengths
            max_type_w = max(max_type_w, len(obj_type))
            max_path_w = max(max_path_w, len(path))

        # 2. Iterate and build the message using calculated widths
        for index, (obj_type, sub_path, obj) in enumerate(processed_objects):
            order_index = f"{[index]}"
            base_str = f"{order_index:>{max_idx_w+2}} {obj_type:<{max_type_w + 2}} {sub_path:<{max_path_w}}"  # pylint: disable=line-too-long
            message.add(base_str)

            if show_info.status:
                status = obj.status()
                color_tag = self.color_tag(status)
                message.add(f"({status})", color_tag)

            message.add("\n")

        return message

    def show_predecessors(self, predecessors: List['VObject'], total: int) -> Message:  # pylint: disable=too-many-locals
        """ Show the predecessors of the object with dynamic alignment """
        message = Message()
        message.add("o--> Predecessors:\n", "title0")

        if not predecessors:
            return message

        # 1. Sort the predecessors
        yaml_file = metadata.YamlFile(os.path.join(self.path, "celebi.yaml"))
        alias_list = yaml_file.read_variable("alias", [])

        predecessors.sort(
            key=lambda x: alias_list.index(self.path_to_alias(x.invariant_path()))
            if self.path_to_alias(x.invariant_path()) in alias_list
            else -1,
        )

        # 2. Pre-process data and calculate maximum widths
        processed_data = []
        max_order_w = 0
        max_type_w = 0
        max_alias_w = 0

        for index, pred_object in enumerate(predecessors):
            order_str = f"[{total + index}]"
            obj_type = f"({pred_object.object_type()})"
            alias = self.path_to_alias(pred_object.invariant_path()) or "code"
            pred_path = f"@/{pred_object.invariant_path()}"

            processed_data.append((order_str, obj_type, alias, pred_path))

            # Update max widths
            max_order_w = max(max_order_w, len(order_str))
            max_type_w = max(max_type_w, len(obj_type))
            max_alias_w = max(max_alias_w, len(alias))

        # 3. Emit each predecessor with dynamic padding
        for order, obj_type, alias, pred_path in processed_data:
            line = (
                f"{order:>{max_order_w}} "
                f"{obj_type:<{max_type_w + 1}} "
                f"{alias:<{max_alias_w}}: "
                f"{pred_path}\n"
            )
            message.add(line)

        return message

    def show_successors(self, successors: List['VObject'], total: int) -> Message:
        """ Show the successors of the object"""
        message = Message()
        message.add("-->o Successors:\n", "title0")
        for index, succ_object in enumerate(successors):
            alias = self.path_to_alias(succ_object.invariant_path())
            order = f"[{total+index}]"
            succ_path = (
                succ_object.invariant_path()
            )
            obj_type = f"({succ_object.object_type()})"
            message.add(f"{order} {obj_type:<12} {alias:>10}: @/{succ_path:<20}\n")
        return message

    def tree(self, max_depth=999, current_depth=0):
        message = Message()
        index = "--" * current_depth
        message.add(f"{index}{os.path.basename(self.path)}({self.object_type()})\n")
        objects = sorted(self.sub_objects(), key=lambda x: x.path)
        for obj in objects:
            message.append(obj.tree(max_depth, current_depth+1))
        return message