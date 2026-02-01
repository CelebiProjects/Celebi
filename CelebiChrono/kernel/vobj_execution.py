""" This module provides the ExecutionManagement class.
"""
import time
from logging import getLogger
from typing import Optional, TYPE_CHECKING

from ..utils.message import Message
from .chern_communicator import ChernCommunicator
from .vobj_core import Core
from .chern_cache import ChernCache

if TYPE_CHECKING:
    from .vobject import VObject
    from .vimpression import VImpression


CHERN_CACHE = ChernCache.instance()
logger = getLogger("ChernLogger")


class ExecutionManagement(Core):
    """ Manage the contact with dite and runner. """
    def is_submitted(self, runner: str = "local") -> bool: # pylint: disable=unused-argument
        """ Judge whether submitted or not. Return a True or False.
        """
        # FIXME: incomplete
        if not self.is_impressed_fast():
            return False
        return False

    def get_impressions(self) -> list[str]:
        """ Get the impressions of the object.
        """
        if not self.is_task_or_algorithm():
            sub_objects = self.sub_objects()
            impressions = []
            for sub_object in sub_objects:
                impressions.extend(sub_object.get_impressions())
            return impressions
        impression = self.impression()
        if impression is None:
            return []
        return [impression.uuid]

    def submit(self, runner: str = "local") -> Message:
        """ Submit the impression to the runner. """
        cherncc = ChernCommunicator.instance()
        # Check the connection
        dite_status = cherncc.dite_status()
        if dite_status != "connected":
            msg = Message()
            msg.add("DITE is not connected. Please check the connection.", "warning")
            # logger.error(msg)
            return msg
        if self.is_algorithm():
            msg = Message()
            msg.add("Cannot submit an algorithm directly. Please submit its tasks.", "warning")
            return msg
        self.deposit()
        if not self.is_task_or_algorithm():
            sub_objects = self.sub_objects_recursively()
            for sub_object in sub_objects:
                if not sub_object.is_task():
                    continue
                default_runner = self.get_vtask(sub_object.path).default_runner()
                if default_runner != runner:
                    msg = Message()
                    msg.add(
                            f"Runner mismatch: some object target runner is"
                            f" {default_runner}, but submit to {runner}.",
                            "warning"
                            )
                    return msg
        else:
            if self.is_task() and self.get_vtask(self.path).default_runner() != runner:
                default_runner = self.get_vtask(self.path).default_runner()
                msg = Message()
                msg.add(
                        f"Runner mismatch: object target runner is"
                        f" {default_runner}, but submit to {runner}.",
                        "warning"
                        )
                return msg
        use_eos = {}
        sub_objects = self.sub_objects_recursively()
        for sub_object in sub_objects:
            if not sub_object.is_task():
                continue
            task = self.get_vtask(sub_object.path)
            use_eos[task.impression().uuid] = task.use_eos()
        impressions = self.get_impressions()
        cherncc.execute(impressions, use_eos, runner)
        msg = Message()
        msg.add(f"Impressions {impressions} submitted to {runner}.", "info")
        return msg

    def purge(self, _: str = "local") -> Message:
        """ Submit the impression to the runner. """
        cherncc = ChernCommunicator.instance()
        # Check the connection
        dite_status = cherncc.dite_status()
        if dite_status != "connected":
            msg = Message()
            msg.add("DITE is not connected. Please check the connection.", "warning")
            # logger.error(msg)
            return msg
        impressions = self.get_impressions()
        cherncc.purge(impressions)
        msg = Message()
        msg.add(f"Impressions {impressions} purged.", "info")
        return msg

    def purge_old_impressions(self) -> Message:
        """ Purge old impressions from the dite. """
        cherncc = ChernCommunicator.instance()
        # Check the connection
        dite_status = cherncc.dite_status()
        if dite_status != "connected":
            msg = Message()
            msg.add("DITE is not connected. Please check the connection.", "warning")
            # logger.error(msg)
            return msg
        impressions = self.sub_objects_recursively_parents()
        cherncc.purge(impressions)
        msg = Message()
        msg.add(f"Old impressions {impressions} purged.", "info")
        return msg

    def resubmit(self, runner: str = "local") -> None:
        """ Resubmit the impression to the runner. """
        # FIXME: incomplete

    def deposit(self, consult_id=None) -> None:
        """ Deposit the impression to the dite. """
        now = time.time()
        if consult_id is not None:
            now = consult_id

        # print("Time: ", now)

        if not self.is_task_or_algorithm():
            sub_objects = self.sub_objects()
            for sub_object in sub_objects:
                sub_object.deposit(now)
            return

        self.deposit_with_dependencies(now)
        # cherncc = ChernCommunicator.instance()
        # if self.is_deposited():
        #     return
        # if not self.is_impressed_fast():
        #     self.impress()
        # for obj in self.predecessors():
        #     obj.deposit()
        # cherncc.deposit(self.impression())

    def deposit_with_dependencies(self, consult_id) -> None:
        """ Deposit the impression and its dependencies to the dite. """
        consult_table = CHERN_CACHE.deposit_consult_table
        cid, deposited = consult_table.get(self.path, (-1, False))
        # print(consult_id, cid, deposited)
        if cid == consult_id and deposited:
            return
        cherncc = ChernCommunicator.instance()
        if self.is_deposited():
            consult_table[self.path] = (consult_id, True)
            return
        if not self.is_impressed_fast():
            self.impress()
        for obj in self.predecessors():
            obj.deposit_with_dependencies(consult_id)
        cherncc.deposit(self.impression())
        consult_table[self.path] = (consult_id, True)

    def is_deposited(self) -> bool:
        """ Judge whether deposited or not. Return a True or False. """
        if not self.is_impressed_fast():
            return False
        cherncc = ChernCommunicator.instance()
        return cherncc.is_deposited(self.impression()) == "TRUE"

    def job_status(self, consult_id = None, runner: Optional[str] = None) -> str:
        """ Get the status of the job"""
        consult_table = CHERN_CACHE.job_status_consult_table
        if consult_id is not None:
            cid, status = consult_table.get(self.path, (-1, -1))
            if cid == consult_id:
                return status

        if consult_id is None:
            consult_id = time

        if not self.is_task_or_algorithm():
            sub_objects = self.sub_objects()
            pending = False
            for sub_object in sub_objects:
                if sub_object.object_type() == "algorithm":
                    continue
                status = sub_object.job_status(consult_id, runner)
                if status == "failed":
                    consult_table[self.path] = (consult_id, "failed")
                    return "failed"
                if status not in ("finished", "archived"):
                    pending = True
            if pending:
                consult_table[self.path] = (consult_id, "pending")
                return "pending"
            consult_table[self.path] = (consult_id, "finished")
            return "finished"
        cherncc = ChernCommunicator.instance()
        if runner is None:
            job_status = cherncc.job_status(self.impression())
            consult_table[self.path] = (consult_id, job_status)
            return job_status
        job_status = cherncc.job_status(self.impression(), runner)
        consult_table[self.path] = (consult_id, job_status)
        return job_status

    def set_use_eos(self, use_eos: bool) -> None:
        """ Set whether to use EOS for this task. """
        if not self.is_task_or_algorithm():
            sub_objects = self.sub_objects()
            for sub_object in sub_objects:
                sub_object.set_use_eos(use_eos)
            return
        if not self.is_task():
            return
        self.config_file.write_variable("use_eos", use_eos)

    def set_default_runner(self, runner):
        """ Set the default runner for this object """
        if not self.is_task_or_algorithm():
            sub_objects = self.sub_objects()
            for sub_object in sub_objects:
                sub_object.set_default_runner(runner)
            return
        if not self.is_task():
            return
        self.get_vtask(self.path).set_default_runner(runner)

    def add_parameter(self, parameter, value):
        """
        Add a parameter to the parameter file
        """
        if not self.is_task_or_algorithm():
            sub_objects = self.sub_objects()
            for sub_object in sub_objects:
                sub_object.add_parameter(parameter, value)
            return
        if not self.is_task():
            return
        self.get_vtask(self.path).add_parameter(parameter, value)

    def remove_parameter(self, parameter):
        """
        Remove a parameter from the parameter file
        """
        if not self.is_task_or_algorithm():
            sub_objects = self.sub_objects()
            for sub_object in sub_objects:
                sub_object.remove_parameter(parameter)
            return
        if not self.is_task():
            return
        self.get_vtask(self.path).remove_parameter(parameter)

    def collect(self, contents="all") -> Message:
        """ Collect the results from the runner. """
        cherncc = ChernCommunicator.instance()
        # Check the connection
        dite_status = cherncc.dite_status()
        if dite_status != "connected":
            msg = Message()
            msg.add("DITE is not connected. Please check the connection.", "warning")
            # logger.error(msg)
            return msg
        if not self.is_task_or_algorithm():
            sub_objects = self.sub_objects_recursively()
            for sub_object in sub_objects:
                if not sub_object.is_task():
                    continue
                sub_object.collect(contents)
            msg = Message()
            msg.add("Results of sub-tasks collected.", "info")
            return msg
        if self.is_task():
            task = self.get_vtask(self.path)
            task.collect(contents)
            msg = Message()
            msg.add(f"Results of task {self.path} collected.", "info")

        return msg
