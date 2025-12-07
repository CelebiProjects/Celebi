""" This module contains the SettingManager class which is responsible
    for managing the settings of the task.
    It reads the settings from the chern.yaml file and provides methods
    to modify the settings. The settings include the environment, memory limit,
    parameters, auto_download, and default_runner.
    The environment is the type of data that the task is working with.
    The memory limit is the memory limit of the task.
    The parameters are the parameters of the task.
    The auto_download is a boolean value that determines whether the task should
    automatically download the data or not.
    The default_runner is the default runner that the task should use.
    The SettingManager class also provides methods to validate the settings.
    The env_validated method checks whether the environment is validated or not.
    The validated method checks whether the task is validated or not.
"""
from logging import getLogger
from os.path import join

from ..utils import metadata
from .vtask_core import Core

logger = getLogger("ChernLogger")

class SettingManager(Core):
    """ SettingManager class is responsible for managing the settings of the task.
    """
    def environment(self):
        """
        Read the environment file
        """
        parameters_file = metadata.YamlFile(join(self.path, "chern.yaml"))
        environment = parameters_file.read_variable("environment", "")
        return environment

    def memory_limit(self):
        """
        Read the memory limit file
        """
        parameters_file = metadata.YamlFile(join(self.path, "chern.yaml"))
        memory_limit = parameters_file.read_variable(
            "memory_limit", "")
        # Backward compatibility
        # ---------------------------------------------
        if not memory_limit:
            memory_limit = parameters_file.read_variable(
                "kubernetes_memory_limit", "")
        # ---------------------------------------------
        return memory_limit

    def parameters(self):
        """
        Read the parameters file
        """
        parameters_file = metadata.YamlFile(join(self.path, "chern.yaml"))
        parameters = parameters_file.read_variable("parameters", {})
        return sorted(parameters.keys()), parameters

    def auto_download(self):
        """
        Return whether the task is auto_download or not
        """
        return self.config_file.read_variable("auto_download", True)

    def default_runner(self):
        """
        Return the default runner
        """
        return self.config_file.read_variable("default_runner", "local")

    # Modifying Settings
    def add_parameter(self, parameter, value):
        """
        Add a parameter to the parameters file
        """
        parameters_file = metadata.YamlFile(join(self.path, "chern.yaml"))
        parameters = parameters_file.read_variable("parameters", {})
        parameters[parameter] = value
        parameters_file.write_variable("parameters", parameters)

    def remove_parameter(self, parameter):
        """
        Remove a parameter to the parameters file
        """
        parameters_file = metadata.YamlFile(join(self.path, "chern.yaml"))
        parameters = parameters_file.read_variable("parameters", {})
        if parameter not in parameters.keys():
            logger.warning("Parameter '%s' not found in parameters file", parameter)
            return
        parameters.pop(parameter)
        parameters_file.write_variable("parameters", parameters)

    def set_auto_download(self, auto_download):
        """
        Set the auto_download
        """
        self.config_file.write_variable("auto_download", auto_download)

    def set_default_runner(self, runner):
        """
        Set the default runner
        """
        self.config_file.write_variable("default_runner", runner)

    def set_environment(self, environment):
        """
        Set the environment
        """
        parameters_file = metadata.YamlFile(join(self.path, "chern.yaml"))
        parameters_file.write_variable("environment", environment)

    def set_memory_limit(self, memory_limit):
        """
        Set the memory limit
        """
        parameters_file = metadata.YamlFile(join(self.path, "chern.yaml"))
        parameters_file.write_variable("memory_limit", memory_limit)

    # Validation
    def env_validated(self):
        """
        Check whether the environment is validated or not
        """
        if self.environment() == "rawdata":
            return True
        if self.algorithm() is not None:
            if self.algorithm().environment() == "script":
                return True
            if self.environment() == self.algorithm().environment():
                return True
        return False

    def validated(self):
        """
        Check whether the task is validated or not
        """
        if not self.env_validated():
            return False
        return True
