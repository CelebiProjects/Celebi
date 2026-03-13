"""
Object creation functions for shell interface.

Functions for creating new algorithms, tasks, data objects, and directories.
"""
import os

from ...utils import csys
from ...utils.message import Message
from ...kernel.vobject import VObject
from ...kernel.vtask import create_task
from ...kernel.vtask import create_data
from ...kernel.vtask import create_data_list
from ...kernel.valgorithm import create_algorithm
from ...kernel.vdirectory import create_directory
from ._manager import MANAGER


def mkalgorithm(line: str, use_template: bool = False) -> Message:
    """Create a new algorithm object.

    Creates a new algorithm within the current project. Algorithms define
    computational procedures that can be executed on tasks. They include
    scripts, configuration, and metadata for reproducible analysis.

    Args:
        line (str): Path where the algorithm should be created. Must be within
            a valid directory or project location.
        use_template (bool, optional): If True, initializes the algorithm with
            a template structure. Defaults to False.

    Examples:
        mkalgorithm my_algo           # Create algorithm at my_algo/
        mkalgorithm path/to/algo      # Create at specific path
        mkalgorithm @/algorithms/new  # Use project-relative path

    Returns:
        Message: A Message object containing success or warning information

    Note:
        Algorithms can only be created within directories or projects,
        not within other object types like tasks or data objects.
    """
    line = csys.refine_path(line, MANAGER.current_object().path)
    message = Message()
    parent_path = os.path.abspath(line+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("directory", "project"):
        message.add("Not allowed to create algorithm here", "warning")
        return message
    create_algorithm(line, use_template)
    message.add("Created successfully", "success")
    return message


def mktask(line: str) -> Message:
    """Create a new task object.

    Creates a new task within the current project. Tasks are executable units
    that combine inputs, algorithms, and parameters to produce outputs.
    Tasks can be submitted for execution and tracked through their lifecycle.

    Args:
        line (str): Path where the task should be created. Must be within
            a valid directory or project location.

    Examples:
        mktask my_task           # Create task at my_task/
        mktask path/to/task      # Create at specific path
        mktask @/tasks/new       # Use project-relative path

    Returns:
        Message: A Message object containing success or warning information

    Note:
        Tasks can only be created within directories or projects,
        not within other object types like algorithms or data objects.
    """
    line = csys.refine_path(line, MANAGER.current_object().path)
    message = Message()
    parent_path = os.path.abspath(line+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("directory", "project"):
        message.add("Not allowed to create task here", "warning")
        return message
    create_task(line)
    message.add("Created successfully", "success")
    return message


def mkdata(line: str) -> Message:
    """Create a new data object.

    Creates a new data object within the current project. Data objects store
    input files, output results, or intermediate data used by tasks and
    algorithms. They provide structured storage for project data with metadata
    tracking.

    Args:
        line (str): Path where the data object should be created. Must be within
            a valid directory or project location.

    Returns:
        Message: A Message object containing success or warning information

    Examples:
        mkdata my_data           # Create data object at my_data/
        mkdata path/to/data      # Create at specific path
        mkdata @/data/new        # Use project-relative path

    Note:
        Data objects can only be created within directories or projects,
        not within other object types like tasks or algorithms.
    """
    line = csys.refine_path(line, MANAGER.current_object().path)
    message = Message()
    parent_path = os.path.abspath(line+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("directory", "project"):
        message.add("Not allowed to create data here", "warning")
        return message
    create_data(line)
    message.add("Created successfully", "success")
    return message


def mkdatalist(line: str) -> Message:
    """Create a new data list object.

    Creates a new data list object within the current project. Data list objects
    store a list of file paths that can be used as input for batch processing.
    They use the 'datalist' environment and generate a dataList.txt file in stageout.

    Args:
        line (str): Path where the data list object should be created. Must be within
            a valid directory or project location.

    Returns:
        Message: A Message object containing success or warning information

    Examples:
        mkdatalist my_datalist       # Create data list at my_datalist/
        mkdatalist path/to/datalist  # Create at specific path
        mkdatalist @/data/lists      # Use project-relative path

    Note:
        Data list objects can only be created within directories or projects,
        not within other object types like tasks or algorithms.
        The datalist field in celebi.yaml stores the list of file paths.
    """
    line = csys.refine_path(line, MANAGER.current_object().path)
    message = Message()
    parent_path = os.path.abspath(line+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("directory", "project"):
        message.add("Not allowed to create data list here", "warning")
        return message
    create_data_list(line)
    message.add("Created successfully", "success")
    return message


def mkdir(line: str) -> Message:
    """Create a new directory within the current project.

    Creates an empty directory for organizing projects, tasks, algorithms,
    and data objects. Directories provide hierarchical organization within
    the Celebi project structure.

    Args:
        line (str): Path where the directory should be created.

    Examples:
        mkdir new_folder          # Create directory in current location
        mkdir path/to/newdir      # Create with full path
        mkdir @/subdirs/new       # Use project-relative path

    Returns:
        Message: A Message object containing success or warning information

    Note:
        Directories can only be created within existing directories or
        projects, not within other object types like tasks or algorithms.
    """
    line = csys.refine_path(line, MANAGER.current_object().path)
    message = Message()
    parent_path = os.path.abspath(line+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("directory", "project"):
        message.add("Not allowed to create directory here", "warning")
        return message
    create_directory(line)
    message.add("Created successfully", "success")
    return message
