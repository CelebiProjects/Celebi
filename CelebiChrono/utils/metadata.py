""" Utility classes to read and write metadata in JSON and YAML files.
"""
import json
import os
import fcntl  # For Unix-based systems
from typing import Any, Optional
import yaml
from . import csys


class ConfigFile():
    """ConfigFile class used to read and write metadata in a JSON file.

    It supports three types:
        - dict
        - list
        - string
    """

    def __init__(self, file_path: str) -> None:
        """Initialize the class with a file path.

        Create the file if it does not initially exist.
        """
        self.file_path = file_path

    def read_variable(self, variable_name: str, default: Optional[Any] = None) -> Any:
        """Get the content of a variable from the JSON file.

        Args:
            variable_name (str): The name of the variable to read.
            default: The default value to return if the variable is not found.

        Returns:
            The value of the variable or the default value.
        """
        if not csys.exists(self.file_path):
            return default
        with open(self.file_path, encoding='utf-8') as f:
            contents = f.read()
            if not contents.strip():
                return default
            data = json.loads(contents)
            return data.get(variable_name, default)

    def write_variable(self, variable_name: str, value: Any) -> None:
        """Write a variable to the JSON file.

        Args:
            variable_name (str): The name of the variable to write.
            value: The value to write.
        """
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not csys.exists(self.file_path):
            with open(self.file_path, "w", encoding='utf-8') as f:
                json.dump({}, f)

        with open(self.file_path, "r+", encoding='utf-8') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            contents = f.read()
            data = json.loads(contents) if contents.strip() else {}
            data[variable_name] = value
            f.seek(0)
            f.truncate()
            json.dump(data, f)
            fcntl.flock(f, fcntl.LOCK_UN)


class TwoTierConfigFile():
    """TwoTierConfigFile class manages shared and local configuration files.

    Supports reading from and writing to both a shared config and a local override config.
    When reading, local config is checked first, then falls back to shared config.
    When writing, values go to the local config to preserve shared defaults.

    Config files:
        - Shared: config.json (e.g., .celebi/config.json)
        - Local: config.local.json (e.g., .celebi/config.local.json)
    """

    def __init__(self, file_path: str) -> None:
        """Initialize with a shared config file path.

        Args:
            file_path: Path to the shared config file (e.g., .celebi/config.json)
        """
        self.file_path = file_path
        # Local config is in the same directory with .local.json extension
        dir_path = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        # Replace .json with .local.json
        local_file_name = file_name.replace('.json', '.local.json')
        self.local_file_path = os.path.join(dir_path, local_file_name)

    def read_variable(self, variable_name: str, default: Optional[Any] = None) -> Any:
        """Get a variable, checking local config first, then shared config.

        Args:
            variable_name: The name of the variable to read.
            default: The default value if the variable is not found.

        Returns:
            The value from local config, shared config, or the default.
        """
        # Check local config first
        if csys.exists(self.local_file_path):
            with open(self.local_file_path, encoding='utf-8') as f:
                contents = f.read()
                if contents.strip():
                    data = json.loads(contents)
                    if variable_name in data:
                        return data[variable_name]

        # Fall back to shared config
        if not csys.exists(self.file_path):
            return default
        with open(self.file_path, encoding='utf-8') as f:
            contents = f.read()
            if not contents.strip():
                return default
            data = json.loads(contents)
            return data.get(variable_name, default)

    def write_variable(self, variable_name: str, value: Any) -> None:
        """Write a variable to the local config file.

        Args:
            variable_name: The name of the variable to write.
            value: The value to write.
        """
        os.makedirs(os.path.dirname(self.local_file_path), exist_ok=True)
        if not csys.exists(self.local_file_path):
            with open(self.local_file_path, "w", encoding='utf-8') as f:
                json.dump({}, f)

        with open(self.local_file_path, "r+", encoding='utf-8') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            contents = f.read()
            data = json.loads(contents) if contents.strip() else {}
            data[variable_name] = value
            f.seek(0)
            f.truncate()
            json.dump(data, f)
            fcntl.flock(f, fcntl.LOCK_UN)


class YamlFile():
    """YamlFile class used to read and write metadata in a YAML file.

    YAML files are similar to JSON but are more human-readable.
    """

    def __init__(self, file_path: str) -> None:
        """Initialize the class with a file path.

        Create the file if it does not initially exist.
        """
        self.file_path = file_path

    def read_variable(self, variable_name: str, default: Optional[Any] = None) -> Any:
        """Get the content of a variable from the YAML file.

        Args:
            variable_name (str): The name of the variable to read.
            default: The default value to return if the variable is not found.

        Returns:
            The value of the variable or the default value.
        """
        if not csys.exists(self.file_path):
            return default
        with open(self.file_path, encoding='utf-8') as f:
            contents = f.read()
            if not contents.strip():
                return default
            data = yaml.load(contents, Loader=yaml.Loader)
            # Check data is of type dict
            if not isinstance(data, dict):
                return default
            return data.get(variable_name, default)

    def write_variable(self, variable_name: str, value: Any) -> None:
        """Write a variable to the YAML file.

        Args:
            variable_name (str): The name of the variable to write.
            value: The value to write.
        """
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not csys.exists(self.file_path):
            with open(self.file_path, "w", encoding='utf-8') as f:
                yaml.dump({}, f)

        with open(self.file_path, "r+", encoding='utf-8') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            contents = f.read()
            data = (
                yaml.load(contents, Loader=yaml.Loader)
                if contents.strip()
                else {}
            )
            data[variable_name] = value
            f.seek(0)
            f.truncate()
            yaml.dump(data, f)
            fcntl.flock(f, fcntl.LOCK_UN)
