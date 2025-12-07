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
        self.deposit()
        impressions = self.get_impressions()
        cherncc.execute(impressions, runner)
        msg = Message()
        msg.add(f"Impressions {impressions} submitted to {runner}.", "info")
        return msg

    def resubmit(self, runner: str = "local") -> None:
        """ Resubmit the impression to the runner. """
        # FIXME: incomplete

    def deposit(self) -> None:
        """ Deposit the impression to the dite. """
        if not self.is_task_or_algorithm():
            sub_objects = self.sub_objects()
            for sub_object in sub_objects:
                sub_object.deposit()
            return

        cherncc = ChernCommunicator.instance()
        if self.is_deposited():
            return
        if not self.is_impressed_fast():
            self.impress()
        for obj in self.predecessors():
            obj.deposit()
        cherncc.deposit(self.impression())

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
