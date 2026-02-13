"""
Shell interface module for Chern project management.

This module provides command-line interface functions for managing
projects, tasks, algorithms, and directories within the Chern system.
"""
import os
import subprocess
from typing import Tuple

from ..utils import csys
from ..utils.message import Message
from ..kernel.vobject import VObject
from ..interface.ChernManager import get_manager, create_object_instance
from ..kernel.vtask import create_task
from ..kernel.vtask import create_data
from ..kernel.valgorithm import create_algorithm
from ..kernel.vdirectory import create_directory
from ..utils.pretty import color_print
from ..utils.pretty import colorize
from ..utils import metadata
from ..kernel.chern_communicator import ChernCommunicator
from ..kernel.vobj_file import LsParameters

MANAGER = get_manager()


def cd_project(line: str) -> None:
    """Switch to a different project and change directory to its path.

    Changes the current working project and navigates to its root directory.
    This function updates both the Celebi project manager and the system
    working directory.

    Args:
        line (str): Name of the project to switch to.

    Examples:
        cd_project my_project      # Switch to project named 'my_project'
        cd_project analysis        # Switch to 'analysis' project

    Note:
        The project must exist in the Celebi project registry.
        Current working directory will change to the project's root path.
    """
    MANAGER.switch_project(line)
    os.chdir(MANAGER.current_object().path)


def shell_cd_project(line: str) -> None:
    """Switch to a different project and print the new path.

    Changes the current working project and prints the absolute path
    to the project's root directory. This is the shell-version that
    outputs the path for shell integration.

    Args:
        line (str): Name of the project to switch to.

    Examples:
        shell_cd_project my_project  # Switch and print path to 'my_project'

    Note:
        Prints the absolute path to stdout for shell capture.
        Uses the same project validation as cd_project.
    """
    cd_project(line)
    print(MANAGER.current_object().path)


def cd(line: str) -> None:
    """Change directory within the current project.

    Changes the current working directory to a specified path or object within
    the current project. Supports both path-based navigation and numeric indices
    for quick access to recently viewed objects.

    Args:
        line (str): Either a path string or numeric index. If a numeric string,
            changes to the object at that index in the current directory listing.
            If a path, changes to the specified object or directory.

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
        _cd_by_index(int(line))
    else:
        _cd_by_path(line)


def _cd_by_index(index: int) -> None:
    """Change directory by numeric index."""
    sub_objects = MANAGER.current_object().sub_objects()
    successors_list = MANAGER.current_object().successors()
    predecessors = MANAGER.current_object().predecessors()
    total = len(sub_objects)

    if index < total:
        sub_objects.sort(key=lambda x: (x.object_type(), x.path))
        cd(MANAGER.current_object().relative_path(sub_objects[index].path))
        return

    index -= total
    total = len(predecessors)
    if index < total:
        cd(MANAGER.current_object().relative_path(predecessors[index].path))
        return

    index -= total
    total = len(successors_list)
    if index < total:
        cd(MANAGER.current_object().relative_path(successors_list[index].path))
        return

    color_print("Out of index", "remind")


def _cd_by_path(line: str) -> None:
    """Change directory by path string."""
    # cd can be used to change directory using absolute path
    line = csys.special_path_string(line)
    if line.startswith("@/") or line == "@":
        line = csys.project_path() + line.strip("@")
    else:
        line = os.path.abspath(line)

    # Check available
    if os.path.relpath(line, csys.project_path()).startswith(".."):
        print("[ERROR] Unable to navigate to a location that is not within the project.")
        return
    if not csys.exists(line):
        print("Directory not exists")
        return
    MANAGER.switch_current_object(line)
    os.chdir(MANAGER.c.path)

def _normalize_paths(source: str, destination: str) -> tuple[str, str]:
    """Normalize source and destination paths."""
    if source.startswith("@/") or source == "@":
        source = os.path.normpath(csys.project_path() + source.strip("@"))
    else:
        source = os.path.abspath(source)

    if destination.startswith("@/") or destination == "@":
        destination = os.path.join(csys.project_path(), destination.strip("@"))
    else:
        destination = os.path.abspath(destination)

    return source, destination

def _validate_copy_operation(source: str, destination: str) -> bool:
    """Validate if copy operation is allowed. Returns True if valid."""
    # Skip if the destination is outside the project
    if os.path.relpath(destination, csys.project_path()).startswith(".."):
        print("Destination is outside the project")
        return False

    # Skip the case that the source is the same as the destination
    if source == destination:
        print("Source is the same as destination")
        return False

    # Skip the case that the destination is a subdirectory of the source
    if not os.path.relpath(destination, source).startswith(".."):
        print("Destination is a subdirectory of source")
        return False

    # Skip the case that the destination already exists and is restricted
    if csys.exists(destination):
        dest_obj = VObject(destination)
        if dest_obj.is_task_or_algorithm():
            print("Destination is a task or algorithm")
            return False
        if dest_obj.is_zombie():
            print("Illegal to copy")
            return False

    return True


def _adjust_destination_path(source: str, destination: str) -> str:
    """Adjust destination path if it's an existing directory."""
    if csys.exists(destination):
        dest_obj = VObject(destination)
        if dest_obj.object_type() in ("directory", "project"):
            return os.path.join(destination, os.path.basename(source))
    return destination


