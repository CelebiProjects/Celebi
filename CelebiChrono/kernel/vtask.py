""" The VTask class
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #Methods:
        + helpme:
            Print the helpme of the task
        + ls:
            First call the general ls and then print some other useful information:
            parameters, status, outputs, algorithms
        + output_files:
            Get the information of the output_files from ChernCommunicator
        + get_file:
            Get file??? from ChernCommunicator

        + inputs:
        + outputs:

        + submit
            Submit the job to server. Through ChernCommunicator.
        + resubmit
            Resubmit the job to server. Through ChernCommunicator.
        + view
        + cp
            Copy the output to some directory
        + remove
            Remove the task.
        + jobs
            Query the jobs of the task throught ChernCommunicator.

        + view
            Open the file through ChernCommunicator. This is quite temporatory.
            Because it can only open local file.

        + is_submitted:
            Judge whether the task is submitted or not. Ask this information from
            ChernCommunicator.

        + output_md5:
            Read the md5 of the output directory

        + add_parameter
        + remove_parameter:
            Add/Remove parameter, should deal the problem of missing
            parameter/parameter already there.

        + add_input
            Add input to the task(with alias), print something, maybe changed later.
        + remove_input
            Remove input of the task through alias.

        + add_algorithm
            Add the algorithm correspnding to the task. if already has algorithm, replace the
            old one and print the message. Maybe changed later because I do not want to print
            anything in the kernel.
        + remove_algorithm
            Remove the algorithm corresponding to the task. if nothing to remove it print the
            message. Maybe changed later because I do not want to print anything in the kernel.
        + algorithm
            Return the algorithm corresponding to this task. If the task is not related to an
            algorithm, return None.

        + container
            Return the container corresponding the top impression.
        + add_source
            Make a new task, with raw data.

        ===================
        Inherited from VObject
        + __init__
        + __str__, __repr__
        + invariant_path, relative_path
        + object_type, is_zombine
        + color_tag
        + ls
        + copy_to, clean_impressions/flow
        + rm
        + move_to
        + alias(and related)
        + add/remove_arc_from/to
        + (has)successor/predecessors(s)
        + doctor
        + pack(and related)
        + impression(and related)

"""
import os
from logging import getLogger
from os.path import join

from ..utils import metadata
from ..utils import csys
from ..utils.csys import open_subprocess

from .chern_cache import ChernCache
from .chern_communicator import ChernCommunicator

from .vobject import VObject
from .vtask_input import InputManager
from .vtask_setting import SettingManager
from .vtask_file import FileManager
from .vtask_job import JobManager

CHERN_CACHE = ChernCache.instance()
logger = getLogger("ChernLogger")


class VTask(InputManager, SettingManager, FileManager, JobManager):
    """ The main vtask class
    It contains: Core, InputManager, SettingManager, FileManager, JobManager
    """
    def output_files(self):
        """ [unused]
        """
        return []

    def get_file(self, filename):
        """ Get file from ChernCommunicator
        """
        cherncc = ChernCommunicator.instance()
        return cherncc.get_file("local", self.impression(), filename)

    def view(self, filename):
        """ View the file through ChernCommunicator
        """
        if filename.startswith("local:"):
            path = self.get_file("local:" + filename[6:])
            if not csys.exists(path):
                print(f"File: {path} do not exists")
                return
            with open_subprocess(f"open {path}"):
                pass

    def printed_status(self):
        """ Print the status of the task
        """
        message = super().printed_status()

        if self.status() != "impressed":
            return message

        cherncc = ChernCommunicator.instance()
        dite_status = cherncc.dite_status()
        if dite_status != "connected":
            return message
        job_status = cherncc.job_status(self.impression())
        message.add("Job status: ")
        message.add(f"{'['+job_status+']'}", "success")
        message.add("\n")

        environment = self.environment()
        if environment == "rawdata":
            files = cherncc.output_files(self.impression(), "none")
            message.add("Sample files (collected on DIET):\n", "title0")
            for f in files:
                message.add(f"    {f}\n")
            return message

        workflow_check = cherncc.workflow(self.impression())
        if workflow_check[0] == "UNDEFINED":
            message.add("Workflow not defined", "error")
            message.add("\n")
            return message

        if environment != "rawdata":
            message.add("**** Workflow: ", "title0")
            message.add("\n")
            runner = workflow_check[0]
            workflow = workflow_check[1]
            message.add("Workflow: ")
            message.add(f"[{runner}]", "success")
            message.add(f"[{workflow}]", "success")
            message.add("\n")

            files = cherncc.output_files(self.impression(), runner)
            message.add("Output files (collected on DIET):\n", "title0")
            for f in files:
                message.add(f"    {f}\n")
        return message

    def get_task(self, path):
        """ Get the task from the path
        """
        return VTask(path)


def create_task(path):
    """ Create a task
    """
    path = csys.strip_path_string(path)
    parent_path = os.path.abspath(join(path, ".."))
    object_type = VObject(parent_path).object_type()
    if object_type not in ("project", "directory"):
        return

    csys.mkdir(path+"/.chern")
    config_file = metadata.ConfigFile(path + "/.chern/config.json")
    config_file.write_variable("object_type", "task")
    config_file.write_variable("auto_download", True)
    config_file.write_variable("default_runner", "local")
    task = VObject(path)

    # Create the default chern.yaml file
    yaml_file = metadata.YamlFile(join(path, "chern.yaml"))
    yaml_file.write_variable("environment", "reanahub/reana-env-root6:6.18.04")
    yaml_file.write_variable("memory_limit", "256Mi")

    with open(path + "/.chern/README.md", "w", encoding="utf-8") as f:
        f.write(f"Please write README for task {task.invariant_path()}")


def create_data(path):
    """ Create a data
    """
    path = csys.strip_path_string(path)
    parent_path = os.path.abspath(path+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("project", "directory"):
        return

    csys.mkdir(path+"/.chern")
    config_file = metadata.ConfigFile(path + "/.chern/config.json")
    config_file.write_variable("object_type", "task")
    task = VObject(path)

    with open(path + "/.chern/README.md", "w", encoding="utf-8") as f:
        f.write(f"Please write README for task {task.invariant_path()}")

    yaml_file = metadata.YamlFile(join(path, "chern.yaml"))
    yaml_file.write_variable("environment", "rawdata")
    yaml_file.write_variable("uuid", "")
