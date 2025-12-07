""" The VDirectory class
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    VDirectory:
    #Methods:
        + helpme:
            Print the helpme of this directory
            FIXME: Maybe transfer to return the helpme and putting the
            printing function to interface
        + status:
            Give the status of the object
        + submit:
            Submit the contents of the directory
            (apply submit to the tasks/algorithms/subdirectories)
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
from ..utils import csys
from ..utils import metadata
from ..utils.message import Message
from .vobject import VObject
from .vtask import VTask
from .valgorithm import VAlgorithm
from . import helpme

class VDirectory(VObject):
    """ The VDirectory class
    """
    def helpme(self, command):
        """ Print the helpme of this directory
        """
        message = Message()
        message.add(helpme.directory_helpme.get(command, "No such command, try ``helpme'' alone."))
        return message

    def deposit(self):
        """ Deposit the contents of the directory
            (apply deposit to the tasks/algorithms/subdirectories)
        """
        sub_objects = self.sub_objects()
        for sub_object in sub_objects:
            if sub_object.is_task():
                VTask(sub_object.path).deposit()
            elif sub_object.object_type() == "algorithm":
                VAlgorithm(sub_object.path).deposit()
            else:
                VDirectory(sub_object.path).deposit()

def create_directory(path):
    """ Create a directory
    """
    path = csys.strip_path_string(path)
    parent_path = os.path.abspath(path+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("project", "directory"):
        raise Exception("create directory only under project or directory")
    csys.mkdir(path)
    csys.mkdir(path+"/.chern")
    config_file = metadata.ConfigFile(f"{path}/.chern/config.json")
    config_file.write_variable("object_type", "directory")
    directory = VObject(path)

    with open(path + "/.chern/README.md", "w", encoding="utf-8") as f:
        f.write(
            f"Please write README for the directory "
            f"{directory.invariant_path()}"
        )