def mv(source: str, destination: str) -> None:
    """Move or rename objects within the current project.

    Moves or renames Celebi objects (files, directories, tasks, algorithms, etc.)
    while preserving their relationships and metadata. Supports moving a single
    object to a new location or renaming it within the same directory.

    Args:
        source (str): Path to the object to move or rename.
        destination (str): New path or destination directory. If destination
            is an existing directory, the source object is moved into it with
            its original name.

    Returns:
        None: Prints error messages to console for invalid operations

    Examples:
        mv old_name new_name          # Rename object in current directory
        mv file.txt subdir/           # Move file into subdirectory
        mv @/old_path @/new_path      # Move using project-relative paths

    Note:
        - Preserves link relationships and object metadata
        - Only supports moving single objects (not multiple sources)
        - Validates that both source and destination are within project bounds
        - BECAREFUL: Moving critical objects may break dependencies
    """
    source, destination = _normalize_paths(source, destination)
    # Initial validation
    if not _validate_copy_operation(source, destination):
        return

    # Adjust destination if it's an existing directory
    destination = _adjust_destination_path(source, destination)

    # Validate again after path adjustment
    if not _validate_copy_operation(source, destination):
        return

    result = VObject(source).move_to(destination)
    if result.messages:  # If there are error messages
        print(result.colored())


def cp(source: str, destination: str) -> None:
    """Copy objects within the current project.

    Copies Celebi objects (files, directories, tasks, algorithms, etc.)
    while preserving their relationships and metadata. Supports copying
    a single object to a new location or into an existing directory.

    Args:
        source (str): Path to the object to copy.
        destination (str): New path or destination directory. If destination
            is an existing directory, the source object is copied into it with
            its original name.

    Returns:
        None: Prints error messages to console for invalid operations

    Examples:
        cp file.txt file_copy.txt        # Copy file with new name
        cp dir/ newdir/                  # Copy directory
        cp @/source @/dest               # Copy using project-relative paths

    Note:
        - Preserves link relationships and object metadata
        - Within tasks or algorithms, uses object-specific copy logic
        - Validates that both source and destination are within project bounds
    """
    # Within a task or algorithm, use object-specific copy
    if MANAGER.current_object().object_type() in ("task", "algorithm"):
        MANAGER.current_object().cp(source, destination)
        return

    # Normalize paths
    source, destination = _normalize_paths(source, destination)

    # Initial validation
    if not _validate_copy_operation(source, destination):
        return

    # Adjust destination if it's an existing directory
    destination = _adjust_destination_path(source, destination)

    # Validate again after path adjustment
    if not _validate_copy_operation(source, destination):
        return

    result = VObject(source).copy_to(destination)
    if result.messages:  # If there are error messages
        print(result.colored())


