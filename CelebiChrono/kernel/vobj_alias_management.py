""" This module is used to manage the alias of the vobj.
"""
import os
from logging import getLogger
from typing import List, TYPE_CHECKING

from ..utils import csys
from ..utils import metadata
from .vobj_core import Core

if TYPE_CHECKING:
    from .vimpression import VImpression

logger = getLogger("ChernLogger")


class AliasManagement(Core):
    """ This class is used to manage the alias of the vobj.
    """
    def path_to_alias(self, path: str) -> str: # UnitTest: DONE
        """ Get the alias of the vobj by the path."""
        path_to_alias = self.config_file.read_variable("path_to_alias", {})
        return path_to_alias.get(path, "")

    def alias_to_path(self, alias: str) -> str: # UnitTest: DONE
        """ Get the path of the vobj by the alias."""
        alias_to_path = self.config_file.read_variable("alias_to_path", {})
        return alias_to_path.get(alias, "")

    def alias_to_impression(self, alias: str) -> 'VImpression': # UnitTest: DONE
        """ Get the impression of the vobj by the alias."""
        path = self.alias_to_path(alias)
        obj = self.get_vobject(os.path.join(csys.project_path(self.path), path))
        return obj.impression()

    def has_alias(self, alias: str) -> bool: # UnitTest: DONE
        """ Check if the alias is in the alias list."""
        alias_to_path = self.config_file.read_variable("alias_to_path", {})
        return alias in alias_to_path.keys()

    def remove_alias(self, alias: str, ignore_yaml: bool = False) -> None: # UnitTest: DONE
        """ Remove the alias from the alias list."""
        if alias == "":
            return
        alias_to_path = self.config_file.read_variable("alias_to_path", {})
        path_to_alias = self.config_file.read_variable("path_to_alias", {})
        path = alias_to_path[alias]
        path_to_alias.pop(path)
        alias_to_path.pop(alias)
        self.config_file.write_variable("alias_to_path", alias_to_path)
        self.config_file.write_variable("path_to_alias", path_to_alias)
        if not ignore_yaml:
            yaml_file = metadata.YamlFile(os.path.join(self.path, "chern.yaml"))
            yaml_alias = yaml_file.read_variable("alias", [])
            if alias in yaml_alias:
                yaml_alias.remove(alias)
                yaml_file.write_variable("alias", yaml_alias)

    def set_alias(self, alias: str, path: str, ignore_yaml: bool = False) -> None: # UnitTest: DONE
        """ Set the alias of the vobj by the path."""
        if alias == "":
            return
        if self.has_alias(alias):
            logger.warning("Alias '%s' already exists. Will not overwrite.", alias)
            return
        path_to_alias = self.config_file.read_variable("path_to_alias", {})
        alias_to_path = self.config_file.read_variable("alias_to_path", {})
        if path_to_alias.get(path, "") != "":
            logger.warning("Path '%s' already has an alias. Will not overwrite.", alias)
            return
        path_to_alias[path] = alias
        alias_to_path[alias] = path
        self.config_file.write_variable("path_to_alias", path_to_alias)
        self.config_file.write_variable("alias_to_path", alias_to_path)
        if not ignore_yaml:
            yaml_file = metadata.YamlFile(os.path.join(self.path, "chern.yaml"))
            yaml_alias = yaml_file.read_variable("alias", [])
            if alias not in yaml_alias:
                yaml_alias.append(alias)
                yaml_file.write_variable("alias", yaml_alias)

    def get_alias_list(self) -> List[str]: # UnitTest: DONE
        """ Get the alias list."""
        alias_to_path = self.config_file.read_variable("alias_to_path", {})
        return alias_to_path.keys()
