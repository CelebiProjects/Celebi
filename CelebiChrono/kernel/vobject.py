""" Virtual base class for all ```directory'', ``task'', ``algorithm''
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    VObject:
    # Methods:
        + __init__:
            It should be initialized with a absolute path.
            The initialization gets variable "path" and "config_file".
            It is quite light-weight to create a VObject.
            A VObject can be abandoned after using
            and create another when needed.

        + __str__, __repr__:
            For print

        + invariant_path:
            Return the path relative to the project root
        + relative_path(a_path);
            Return the path of the VObject relative to a_path

        + object_type:
            Return the type of the object: project,
            task, directory, or empty("")
        + is_zombine
            To judge whether this object has a type

        + color_tag: (Maybe put it somewhere else?)
            For print

        + ls:
            Realization of "ls" call o.ls()
            will give you the contents of the object

        + add_arc_from(obj)
        + remove_arc_from(obj, single=False)
        + add_arc_to(obj)
        + remove_arc_from(obj, single=False):
            Add or remove arcs,
            the "single" variable is only used for debug usage.

        + successors
        + predecessors:
            Get [objects]
        + has_successor(obj)
        + has_predessor(obj)
            Judge whether obj is the succ/pred of this obj

        + doctor:
            Judge whether it is a good object(with all arc linked)

        + copy_to:
            Copy the object and its contains to a new path. Before the copy,
            all objects in the directory will be impressed.
            The arcs within the directory will be kept
            and outsides will be removed.
        + clean_impressions
        + clean_flow:
            Helpers for copy_to

        + path_to_alias
        + alias_to_path
        + has_alias
        + set_alias
        + remove_alias

        + move_to:
            Move the object to another directory

        + rm:
            Remove the object

        + impression:
            Return the impression of the object
        + impress:
            Make a impression
        + is_impressed:
            Judge whether this object is impressed

        + pack_impression:
        + unpack_impression:
        + is_packed:
            For future transfer purpose


        -----------------------------
        # Communication with the DITE and the Runners
        + dite
"""
import os
from os.path import join
import subprocess
from logging import getLogger
from typing import TYPE_CHECKING

from ..utils import metadata
from .vobj_arc_management import ArcManagement
from .vobj_alias_management import AliasManagement
from .vobj_impression import ImpressionManagement
from .vobj_execution import ExecutionManagement
from .vobj_file import FileManagement

if TYPE_CHECKING:
    from .vobj_file import LsParameters


logger = getLogger("ChernLogger")

class VObject(ArcManagement, FileManagement, AliasManagement,
              ImpressionManagement, ExecutionManagement):
    """ Virtual class of the objects,
    including VData, VAlgorithm and VDirectory
    """

    # Initialization and Representation
    def __init__(self, path: str, project_path: str = "") -> None:
        """ Initialize a instance of the object.
        All the information is directly read from and write to the disk.
        parameter ``path'' is allowed to be a string
        begin with empty characters.
        """
        logger.debug("VObject init: %s", path)
        super().__init__(path)
        logger.debug("VObject init done: %s", path)

    def color_tag(self, status: str) -> str:
        """ Get the color tag according to the status.
        """
        if status in ("built", "done", "finished"):
            color_tag = "success"
        elif status in ("failed", "unfinished"):
            color_tag = "warning"
        elif status == "running":
            color_tag = "running"
        else:
            color_tag = "normal"
        return color_tag

    def cat(self, file_name: str) -> None:
        """ Get the content of a file in the directory
        """
        path = os.path.join(self.path, file_name)
        with open(path, "r", encoding="utf-8") as f:
            print(f.read().strip(""))

    def readme(self) -> str:
        """
        FIXME
        Get the README String.
        I'd like it to support more
        """
        with open(self.path+"/.chern/README.md", "r", encoding="utf-8") as f:
            return f.read().strip("\n")

    def comment(self, line: str) -> None:
        """ Add a comment line to the README.md"""
        with open(self.path+"/.chern/README.md", "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def edit_readme(self) -> None:
        """ Edit the README.md file of the object"""
        yaml_file = metadata.YamlFile(
            join(os.environ["HOME"], ".chern", "config.yaml")
        )
        editor = yaml_file.read_variable("editor", "vi")
        file_name = os.path.join(self.path, ".chern/README.md")
        subprocess.call(f"{editor} {file_name}", shell=True)

    def get_vobject(self, path: str, project_path: str = "") -> 'VObject':
        return VObject(path, project_path)
