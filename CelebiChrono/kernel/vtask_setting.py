""" This module contains the SettingManager class which is responsible
    for managing the settings of the task.
    It reads the settings from the celebi.yaml file and provides methods
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
from ..utils.lb_run import validated_lb_run_spec
from ..utils.subtasks import read_subtask_count
from .vtask_core import Core

logger = getLogger("ChernLogger")

class SettingManager(Core):
    """ SettingManager class is responsible for managing the settings of the task.
    """
    def subtasks(self):
        """Return the repeat count, or None for an ordinary task."""
        config = metadata.YamlFile(join(self.path, "celebi.yaml"))
        return read_subtask_count(config)

    def environment(self):
        """
        Read the environment file
        """
        parameters_file = metadata.YamlFile(join(self.path, "celebi.yaml"))
        environment = parameters_file.read_variable("environment", "")
        return environment

    def memory_limit(self):
        """
        Read the memory limit file
        """
        parameters_file = metadata.YamlFile(join(self.path, "celebi.yaml"))
        memory_limit = parameters_file.read_variable(
            "memory_limit", "")
        # Backward compatibility
        # ---------------------------------------------
        if not memory_limit:
            memory_limit = parameters_file.read_variable(
                "kubernetes_memory_limit", "")
        # ---------------------------------------------
        return memory_limit

    def task_commands(self):
        """
        Read the task's own commands from celebi.yaml.
        """
        parameters_file = metadata.YamlFile(join(self.path, "celebi.yaml"))
        return parameters_file.read_variable("commands", [])

    def parameters(self):
        """
        Read the parameters file
        """
        parameters_file = metadata.YamlFile(join(self.path, "celebi.yaml"))
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

    def cache_on_runner(self):
        """
        Return whether to cache results on the runner
        """
        return self.config_file.read_variable("cache_on_runner", False)

    # Modifying Settings
    def add_parameter(self, parameter, value):
        """
        Add a parameter to the parameters file
        """
        if parameter == "index" and self.subtasks() is not None:
            raise ValueError("index is reserved when subtasks is configured")
        parameters_file = metadata.YamlFile(join(self.path, "celebi.yaml"))
        parameters = parameters_file.read_variable("parameters", {})
        parameters[parameter] = value
        parameters_file.write_variable("parameters", parameters)

    def remove_parameter(self, parameter):
        """
        Remove a parameter to the parameters file
        """
        parameters_file = metadata.YamlFile(join(self.path, "celebi.yaml"))
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

    def set_cache_on_runner(self, cache_on_runner):
        """
        Set whether to cache results on the runner (EOS on reana,
        the runner's impressions dir on ssh)
        """
        self.config_file.write_variable("cache_on_runner", cache_on_runner)

    def set_environment(self, environment):
        """
        Set the environment
        """
        parameters_file = metadata.YamlFile(join(self.path, "celebi.yaml"))
        parameters_file.write_variable("environment", environment)

    def set_memory_limit(self, memory_limit):
        """
        Set the memory limit
        """
        parameters_file = metadata.YamlFile(join(self.path, "celebi.yaml"))
        parameters_file.write_variable("memory_limit", memory_limit)

    # Validation
    def env_validated(self):
        """
        Check whether the environment is validated or not
        """
        if self.environment() in ("rawdata", "datalist", "lhcb_ap_datalist"):
            return True
        if self.task_commands():
            return bool(self.environment())
        if self.algorithm() is not None:
            if self.algorithm().environment() == "script":
                return True
            if self.environment() == self.algorithm().environment():
                return True
        return False

    def lb_run_validated(self):
        """Validate lb-run against the task and effective command source."""
        task_yaml = metadata.YamlFile(join(self.path, "celebi.yaml"))
        command_yaml = task_yaml
        command_environment = self.environment()
        if not self.task_commands():
            algorithm = self.algorithm()
            if algorithm is not None:
                command_yaml = metadata.YamlFile(
                    join(algorithm.path, "celebi.yaml"))
                command_environment = algorithm.environment()

        raw = command_yaml.read_variable("lb_run", None)
        _keys, parameters = self.parameters()

        def substitute(value):
            for key, replacement in parameters.items():
                value = value.replace("${" + key + "}", str(replacement))
            return value

        try:
            validated_lb_run_spec(
                self.environment(), command_environment, raw, substitute)
        except ValueError:
            return False
        return True

    def validated(self):
        """
        Check whether the task is validated or not
        """
        try:
            self.subtasks()
        except ValueError:
            return False
        if not self.env_validated():
            return False
        if not self.lb_run_validated():
            return False
        return True
