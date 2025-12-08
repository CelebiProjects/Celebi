""" VAlgorithm
"""
import os
import shutil
from typing import List, Tuple

from ..utils import csys
from ..utils import metadata
from ..utils.message import Message

from .chern_cache import ChernCache
from .chern_communicator import ChernCommunicator
from . import helpme
from .vobject import VObject
from .vobj_file import LsParameters

CHERN_CACHE = ChernCache.instance()


class VAlgorithm(VObject):
    """ Algorithm class
    """

    def helpme(self, command: str) -> Message:
        """ Helpme function """
        message = Message()
        message.add(helpme.algorithm_helpme.get(command, "No such command, try ``helpme'' alone."))
        return message

    def printed_status(self) -> Message:
        """ Print the status """
        message = super().printed_status()
        cherncc = ChernCommunicator.instance()
        dite_status = cherncc.dite_status()
        if dite_status != "connected":
            return message
        workflow_check = cherncc.workflow(self.impression())
        if workflow_check == "UNDEFINED":
            message.add("Workflow not defined\n")
        return message

    def run_status(self) -> str:
        """ Asking for the remote status
        """
        cherncc = ChernCommunicator.instance()
        return cherncc.status(self.impression())

    def is_submitted(self, runner: str = "local") -> bool:
        """ Judge whether submitted or not. Return a True or False.
        [FIXME: incomplete]
        """
        if not self.is_impressed_fast():
            return False
        return False

    def resubmit(self, runner: str = "local") -> None:
        """ Resubmit """
        # FIXME: fixit later


    def ls(self, show_info: LsParameters = LsParameters()) -> Message:
        """ list the infomation.
        """
        message = super().ls(show_info)

        if show_info.status:
            status = self.status()
            status_str = f"[{status}]"
            message.add("**** STATUS: ", "title0")
            message.add(status_str)
            message.add("\n")

        message.append(self.print_files(self.path, excluded=(".chern", "chern.yaml", "README.md")))

        environment = self.environment()
        message.add(f"---- Environment: {environment}\n", "title0")

        build_commands = self.build_commands()
        if build_commands:
            message.add("---- Build commands:\n", "title0")
            for command in build_commands:
                message.add(command + "\n")

        commands = self.commands()
        if commands:
            message.add("---- Commands:\n", "title0")
            for command in commands:
                message.add(command + "\n")

        return message


    def print_files(self, path: str, excluded: Tuple[str, ...] = ()) -> Message:
        """ Print the files in the path """
        message = Message()
        message.add("---- Files:\n", "title0")

        files = [f for f in os.listdir(path) if not f.startswith(".") and f not in excluded]
        if not files:
            message.add("No files found.\n")
            return message

        terminal_width = shutil.get_terminal_size((80, 20)).columns
        max_length = max(len(f) for f in files) + 2  # padding
        num_columns = max(1, terminal_width // max_length)

        line = ""
        for i, f in enumerate(files):
            line += f.ljust(max_length)
            if (i + 1) % num_columns == 0:
                message.add(line + "\n")
                line = ""
        if line:
            message.add(line + "\n")

        return message

    def commands(self) -> List[str]:
        """ Get the commands from the yaml file """
        yaml_file = metadata.YamlFile(os.path.join(self.path, "chern.yaml"))
        return yaml_file.read_variable("commands", [])

    def build_commands(self) -> List[str]:
        """ Get the build commands from the yaml file """
        yaml_file = metadata.YamlFile(os.path.join(self.path, "chern.yaml"))
        return yaml_file.read_variable("build", [])

    def environment(self) -> str:
        """ Get the environment
        """
        yaml_file = metadata.YamlFile(os.path.join(self.path, "chern.yaml"))
        return yaml_file.read_variable("environment", "")

def create_algorithm(path: str, use_template: bool = False) -> None:
    """ Create an algorithm """
    path = csys.strip_path_string(path)
    os.mkdir(path)
    os.mkdir(f"{path}/.chern")
    config_file = metadata.ConfigFile(f"{path}/.chern/config.json")
    config_file.write_variable("object_type", "algorithm")

    with open(f"{path}/.chern/README.md", "w", encoding="utf-8") as readme_file:
        readme_file.write("Please write README for this algorithm")
    # subprocess.call(f"vim {path}/.chern/README.md", shell=True)
    if use_template:
        template_name = input("Please input the Dockerfile template type")
        print("Creating template, but ...")
        print("Not implemented yet.")
        print(f"Template name: {template_name}")
        # FIXME: implement it later