def ls(*args):
    """List the contents of a Celebi object.

    Displays the object's structure including sub-objects (projects, tasks,
    algorithms, data objects). Shows README, sub-objects, and task information
    by default.

    Args:
        *args: Variable length argument list. Accepts 0 or 1 argument:
            - If no arguments: lists the current object
            - If one argument: treats it as a path to list (must be within
              the current project)

    Returns:
        Message: Formatted listing output or None if path is invalid

    Examples:
        ls                    # List current object
        ls /path/to/object    # List specific object within project
        ls @/subdir           # List object using project-relative path

    Note:
        - Only lists objects within the current project boundary
        - Returns None for invalid paths or objects outside project
        - Uses object-specific ls() method for formatted output
    """
    if len(args) == 0:
        # No path provided, list current object
        return MANAGER.current_object().ls()
    elif len(args) == 1:
        path = args[0]
        # Resolve and validate the path
        path = csys.special_path_string(path)
        if path.startswith("@/") or path == "@":
            path = os.path.normpath(csys.project_path() + path.strip("@"))
        else:
            path = os.path.abspath(path)

        # Check if path is within current project
        try:
            if os.path.relpath(path, csys.project_path()).startswith(".."):
                # print("[ERROR] Unable to list object outside the current project.")
                return None
        except Exception as e:
            # print(f"[ERROR] Failed to validate path: {e}")
            return None

        # Check if object exists
        if not csys.exists(path):
            # print(f"[ERROR] Object not found: {path}")
            return None

        # Get the object and list it
        try:
            return create_object_instance(path).ls()
        except Exception as e:
            # print(f"[ERROR] Failed to list object: {e}")
            msg = Message()
            msg.add(f"Failed to list object: {e}", "error")
            return msg
    else:
        # print("[ERROR] ls takes at most one argument (path)")
        msg = Message()
        msg.add("ls takes at most one argument (path)", "error")
        return msg


def successors() -> Message:
    """List the successors of the current object.

    Displays objects that depend on or follow from the current object in the
    project workflow. Shows only successor relationships, excluding other
    object details.

    Returns:
        Message: Formatted listing of successor objects

    Examples:
        successors()  # List all successors of current object

    Note:
        - Only shows successors, not predecessors or other relationships
        - Returns empty message if no successors exist
        - Uses specialized ls parameters to filter for successors only
    """
    return MANAGER.current_object().ls(
        LsParameters(
            readme=False,
            successors=True,
            predecessors=False,
            status=False,
            sub_objects=False,
            task_info=False,
        )
    )


def short_ls(_: str) -> None:
    """Show short listing of the current object.

    Displays a concise summary of the current object's contents, showing only
    essential information without detailed metadata or relationship data.

    Args:
        _ (str): Unused parameter (maintains command interface consistency)

    Returns:
        None: Output is printed directly to console

    Examples:
        short_ls("")  # Show short listing of current object

    Note:
        - Shows minimal information compared to full ls() output
        - Ignores the input parameter for interface compatibility
        - Useful for quick overviews in interactive sessions
    """
    MANAGER.current_object().short_ls()


