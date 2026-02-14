"""
Object creation functions for shell interface.

Functions for creating new algorithms, tasks, data objects, and directories.
"""
import os

from ...utils import csys
from ...kernel.vobject import VObject
from ...kernel.vtask import create_task
from ...kernel.vtask import create_data
from ...kernel.valgorithm import create_algorithm
from ...kernel.vdirectory import create_directory
from ._manager import MANAGER


def mkalgorithm(line: str, use_template: bool = False) -> None:
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
        None: Algorithm is created at specified path, or error message printed to console

    Note:
        Algorithms can only be created within directories or projects,
        not within other object types like tasks or data objects.
    """
    line = csys.refine_path(line, MANAGER.current_object().path)
    parent_path = os.path.abspath(line+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("directory", "project"):
        print("Not allowed to create algorithm here")
        return
    create_algorithm(line, use_template)


def mktask(line: str) -> None:
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
        None: Task is created at specified path, or error message printed to console

    Note:
        Tasks can only be created within directories or projects,
        not within other object types like algorithms or data objects.
    """
    line = csys.refine_path(line, MANAGER.current_object().path)
    parent_path = os.path.abspath(line+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("directory", "project"):
        print("Not allowed to create task here")
        return
    create_task(line)


def mkdata(line: str) -> None:
    """Create a new data object.

    Creates a new data object within the current project. Data objects store
    input files, output results, or intermediate data used by tasks and
    algorithms. They provide structured storage for project data with metadata
    tracking.

    Args:
        line (str): Path where the data object should be created. Must be within
            a valid directory or project location.

    Returns:
        None: Data object is created at specified path, or error message printed to console

    Examples:
        mkdata my_data           # Create data object at my_data/
        mkdata path/to/data      # Create at specific path
        mkdata @/data/new        # Use project-relative path

    Note:
        Data objects can only be created within directories or projects,
        not within other object types like tasks or algorithms.
    """
    line = csys.refine_path(line, MANAGER.current_object().path)
    parent_path = os.path.abspath(line+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("directory", "project"):
        print("Not allowed to create data here")
        return
    create_data(line)


def mkdir(line: str) -> None:
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
        None: Directory is created at specified path, or error message printed to console

    Note:
        Directories can only be created within existing directories or
        projects, not within other object types like tasks or algorithms.
    """
    line = csys.refine_path(line, MANAGER.current_object().path)
    parent_path = os.path.abspath(line+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("directory", "project"):
        print("Not allowed to create directory here")
        return
    create_directory(line)