# pylint: disable=too-many-public-methods
""" Core class for vtasks.
    + helpme: Print help message for the command.
    + ls: List the information of the task.
"""

import os
from abc import abstractmethod
from logging import getLogger
from typing import Tuple, List, Optional, TYPE_CHECKING

from . import helpme
from ..utils.message import Message
from .vobject import VObject
from .vobj_file import LsParameters

if TYPE_CHECKING:
    from .valgorithm import VAlgorithm

logger = getLogger("ChernLogger")


class Core(VObject):
    """ Core class for vtasks.
    """
    def helpme(self, command: str) -> Message:
        """ Print help message for the command.
        """
        message = Message()
        message.add(helpme.task_helpme.get(command, "No such command, try ``helpme'' alone."))
        return message

    def ls(self, show_info: LsParameters = LsParameters()) -> Message:
        """ List the information of the task.
        """
        message = super().ls(show_info)

        message.append(self.show_parameters())

        # if show_info.status:
        #    message.append(self.show_status())

        if self.algorithm() is not None:
            message.append(self.show_algorithm())

        return message

    def show_parameters(self) -> Message:
        """ Show the parameters of the task.
        """
        parameters, values = self.parameters()
        message = Message()

        if parameters:
            message.add("---- Parameters:\n", "title0")
            for parameter in parameters:
                message.add(f"{parameter} = {values[parameter]}\n")

        if self.environment() == "rawdata":
            message.add("---- Input data: ", "title0")
            message.add(f"{self.input_md5()}")
            message.add("\n")

        message.add("Environment: ", "title0")
        message.add(f"{self.environment()}")
        message.add("\n")

        message.add("Memory limit: ", "title0")
        message.add(f"{self.memory_limit()}")
        message.add("\n")

        validated_str = "True" if self.validated() else "False"
        message.add("Validated: ", "title0")
        message.add(f"{validated_str}")
        message.add("\n")

        message.add("Auto download: ", "title0")
        message.add(f"{self.auto_download()}")
        message.add("\n")

        message.add("Default runner: ", "title0")
        message.add(f"{self.default_runner()}")
        message.add("\n")


        return message

    def show_algorithm(self) -> Message:
        """ Show the algorithm of the task.
        """
        message = Message()

        message.add("---- Algorithm files:\n", "title0")

        files = os.listdir(self.algorithm().path)
        if not files:
            return message

        files = sorted(f for f in files
            if not f.startswith(".") and f not in ["README.md", "chern.yaml"])
        if not files:
            return message

        max_len = max(len(f) for f in files)
        columns = os.get_terminal_size().columns
        nfiles = max(1, columns // (max_len + 4 + 11))  # Avoid division by zero
        line = ""

        for i, f in enumerate(files, start=1):
            line += f"code:{f:<{max_len+4}}"
            if i % nfiles == 0:
                message.add(line + "\n")
                line = ""
        if line:
            message.add(line + "\n")

        message.add("---- Commands:\n", "title0")
        for command in self.algorithm().commands():
            parameters, values = self.parameters()
            for parameter in parameters:
                command = command.replace("${" + parameter + "}", values[parameter])
            message.add(command + "\n")

        return message

    @abstractmethod
    def get_task(self, path: str) -> 'Core':
        """ Get the task from the path.
        """

    @abstractmethod
    def algorithm(self) -> Optional['VAlgorithm']:
        """ Abstract method for future implementation"""

    @abstractmethod
    def parameters(self) -> Tuple[List[str], dict]:
        """ Abstract method for future implementation"""

    @abstractmethod
    def input_md5(self) -> str:
        """ Abstract method for future implementation"""

    @abstractmethod
    def set_input_md5(self, path: str) -> None:
        """ Abstract method for future implementation"""

    @abstractmethod
    def output_files(self) -> List[str]:
        """ Abstract method for future implementation"""

    @abstractmethod
    def environment(self) -> str:
        """ Abstract method for future implementation"""

    @abstractmethod
    def memory_limit(self) -> str:
        """ Abstract method for future implementation"""

    @abstractmethod
    def validated(self) -> bool:
        """ Abstract method for future implementation"""

    @abstractmethod
    def auto_download(self) -> bool:
        """ Abstract method for future implementation"""

    @abstractmethod
    def default_runner(self) -> str:
        """ Abstract method for future implementation"""

    @abstractmethod
    def send_data(self, path):
        """ Abstract method for future implementation"""

    @abstractmethod
    def inputs(self):
        """ Abstract method for future implementation"""