def mkalgorithm(obj: str, use_template: bool = False) -> None:
    """Create a new algorithm object.

    Creates a new algorithm within the current project. Algorithms define
    computational procedures that can be executed on tasks. They include
    scripts, configuration, and metadata for reproducible analysis.

    Args:
        obj (str): Path where the algorithm should be created. Must be within
            a valid directory or project location.
        use_template (bool, optional): If True, initializes the algorithm with
            a template structure. Defaults to False.

    Examples:
        create-algorithm my_algo           # Create algorithm at my_algo/
        create-algorithm path/to/algo      # Create at specific path
        create-algorithm @/algorithms/new  # Use project-relative path

    Note:
        Algorithms can only be created within directories or projects,
        not within other object types like tasks or data objects.
    """
    line = csys.refine_path(obj, MANAGER.current_object().path)
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
        create-task my_task           # Create task at my_task/
        create-task path/to/task      # Create at specific path
        create-task @/tasks/new       # Use project-relative path

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
    """Create a new data task."""
    line = csys.refine_path(line, MANAGER.current_object().path)
    parent_path = os.path.abspath(line+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("directory", "project"):
        print("Not allowed to create task here")
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


def rm(line: str) -> None:
    """Remove objects (files, directories, tasks, algorithms) from the project.

    Deletes Celebi objects from the current project. The operation is validated
    to ensure project integrity and prevent accidental deletion of critical
    components.

    Args:
        line (str): Path to the object to remove.

    Returns:
        None: Prints error messages to console for invalid operations

    Examples:
        rm file.txt              # Remove file
        rm directory/            # Remove directory
        rm @/path/to/object      # Remove using project-relative path

    Note:
        - Cannot remove the current project root
        - Cannot remove objects outside the project boundary
        - Some objects may be protected from deletion
        - Prints error messages instead of raising exceptions
    """
    line = os.path.abspath(line)
    # Deal with the illegal operation
    if line == csys.project_path():
        print("Unable to remove project")
        return
    if os.path.relpath(line, csys.project_path()).startswith(".."):
        print("Unable to remove directory outside the project")
        return
    if not csys.exists(line):
        print("File not exists")
        return
    result = VObject(line).rm()
    if result.messages:  # If there are error messages
        print(result.colored())


def rm_file(file_name: str) -> None:
    """Remove a file from current task or algorithm.

    Deletes files within the context of a task or algorithm object. Supports
    wildcard removal with '*' to delete all non-protected files.

    Args:
        file_name (str): Name of file to remove, or '*' for all files

    Returns:
        None: Prints error messages to console for invalid operations

    Examples:
        rm_file("data.txt")      # Remove specific file
        rm_file("*")             # Remove all non-protected files

    Note:
        - Only works within task or algorithm contexts
        - Protects system files (.celebi, celebi.yaml) from deletion
        - Wildcard '*' removes all files except protected system files
        - Prints colored error messages for failed operations
    """
    if MANAGER.current_object().object_type() not in ("task", "algorithm"):
        print("Unable to call rm_file if you are not in a task or algorithm.")
        return
    # Deal with * case
    if file_name == "*":
        path = MANAGER.current_object().path
        for current_file in os.listdir(path):
            # protect .chern and celebi.yaml
            if current_file in (".celebi", "celebi.yaml"):
                continue
            result = MANAGER.current_object().rm_file(current_file)
            if result.messages:  # If there are error messages
                print(result.colored())
        return
    result = MANAGER.current_object().rm_file(file_name)
    if result.messages:  # If there are error messages
        print(result.colored())


def mv_file(file_name: str, dest_file: str) -> None:
    """Move a file within current task or algorithm.

    Relocates or renames files within the context of a task or algorithm object.
    Maintains file relationships and metadata during the move operation.

    Args:
        file_name (str): Name of the file to move
        dest_file (str): Destination file name or path

    Returns:
        None: Prints error messages to console for invalid operations

    Examples:
        mv_file("old.txt", "new.txt")      # Rename file
        mv_file("data.txt", "subdir/data.txt")  # Move to subdirectory

    Note:
        - Only works within task or algorithm contexts
        - Preserves file metadata and relationships
        - Prints colored error messages for failed operations
        - Uses object-specific move_file() method
    """
    if MANAGER.current_object().object_type() not in ("task", "algorithm"):
        print("Unable to call mv_file if you are not in a task or algorithm.")
        return
    result = MANAGER.current_object().move_file(file_name, dest_file)
    if result.messages:  # If there are error messages
        print(result.colored())


def add_source(line: str) -> None:
    """Add a source to the current object."""
    MANAGER.current_object().add_source(line)


def jobs(_: str) -> None:
    """Show jobs for current algorithm or task."""
    object_type = MANAGER.current_object().object_type()
    if object_type not in ("algorithm", "task"):
        print("Not able to found job")
        return
    MANAGER.current_object().jobs()


def status():
    """Show status of current object."""
    return MANAGER.current_object().printed_status()

def import_file(filename: str) -> None:
    """Import a file into current task or algorithm.

    Copies external files into the current task or algorithm context. Supports
    wildcard imports with '/*' to import all files from a directory.

    Args:
        filename (str): Path to file to import, or directory path ending with '/*'

    Returns:
        None: Prints error messages to console for invalid operations

    Examples:
        import_file("/external/data.txt")      # Import specific file
        import_file("/external/dir/*")         # Import all files from directory

    Note:
        - Only works within task or algorithm contexts
        - Supports directory wildcard imports with '/*' suffix
        - Validates that source paths exist and are accessible
        - Prints colored error messages for failed operations
        - Shows import progress messages for each file
    """
    if MANAGER.current_object().object_type() not in ("task", "algorithm"):
        print("Unable to call importfile if you are not in a task or algorithm.")
        return

    # Check if the path is a format of /path/to/a/dir/*
    if filename.endswith("/*"):
        filename = filename[:-2]
        if not os.path.isdir(filename):
            print("The path is not a directory")
            return
        for file in os.listdir(filename):
            print(f"Importing: from {os.path.join(filename, file)}")
            print(f"Importing: to {MANAGER.current_object().path}")
            result = MANAGER.current_object().import_file(os.path.join(filename, file))
            if result.messages:  # If there are error messages
                print(result.colored())
        return
    result = MANAGER.current_object().import_file(filename)
    if result.messages:  # If there are error messages
        print(result.colored())


# pylint: disable=too-many-branches
def add_input(path: str, alias: str) -> None:
    """Add an input to the current task or algorithm.

    Links an existing object (data, task output, or algorithm) as an input
    to the current task or algorithm. Inputs are referenced by alias within
    the execution context.

    Args:
        path (str): Path to the object to add as input.
        alias (str): Name to reference this input within the task/algorithm.

    Examples:
        add-input data/file.txt input_data  # Add file as input with alias
        add-input @/tasks/prev/output result  # Add task output as input

    Note:
        - The current object must be a task or algorithm
        - Input objects must exist within the project
        - Aliases must be unique within the task/algorithm
    """
    if MANAGER.current_object().object_type() == "directory":
        destination_path = MANAGER.current_object().relative_path(path)
        dest_obj = VObject(os.path.join(MANAGER.current_object().path, destination_path))
        if dest_obj.object_type() == "task":
            sub_objects = MANAGER.current_object().sub_objects()
            for obj in sub_objects:
                if obj.object_type() != "task":
                    continue
                obj_path = MANAGER.current_object().relative_path(obj.path)
                task = MANAGER.sub_object(obj_path)
                task.add_input(path, alias)
        elif dest_obj.object_type() == "directory":
            dest_sub_objects = dest_obj.sub_objects()
            sub_objects = MANAGER.current_object().sub_objects()
            if len(dest_sub_objects) != len(sub_objects):
                print("The number of sub-objects does not match.")
                return
            # Check whether the sub-objects name ends with _<index>
            # By getting the _<index> and check whether <index> is a digit
            for obj in sub_objects:
                ending = obj.path.split("_")[-1]
                if not ending.isdigit():
                    print("The sub-objects are not in indexed format.")
                    return
            for dest_obj in sub_objects:
                ending = dest_obj.path.split("_")[-1]
                if not ending.isdigit():
                    print("The dest-sub-objects are not in indexed format.")
                    return
            # Sort both lists by the index
            sub_objects.sort(key=lambda x: int(x.path.split("_")[-1]))
            dest_sub_objects.sort(key=lambda x: int(x.path.split("_")[-1]))
            length = len(sub_objects)
            for obj, dest_obj in zip(sub_objects, dest_sub_objects):
                if obj.path.split("_")[-1] != dest_obj.path.split("_")[-1]:
                    print("The sub-objects are not aligned.")
                    return
                obj_path = MANAGER.current_object().relative_path(obj.path)
                task = MANAGER.sub_object(obj_path)
                task.add_input(dest_obj.path, alias)
                if length > 100 and int(dest_obj.path.split("_")[-1]) % (length // 10) == 0:
                    print(f"Progress: {int(dest_obj.path.split('_')[-1])}/{length}")
        return
    if MANAGER.current_object().object_type() not in ("task", "algorithm"):
        print("Unable to call add_input if you are not in a task or algorithm.")
        return
    MANAGER.current_object().add_input(path, alias)


def add_algorithm(path: str) -> None:
    """Add an algorithm to current task."""
    if MANAGER.current_object().object_type() == "directory":
        sub_objects = MANAGER.current_object().sub_objects()
        for obj in sub_objects:
            if obj.object_type() != "task":
                continue
            obj_path = MANAGER.current_object().relative_path(obj.path)
            task = MANAGER.sub_object(obj_path)
            task.add_algorithm(path)
        return
    if MANAGER.current_object().object_type() != "task":
        print("Unable to call add_algorithm if you are not in a task.")
        return
    MANAGER.current_object().add_algorithm(path)


def add_parameter(par: str, value: str) -> None:
    """Add a parameter to current task."""
    if MANAGER.current_object().object_type() == "directory":
        sub_objects = MANAGER.current_object().sub_objects()
        for obj in sub_objects:
            if obj.object_type() != "task":
                continue
            obj_path = MANAGER.current_object().relative_path(obj.path)
            task = MANAGER.sub_object(obj_path)
            task.add_parameter(par, value)
        return
    if MANAGER.current_object().object_type() != "task":
        print("Unable to call add_input if you are not in a task.")
        return
    MANAGER.current_object().add_parameter(par, value)

def add_parameter_subtask(dirname: str, par: str, value: str) -> None:
    """Add a parameter to current task."""
    if MANAGER.current_object().object_type() not in ("directory", "project"):
        print("Unable to call add_parameter_subtask if you are not in a dir")
        return
    obj = MANAGER.sub_object(dirname)
    if not obj.is_task():
        print("Unable to call add_parameter if you are not in a task.")
        return
    obj.add_parameter(par, value)

def set_environment(env: str) -> None:
    """Set environment for current task."""
    if MANAGER.current_object().object_type() == "directory":
        sub_objects = MANAGER.current_object().sub_objects()
        for obj in sub_objects:
            if obj.object_type() != "task":
                continue
            obj_path = MANAGER.current_object().relative_path(obj.path)
            task = MANAGER.sub_object(obj_path)
            task.set_environment(env)
        return
    if MANAGER.current_object().object_type() != "task":
        print("Unable to call set_environment if you are not in a task.")
        return
    MANAGER.current_object().set_environment(env)


def set_memory_limit(limit: str) -> None:
    """Set memory limit for current task."""
    if MANAGER.current_object().object_type() == "directory":
        sub_objects = MANAGER.current_object().sub_objects()
        for obj in sub_objects:
            if obj.object_type() != "task":
                continue
            obj_path = MANAGER.current_object().relative_path(obj.path)
            task = MANAGER.sub_object(obj_path)
            task.set_memory_limit(limit)
        return
    if MANAGER.current_object().object_type() != "task":
        print("Unable to call set_memory_limit if you are not in a task.")
        return
    MANAGER.current_object().set_memory_limit(limit)


def rm_parameter(par: str) -> None:
    """Remove a parameter from current task."""
    if MANAGER.current_object().object_type() != "task":
        print("Unable to call remove_parameter if you are not in a task.")
        return
    MANAGER.current_object().remove_parameter(par)


def remove_input(alias: str) -> None:
    """Remove an input from current task or algorithm."""
    if MANAGER.current_object().object_type() == "directory":
        sub_objects = MANAGER.current_object().sub_objects()
        for obj in sub_objects:
            if obj.object_type() != "task":
                continue
            obj_path = MANAGER.current_object().relative_path(obj.path)
            task = MANAGER.sub_object(obj_path)
            task.remove_input(alias)
        return
    if not MANAGER.current_object().is_task_or_algorithm():
        print("Unable to call remove_input if you are not in a task.")
        return
    MANAGER.current_object().remove_input(alias)


def add_host(host: str, url: str) -> None:
    """Add a host to the communicator."""
    cherncc = ChernCommunicator.instance()
    cherncc.add_host(host, url)


def hosts() -> None:
    """Show all hosts and their status."""
    cherncc = ChernCommunicator.instance()
    host_list = cherncc.hosts()
    print(f"{'HOSTS':<20}{'STATUS':20}")
    for host in host_list:
        host_status = cherncc.host_status(host)
        color_tag = {"ok": "ok", "unconnected": "warning"}[host_status]
        print(f"{host:<20}{colorize(host_status, color_tag):20}")


def dite() -> None:
    """Show DITE information."""
    cherncc = ChernCommunicator.instance()
    dite_info = cherncc.dite_info()
    print(dite_info)

def set_dite(url: str = "") -> None:
    """Set DITE connection."""
    project_path = csys.project_path()
    config_path = os.path.join(project_path, ".celebi", "hosts.json")
    config_file = metadata.ConfigFile(config_path)
    if url:
        config_file.write_variable("serverurl", url)
        print(f"DITE URL set to: {url}")


def runners() -> Message:
    """Display all available runners."""
    message = Message()
    cherncc = ChernCommunicator.instance()
    dite_status = cherncc.dite_status()
    if dite_status == "unconnected":
        message.add("DITE unconnected, please connect first", "warning")
        return message
    runner_list = cherncc.runners()
    message.add(f"Number of runners: {len(runner_list)}\n", "title0")
    if runner_list:
        urls = cherncc.runners_url()
        for runner, url in zip(runner_list, urls):
            message.add(f"{runner:<20}{url:20}", "normal")
            message.add("\n")
            info = cherncc.runner_connection(runner)
            message.add(f"{'Status: ':<20}", "info")
            if info['status'] == "Connected":
                message.add(f"{info['status']:20}\n", "success" )
            else:
                message.add(f"{info['status']:20}\n", "warning" )
            message.add("------------\n")
    return message


def register_runner(runner: str, url: str, secret: str, backend_type: str) -> None:
    """Register a runner with DITE."""
    cherncc = ChernCommunicator.instance()
    cherncc.register_runner(runner, url, secret, backend_type)

def remove_runner(runner: str) -> None:
    """Remove a runner from DITE."""
    cherncc = ChernCommunicator.instance()
    cherncc.remove_runner(runner)

def request_runner(runner: str) -> None:
    """Set the requested runner"""
    MANAGER.current_object().set_default_runner(runner)

def search_impression(partial_uuid: str) -> Message:
    """Search impressions by partial UUID."""
    print("Search partial uuid", partial_uuid)
    message = MANAGER.current_object().search_impression(partial_uuid)
    return message

def send(path: str) -> None:
    """Send a path to current object."""
    MANAGER.current_object().send(path)


def submit(runner: str = "local") -> None:
    """Submit current task for execution.

    Sends the current task to a runner for processing. The runner executes
    the task's algorithm with the specified inputs and parameters, producing
    outputs and logs.

    Args:
        runner (str, optional): Name of the runner to use for execution.
            Defaults to "local" for local execution.

    Examples:
        submit              # Submit to local runner
        submit my_runner    # Submit to specific runner
        submit cluster-01   # Submit to cluster runner

    Returns:
        Message object with submission status and details.

    Note:
        - The current object must be a task
        - The task must have a valid algorithm and inputs configured
        - Runner must be available and configured
    """
    print(MANAGER.current_object())
    print(runner)
    message = MANAGER.current_object().submit(runner)
    return message

def purge():
    """Purge temporary files and cleanup current object.

    Removes temporary files, cache data, and other non-essential artifacts
    associated with the current object. This helps free up disk space and
    resolve potential consistency issues.

    Note:
        The exact behavior depends on the object type. Some objects may
        have protected data that cannot be purged.
    """
    message = MANAGER.current_object().purge()
    print(message.colored())

def purge_old_impressions():
    """Purge old impression data from current object.

    Removes historical impression data that is no longer needed, preserving
    only recent or essential impressions. Impressions are visualization
    or snapshot data generated during task execution.

    Note:
        The age threshold for 'old' impressions is configurable.
        Some impression data may be protected from deletion.
    """
    message = MANAGER.current_object().purge_old_impressions()
    print(message.colored())


def view(browser: str = "open") -> None:
    """View impressions for current task."""
    is_task = MANAGER.current_object().is_task()
    if not is_task:
        print("Not able to view")
        return
    url = MANAGER.current_object().impview()
    subprocess.call([browser, url])

def viewurl() -> str:
    """Get the impression path for view"""
    is_task = MANAGER.current_object().is_task()
    if not is_task:
        print("Not able to get view url")
        return ""
    url = MANAGER.current_object().impview()
    return url

def impress() -> Message:
    """Create impression for current task or algorithm."""
    message = MANAGER.current_object().impress()
    return message

def get_script_path(filename: str) -> Tuple[bool, str]:
    """Get the script path for a algorithm or a task object."""
    if not MANAGER.current_object().is_task_or_algorithm():
        return False, "Not able to get script path if you are not in a task or algorithm."
    if MANAGER.current_object().object_type() == "task":
        if filename.startswith("code/"):
            algorithm = MANAGER.current_object().algorithm()
            return True, f"{algorithm.path}/{filename[5:]}"
        if filename.startswith("code:"):
            algorithm = MANAGER.current_object().algorithm()
            return True, f"{algorithm.path}/{filename[5:]}"
        return True, f"{MANAGER.current_object().path}/{filename}"
    return True, f"{MANAGER.current_object().path}/{filename}"


def config() -> None:
    """Edit configuration for current task or algorithm."""
    if not MANAGER.current_object().is_task_or_algorithm():
        print("Not able to config")
        return
    path = os.path.join(os.environ["HOME"], ".celebi", "config.yaml")
    yaml_file = metadata.YamlFile(path)
    editor = yaml_file.read_variable("editor", "vi")
    # Generate a template file if the config file does not exist
    if not os.path.exists(f"{MANAGER.current_object().path}/celebi.yaml"):
        with open(f"{MANAGER.current_object().path}/celebi.yaml", "w", encoding="utf-8") as f:
            if MANAGER.current_object().object_type() == "task":
                f.write("""environment: chern
memory_limit: 256Mi
alias:
  - void
parameters: {{}}""")
            else:
                f.write("""environment: script
commands:
  - echo 'Hello, world!'""")
    subprocess.call([editor, f"{MANAGER.current_object().path}/celebi.yaml"])

def danger_call(cmd: str) -> None:
    """Execute a dangerous command and print the result."""
    message = MANAGER.current_object().danger_call(cmd)
    print(message.colored())


def workaround_preshell() -> tuple[bool, str]:
    """Execute pre-shell workaround for the current task."""
    if not MANAGER.current_object().is_task():
        return (False, "Not able to call workaround if you are not in a task.")
    return MANAGER.current_object().workaround_preshell()


def workaround_postshell(path: str) -> None:
    """Execute post-shell workaround for the current task."""
    print("Working on postshell")
    if not MANAGER.current_object().is_task():
        print("Not able to call workaround if you are not in a task.")
        return
    print(MANAGER.current_object())
    MANAGER.current_object().workaround_postshell(path)


def trace(impression: str) -> None:
    """Trace back to the task or algorithm that generated the impression."""
    MANAGER.current_object().trace(impression)


def history() -> Message:
    """Print the history of a task or algorithm."""
    return MANAGER.current_object().history()

def watermark() -> Message:
    """Print the watermark of a task or algorithm."""
    return MANAGER.current_object().watermark()

def changes() -> Message:
    """Print the changes of a task or algorithm."""
    return MANAGER.current_object().changes()

def doctor() -> Message:
    """Doctor the impression"""
    return MANAGER.current_object().doctor()

def collect(contents: str = "all") -> Message:
    """Collect task execution results.

    Retrieves outputs, logs, or both from a completed task execution.
    Results are gathered from the runner and made available locally.

    Args:
        contents (str, optional): What to collect: "all", "outputs", or "logs".
            Defaults to "all".

    Examples:
        collect              # Collect both outputs and logs
        collect outputs      # Collect only outputs
        collect logs         # Collect only logs

    Returns:
        Message object with collection status and results.

    Note:
        - The current object must be a task
        - Task must have been submitted and completed
        - Collection may download files from remote runners
    """
    return MANAGER.current_object().collect(contents)

def collect_outputs() -> Message:
    """Collect only task outputs.

    Retrieves output files and data from a completed task execution,
    excluding logs.

    Returns:
        Message object with outputs collection status.

    See Also:
        collect: Collect both outputs and logs
        collect_logs: Collect only logs
    """
    return MANAGER.current_object().collect("outputs")

def collect_logs() -> Message:
    """Collect only task logs.

    Retrieves log files from a completed task execution,
    excluding output data.

    Returns:
        Message object with logs collection status.

    See Also:
        collect: Collect both outputs and logs
        collect_outputs: Collect only outputs
    """
    return MANAGER.current_object().collect("logs")

def bookkeep() -> Message:
    """Bookkeep the impression"""
    return MANAGER.root_object().bookkeep()

def bookkeep_url() -> str:
    """Get the bookkeep URL"""
    return MANAGER.root_object().bookkeep_url()

def tree(depth = -1) -> Message:
    """ Get the directory tree
    """
    return MANAGER.current_object().tree()

def error_log(index) -> Message:
    """ Get the error log
    """
    return MANAGER.current_object().error_log(index)


def navigate() -> str:
    """Return the path of the current project.

    Retrieves the absolute filesystem path of the currently active
    Celebi project. This is useful for shell scripts and external
    tools that need to know the project location.

    Returns:
        Absolute path to the current project's root directory.

    Examples:
        project_path = navigate()  # Get current project path
        cd $(navigate)/subdir     # Use in shell command

    Note:
        Returns empty string if no project is currently active.
        Requires the ChernProjectManager to be initialized.
    """
    from ..interface.ChernManager import ChernProjectManager
    manager = ChernProjectManager().get_manager()
    project_name = manager.get_current_project()
    return manager.get_project_path(project_name)
