""" This module defines the file manager for the VTask.
"""
from os.path import join
from logging import getLogger
from typing import TYPE_CHECKING

from ..utils import metadata
from ..utils import csys
from .vtask_core import Core

if TYPE_CHECKING:
    from .vimpression import VImpression

logger = getLogger("ChernLogger")


class FileManager(Core):
    """ The file manager for the VTask."""

    def input_md5(self) -> str:
        """ Get the md5 of the input files"""
        parameters_file = metadata.YamlFile(join(self.path, "chern.yaml"))
        return parameters_file.read_variable("uuid", "")

    def set_input_md5(self, path: str) -> str:
        """ Set the md5 of the input files"""
        md5 = csys.dir_md5(path)
        parameters_file = metadata.YamlFile(join(self.path, "chern.yaml"))
        parameters_file.write_variable("uuid", md5)
        return md5

    def output_md5(self) -> str:
        """ Get the md5 of the output files"""
        output_md5s = self.config_file.read_variable("output_md5s", {})
        return output_md5s.get(self.impression(), "")
