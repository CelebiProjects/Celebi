""" This module provides the ExecutionManagement class.
"""
import time
from logging import getLogger
from typing import Optional, TYPE_CHECKING

from ..utils import csys
from ..utils.message import Message
from .chern_communicator import ChernCommunicator
from .vobj_core import Core
from .chern_cache import ChernCache

if TYPE_CHECKING:
    from .vobject import VObject
    from .vimpression import VImpression


CHERN_CACHE = ChernCache.instance()
logger = getLogger("ChernLogger")


def _submission_message(impressions, runner, submission):  # pylint: disable=too-many-return-statements
    """Describe whether submit created, replaced, or reused a workflow."""
    workflow_id = submission.get("workflow_id", "")
    reason = submission.get("submission_reason", "")
    workflow_status = submission.get("workflow_status", "") or "unknown"
    if reason == "active":
        return (f"Workflow {workflow_id} is already active "
                f"({workflow_status}) on {runner}; no duplicate workflow "
                "was created.")
    if reason == "completed":
        return (f"Workflow {workflow_id} is already complete "
                f"({workflow_status}) on {runner}; existing results were reused.")
    if reason == "unknown":
        return (f"Workflow {workflow_id} is still unknown after a status "
                f"refresh on {runner}; no new workflow was created.")
    if reason == "refresh_failed":
        detail = submission.get("refresh_error", "status refresh failed")
        return (f"Could not refresh unknown workflow {workflow_id} on {runner}: "
                f"{detail}. No new workflow was created.")
    if reason == "not_retryable":
        return (f"Workflow {workflow_id} refreshed to {workflow_status} on "
                f"{runner}; no new workflow was created.")
    if reason == "replacement":
        previous = submission.get("previous_workflows", {})
        attempts = sorted({
            (details.get("workflow_id", ""),
             details.get("workflow_status")
             or details.get("job_status", "failed"))
            for details in previous.values()
            if details.get("workflow_id")
        })
        labels = ", ".join(f"{old_id} ({status})"
                           for old_id, status in attempts)
        if labels and workflow_id:
            noun = "workflow" if len(attempts) == 1 else "workflows"
            verb = "was" if len(attempts) == 1 else "were"
            return (f"Previous {noun} {labels} {verb} replaced by workflow "
                    f"{workflow_id} on {runner}.")
    if submission.get("status") == "scheduled" and workflow_id:
        return (f"Created workflow {workflow_id} on {runner} for impressions "
                f"{impressions}.")
    return f"Impressions {impressions} submitted to {runner}."


def _submission_level(submission):
    """Warn when an explicit unknown refresh did not permit submission."""
    if submission.get("submission_reason") in (
            "unknown", "refresh_failed", "not_retryable"):
        return "warning"
    return "info"


