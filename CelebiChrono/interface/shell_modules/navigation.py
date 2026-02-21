"""
Navigation functions for shell interface.

Functions for changing directories, navigating projects, and path operations.
"""
import os

from ...utils import csys
from ...utils.message import Message
from ._manager import MANAGER

__all__ = [
    'cd_project',
    'shell_cd_project',
    'cd',
    '_cd_by_index',
    '_cd_by_path',
    'navigate'
]


def cd_project(line: str) -> Message:
    """Switch to a different project and change directory to its path.

    Changes the current working project and navigates to its root directory.
    This function updates both the Celebi project manager and the system
    working directory.

    Args:
        line (str): Name of the project to switch to.

    Returns:
        Message with success info about the project switch.

    Examples:
        cd_project my_project      # Switch to project named 'my_project'
        cd_project analysis        # Switch to 'analysis' project

    Note:
        The project must exist in the Celebi project registry.
        Current working directory will change to the project's root path.
    """
    message = Message()
    MANAGER.switch_project(line)
    os.chdir(MANAGER.current_object().path)
    message.add(f"Switched to project: {line}", "success")
    return message


def shell_cd_project(line: str) -> Message:
    """Switch to a different project and print the new path.

    Changes the current working project and prints the absolute path
    to the project's root directory. This is the shell-version that
    outputs the path for shell integration.

    Args:
        line (str): Name of the project to switch to.

    Returns:
        Message with project switch info and the new path.

    Examples:
        shell_cd_project my_project  # Switch and print path to 'my_project'

    Note:
        Prints the absolute path to stdout for shell capture.
        Uses the same project validation as cd_project.
    """
    message = cd_project(line)
    message.add(MANAGER.current_object().path, "normal")
    return message


def cd(line: str) -> Message:
    """Change directory within the current project.

    Changes the current working directory to a specified path or object within
    the current project. Supports both path-based navigation and numeric indices
    for quick access to recently viewed objects.

    Args:
        line (str): Either a path string or numeric index. If a numeric string,
            changes to the object at that index in the current directory listing.
            If a path, changes to the specified object or directory.

    Returns:
        Message with navigation result or error info.

    Examples:
        cd subdirectory       # Change to subdirectory
        cd ../parent          # Change to parent directory
        cd 2                  # Change to object at index 2 in ls output
        cd @/project/path     # Change using project-relative path

    Note:
        The standalone Chern.cd command is protected and maintains project
        boundary safety.
    """
    line = line.rstrip("\n")
    if line.isdigit():
        return _cd_by_index(int(line))
    return _cd_by_path(line)


def _cd_by_index(index: int) -> Message:
    """Change directory by numeric index."""
    message = Message()
    sub_objects = MANAGER.current_object().sub_objects()
    successors_list = MANAGER.current_object().successors()
    predecessors = MANAGER.current_object().predecessors()
    total = len(sub_objects)

    if index < total:
        sub_objects.sort(key=lambda x: (x.object_type(), x.path))
        return cd(MANAGER.current_object().relative_path(sub_objects[index].path))

    index -= total
    total = len(predecessors)
    if index < total:
        return cd(MANAGER.current_object().relative_path(predecessors[index].path))

    index -= total
    total = len(successors_list)
    if index < total:
        return cd(MANAGER.current_object().relative_path(successors_list[index].path))

    message.add("Out of index", "warning")
    return message


def _cd_by_path(line: str) -> Message:
    """Change directory by path string."""
    message = Message()
    # cd can be used to change directory using absolute path
    line = csys.special_path_string(line)
    if line.startswith("@/") or line == "@":
        line = csys.project_path() + line.strip("@")
    else:
        line = os.path.abspath(line)

    # Check available
    if os.path.relpath(line, csys.project_path()).startswith(".."):
        message.add("[ERROR] Unable to navigate to a location "
                    "that is not within the project.", "error")
        return message
    if not csys.exists(line):
        message.add("Directory not exists", "error")
        return message
    MANAGER.switch_current_object(line)
    os.chdir(MANAGER.c.path)
    return message


def navigate() -> Message:
    """Return the path of the current project.

    Retrieves the absolute filesystem path of the currently active
    Celebi project. This is useful for shell scripts and external
    tools that need to know the project location.

    Returns:
        Message containing the absolute path to the current project's root directory.

    Examples:
        project_path = navigate()  # Get current project path
        cd $(navigate)/subdir     # Use in shell command

    Note:
        Returns empty string if no project is currently active.
        Requires the ChernProjectManager to be initialized.
    """
    from ...interface.ChernManager import ChernProjectManager
    message = Message()
    manager = ChernProjectManager().get_manager()
    project_name = manager.get_current_project()
    path = manager.get_project_path(project_name)
    message.add(path, "normal")
    message.data["path"] = path
    return message
