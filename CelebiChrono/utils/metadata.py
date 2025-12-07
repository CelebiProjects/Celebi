""" Utility classes to read and write metadata in JSON and YAML files.
"""
import json
import os
import fcntl  # For Unix-based systems
from typing import Any, Optional
import yaml


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
        if not os.path.exists(self.file_path):
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
        if not os.path.exists(self.file_path):
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
        if not os.path.exists(self.file_path):
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
        if not os.path.exists(self.file_path):
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