class ExecutionManagement(Core):  # pylint: disable=too-many-public-methods
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

    # pylint: disable=too-many-locals
    def submit(self, runner: str = "local", timeout: Optional[float] = None,
               with_unknown: bool = False) -> Message:
        """ Submit the impression to the runner. """
        now = time.time()
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
        project_path = self.project_path()
        with CHERN_CACHE.freeze_project_modification_time(project_path) as initial_mtime:
            self.deposit(now)
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
        cache_on_runner = {}
        sub_objects = self.sub_objects_recursively()
        for sub_object in sub_objects:
            if not sub_object.is_task():
                continue
            task = self.get_vtask(sub_object.path)
            cache_on_runner[task.impression().uuid] = task.cache_on_runner()
        impressions = self.get_impressions()
        if (initial_mtime is not None
                and csys.dir_mtime(project_path) != initial_mtime):
            msg = Message()
            msg.add(
                "Project files changed while the workflow was being prepared; "
                "submission was stopped. Please submit again.",
                "warning",
            )
            return msg
        logger.info(
            "event=workflow_submit_started runner=%s impressions=%d",
            runner,
            len(impressions),
        )
        submission = cherncc.execute(
            impressions, cache_on_runner, runner, timeout=timeout,
            with_unknown=with_unknown)
        logger.info(
            "event=workflow_submit_completed runner=%s impressions=%d "
            "submission_status=%s workflow=%s duration=%dms",
            runner,
            len(impressions),
            submission.get("status", "unknown"),
            submission.get("workflow_id", ""),
            round((time.time() - now) * 1000),
        )
        msg = Message()
        msg.add(_submission_message(impressions, runner, submission),
                _submission_level(submission))
        return msg

    # pylint: disable=too-many-locals,too-many-branches
    def submit_objects(
            self, objects, runner: str = "local",
            timeout: Optional[float] = None,
            with_unknown: bool = False) -> Message:
        """ Submit multiple objects collectively.

        Similar to submit() on a directory, but only processes the given
        objects and their recursive sub-tasks.
        """
        now = time.time()
        cherncc = ChernCommunicator.instance()
        # Check the connection
        dite_status = cherncc.dite_status()
        if dite_status != "connected":
            msg = Message()
            msg.add("DITE is not connected. Please check the connection.", "warning")
            return msg

        # Collect all tasks recursively from the given objects
        tasks = []
        for obj in objects:
            if obj.is_algorithm():
                continue
            if obj.is_task():
                tasks.append(self.get_vtask(obj.path))
            elif not obj.is_task_or_algorithm():
                for sub_object in obj.sub_objects_recursively():
                    if sub_object.is_task():
                        tasks.append(self.get_vtask(sub_object.path))

        if not tasks:
            msg = Message()
            msg.add("No tasks to submit.", "warning")
            return msg

        project_path = self.project_path()
        with CHERN_CACHE.freeze_project_modification_time(project_path) as initial_mtime:
            for task in tasks:
                task.deposit(now)

        # Validate runner after depositing the immutable task impressions.
        for task in tasks:
            if task.default_runner() != runner:
                default_runner = task.default_runner()
                msg = Message()
                msg.add(
                    f"Runner mismatch: object target runner is"
                    f" {default_runner}, but submit to {runner}.",
                    "warning"
                )
                return msg

        # Collect cache_on_runner and impressions
        cache_on_runner = {}
        impressions = []
        seen_impressions = set()
        for task in tasks:
            impression = task.impression().uuid
            cache_on_runner[impression] = task.cache_on_runner()
            if impression not in seen_impressions:
                seen_impressions.add(impression)
                impressions.append(impression)
        if (initial_mtime is not None
                and csys.dir_mtime(project_path) != initial_mtime):
            msg = Message()
            msg.add(
                "Project files changed while the workflow was being prepared; "
                "submission was stopped. Please submit again.",
                "warning",
            )
            return msg

        logger.info(
            "event=workflow_submit_started runner=%s impressions=%d",
            runner,
            len(impressions),
        )
        submission = cherncc.execute(
            impressions, cache_on_runner, runner, timeout=timeout,
            with_unknown=with_unknown)
        logger.info(
            "event=workflow_submit_completed runner=%s impressions=%d "
            "submission_status=%s workflow=%s duration=%dms",
            runner,
            len(impressions),
            submission.get("status", "unknown"),
            submission.get("workflow_id", ""),
            round((time.time() - now) * 1000),
        )
        msg = Message()
        msg.add(_submission_message(impressions, runner, submission),
                _submission_level(submission))
        return msg

    def kill(self) -> Message:
        """Kill the current impressions of every task in this directory."""
        tasks = [
            self.get_vtask(obj.path)
            for obj in self.sub_objects_recursively()
            if obj.is_task()
        ]
        msg = Message()
        impressions = []
        for task in tasks:
            impression = task.impression()
            if impression is None:
                continue
            impressions.append(impression)

        if not impressions:
            msg.add("No task impressions to kill.", "warning")
            return msg
        cherncc = ChernCommunicator.instance()
        for impression in impressions:
            cherncc.kill(impression)
        impression_uuids = [impression.uuid for impression in impressions]
        msg.add(f"Impressions {impression_uuids} killed.", "info")
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
        cherncc.deposit(self.impression(), self.path)
        consult_table[self.path] = (consult_id, True)

    def is_deposited(self) -> bool:
        """ Judge whether deposited or not. Return a True or False. """
        if not self.is_impressed_fast():
            return False
        cherncc = ChernCommunicator.instance()
        return cherncc.is_deposited(self.impression()) == "TRUE"

    def job_status(self, consult_id=None, runner: Optional[str] = None,
                   live: bool = False) -> str:
        """ Get the status of the job"""
        consult_table = CHERN_CACHE.job_status_consult_table
        if consult_id is not None:
            entry = consult_table.get(self.path)
            if entry is not None and entry[0] == consult_id:
                return entry[1]

        if consult_id is None:
            consult_id = time.time()

        if not self.is_task_or_algorithm():
            sub_objects = self.sub_objects()
            # Topological sort: leaves first to warm predecessor caches.
            # Read predecessor count from config to avoid constructing VObjects.
            sub_objects.sort(
                key=lambda obj: len(obj.config_file.read_variable("predecessors", []))
            )
            pending = False
            for sub_object in sub_objects:
                if sub_object.object_type() == "algorithm":
                    continue
                status = (sub_object.job_status(consult_id, runner, live=True)
                          if live else sub_object.job_status(consult_id, runner))
                if status == "failed":
                    consult_table[self.path] = (consult_id, "failed", "")
                    return "failed"
                if status not in ("finished", "archived", "coda"):
                    pending = True
            if pending:
                consult_table[self.path] = (consult_id, "pending", "")
                return "pending"
            consult_table[self.path] = (consult_id, "finished", "")
            return "finished"
        cherncc = ChernCommunicator.instance()
        if runner is None:
            job_status_data = (cherncc.job_status(self.impression(), wait=True)
                               if live else cherncc.job_status(self.impression()))
            # Extract legacy status string from dict returned by communicator
            job_status = (
                job_status_data.get("status_legacy", "unknown")
                if isinstance(job_status_data, dict) else job_status_data
            )
            detailed_status = (
                job_status_data.get("detailed_status", "")
                if isinstance(job_status_data, dict) else ""
            )
            if job_status == "success":
                job_status = "finished"
            consult_table[self.path] = (consult_id, job_status, detailed_status)
            return job_status
        job_status_data = (cherncc.job_status(
            self.impression(), runner, wait=True) if live
                           else cherncc.job_status(self.impression(), runner))
        job_status = (
            job_status_data.get("status_legacy", "unknown")
            if isinstance(job_status_data, dict) else job_status_data
        )
        detailed_status = (
            job_status_data.get("detailed_status", "")
            if isinstance(job_status_data, dict) else ""
        )
        if job_status == "success":
            job_status = "finished"
        consult_table[self.path] = (consult_id, job_status, detailed_status)
        return job_status

    def job_status_detail(self, consult_id = None, runner: Optional[str] = None) -> str:
        """ Get the detailed status message of the job, if any.

        Reads the consult-table entry populated by job_status(); triggers the
        fetch itself when the entry is missing or stale.
        """
        consult_table = CHERN_CACHE.job_status_consult_table
        if consult_id is None:
            consult_id = time.time()
        entry = consult_table.get(self.path)
        if entry is None or entry[0] != consult_id:
            self.job_status(consult_id, runner)
            entry = consult_table.get(self.path)
        if entry is not None and len(entry) > 2:
            return entry[2]
        return ""

    def set_cache_on_runner(self, cache_on_runner: bool) -> None:
        """ Set whether to use EOS for this task. """
        if not self.is_task_or_algorithm():
            sub_objects = self.sub_objects()
            for sub_object in sub_objects:
                sub_object.set_cache_on_runner(cache_on_runner)
            return
        if not self.is_task():
            return
        self.config_file.write_variable("cache_on_runner", cache_on_runner)

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

    def docker_test(self) -> Message:
        """Run docker test for the object."""
        print("Running docker test... in object")
        if not self.is_task():
            msg = Message()
            msg.add("Docker test can only be run on a task.", "warning")
            return msg
        self.get_vtask(self.path).docker_test()
        msg = Message()
        msg.add("Docker test executed for task.", "info")
        return msg

    def ssh_test(self, runner: str = "") -> Message:
        """Run an ssh test for the task on a registered runner."""
        if not self.is_task():
            msg = Message()
            msg.add("SSH test can only be run on a task.", "warning")
            return msg
        return self.get_vtask(self.path).ssh_test(runner)

    def check_results(self, runner: str = "") -> Message:
        """Mount the task's cached impression results into a check dir on
        the runner."""
        if not self.is_task():
            msg = Message()
            msg.add("Check results can only be run on a task.", "warning")
            return msg
        return self.get_vtask(self.path).check_results(runner)

    def collect(self, contents="", allow_failed=False) -> Message:
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
            msg = Message()
            for sub_object in sub_objects:
                if not sub_object.is_task():
                    continue
                sub_msg = (sub_object.collect(contents, allow_failed=True)
                           if allow_failed else sub_object.collect(contents))
                if sub_msg:
                    msg.append(sub_msg)
            if not msg.messages:
                msg.add("No task results to collect.", "info")
            else:
                msg.add("Results of sub-tasks collected.", "info")
            return msg
        if self.is_task():
            task = self.get_vtask(self.path)
            return (task.collect(contents, allow_failed=True)
                    if allow_failed else task.collect(contents))
        # It's an algorithm
        msg = Message()
        msg.add(f"Algorithm {self.path} doesn't have results to collect.", "info")
        return msg

    def homekeep(self) -> Message:
        """Clean the runner workflow"""
        cherncc = ChernCommunicator.instance()
        dite_status = cherncc.dite_status()
        if dite_status != "connected":
            msg = Message()
            msg.add("DITE is not connected. Please check the connection.", "warning")
            return msg
        cherncc.homekeep(self.project_uuid())
        msg = Message()
        msg.add("Homekeep operation completed.", "info")
        return msg
