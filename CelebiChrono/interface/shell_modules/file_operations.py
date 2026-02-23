"""
File operations functions for shell interface.

Functions for moving, copying, listing, removing files and directories.
"""
import os

from ...utils import csys
from ...utils.message import Message
from ...kernel.vobject import VObject
from ...kernel.vobj_file import LsParameters
from ...interface.ChernManager import create_object_instance
from ._manager import MANAGER

__all__ = [
    '_normalize_paths',
    '_validate_copy_operation',
    '_adjust_destination_path',
    'mv',
    'cp',
    'ls',
    'predecessors',
    'successors',
    'short_ls',
    'rm',
    'rm_file',
    'mv_file',
    'import_file',
    'add_source',
    'send'
]


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


def _validate_copy_operation(source: str, destination: str) -> Message:
    """Validate if copy operation is allowed. Returns Message with errors if invalid."""
    message = Message()
    # Skip if the destination is outside the project
    if os.path.relpath(destination, csys.project_path()).startswith(".."):
        message.add("Destination is outside the project", "error")
        return message

    # Skip the case that the source is the same as the destination
    if source == destination:
        message.add("Source is the same as destination", "error")
        return message

    # Skip the case that the destination is a subdirectory of the source
    if not os.path.relpath(destination, source).startswith(".."):
        message.add("Destination is a subdirectory of source", "error")
        return message

    # Skip the case that the destination already exists and is restricted
    if csys.exists(destination):
        dest_obj = VObject(destination)
        if dest_obj.is_task_or_algorithm():
            message.add("Destination is a task or algorithm", "error")
            return message
        if dest_obj.is_zombie():
            message.add("Illegal to copy", "error")
            return message

    return message


def _adjust_destination_path(source: str, destination: str) -> str:
    """Adjust destination path if it's an existing directory."""
    if csys.exists(destination):
        dest_obj = VObject(destination)
        if dest_obj.object_type() in ("directory", "project"):
            return os.path.join(destination, os.path.basename(source))
    return destination


def mv(source: str, destination: str) -> Message:
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
        Message: Message containing error details for invalid operations,
            or empty message on success.

    Examples:
        mv old_name new_name          # Rename object in current directory
        mv file.txt subdir/           # Move file into subdirectory
        mv @/old_path @/new_path      # Move using project-relative paths

    Note:
        - Preserves link relationships and object metadata
        - Only supports moving single objects (not multiple sources)
        - Validates that both source and destination are within project bounds
        - BE CAREFUL: Moving critical objects may break dependencies
    """
    message = Message()
    source, destination = _normalize_paths(source, destination)
    # Initial validation
    validation = _validate_copy_operation(source, destination)
    if not validation.success:
        return validation

    # Adjust destination if it's an existing directory
    destination = _adjust_destination_path(source, destination)

    # Validate again after path adjustment
    validation = _validate_copy_operation(source, destination)
    if not validation.success:
        return validation

    result = VObject(source).move_to(destination)
    if result.messages:
        message.append(result)
    return message


def cp(source: str, destination: str) -> Message:
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
        Message: Message containing error details for invalid operations,
            or empty message on success.

    Examples:
        cp file.txt file_copy.txt        # Copy file with new name
        cp dir/ newdir/                  # Copy directory
        cp @/source @/dest               # Copy using project-relative paths

    Note:
        - Preserves link relationships and object metadata
        - Within tasks or algorithms, uses object-specific copy logic
        - Validates that both source and destination are within project bounds
    """
    message = Message()
    # Within a task or algorithm, use object-specific copy
    if MANAGER.current_object().object_type() in ("task", "algorithm"):
        MANAGER.current_object().cp(source, destination)
        return message

    # Normalize paths
    source, destination = _normalize_paths(source, destination)

    # Initial validation
    validation = _validate_copy_operation(source, destination)
    if not validation.success:
        return validation

    # Adjust destination if it's an existing directory
    destination = _adjust_destination_path(source, destination)

    # Validate again after path adjustment
    validation = _validate_copy_operation(source, destination)
    if not validation.success:
        return validation

    result = VObject(source).copy_to(destination)
    if result.messages:
        message.append(result)
    return message


def ls(*args) -> Message:  # pylint: disable=too-many-return-statements
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
        Message: Message containing formatted directory listing with object names,
        types, and metadata, colored for display. Returns Message with error if
        the specified path is invalid or outside project bounds.

    Examples:
        ls                    # List current object
        ls /path/to/object    # List specific object within project
        ls @/subdir           # List object using project-relative path

    Note:
        - Only lists objects within the current project boundary
        - Returns Message with error for invalid paths or objects outside project
        - Uses object-specific ls() method for formatted output
    """
    if not args:
        # No path provided, list current object
        return MANAGER.current_object().ls()
    if len(args) == 1:
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
                msg = Message()
                msg.add("[ERROR] Unable to list object outside the current project.", "error")
                return msg
        except Exception as _e:
            msg = Message()
            msg.add(f"[ERROR] Failed to validate path: {_e}", "error")
            return msg

        # Check if object exists
        if not csys.exists(path):
            msg = Message()
            msg.add(f"[ERROR] Object not found: {path}", "error")
            return msg

        # Get the object and list it
        try:
            return create_object_instance(path).ls()
        except Exception as _e:
            msg = Message()
            msg.add(f"Failed to list object: {_e}", "error")
            return msg
    else:
        msg = Message()
        msg.add("ls takes at most one argument (path)", "error")
        return msg


def successors() -> Message:
    """List the successors of the current object.

    Displays objects that depend on or follow from the current object in the
    project workflow. Shows only successor relationships, excluding other
    object details.

    Returns:
        Message: Message containing formatted listing of successor objects with their
        names, paths, and relationship information, colored for display. Returns
        empty message if no successors exist.

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


def predecessors() -> Message:
    """List the predecessors of the current object.

    Displays objects that the current object depends on or follows from in the
    project workflow. Shows only predecessor relationships, excluding other
    object details.

    Returns:
        Message: Message containing formatted listing of predecessor objects with their
        names, paths, and relationship information, colored for display. Returns
        empty message if no predecessors exist.

    Examples:
        predecessors()  # List all predecessors of current object

    Note:
        - Only shows predecessors, not successors or other relationships
        - Returns empty message if no predecessors exist
        - Uses specialized ls parameters to filter for predecessors only
    """
    return MANAGER.current_object().ls(
        LsParameters(
            readme=False,
            successors=False,
            predecessors=True,
            status=False,
            sub_objects=False,
            task_info=False,
        )
    )


def short_ls(_: str) -> Message:
    """Show short listing of the current object.

    Displays a concise summary of the current object's contents, showing only
    essential information without detailed metadata or relationship data.

    Args:
        _ (str): Parameter is ignored (maintains command interface consistency)

    Returns:
        Message: Empty message after executing short listing.

    Examples:
        short_ls("")  # Show short listing of current object (parameter is ignored)

    Note:
        - Shows minimal information compared to full ls() output
        - Ignores the input parameter for interface compatibility
        - Useful for quick overviews in interactive sessions
    """
    message = Message()
    MANAGER.current_object().short_ls()
    return message


def rm(line: str) -> Message:
    """Remove objects (files, directories, tasks, algorithms) from the project.

    Deletes Celebi objects from the current project. The operation is validated
    to ensure project integrity and prevent accidental deletion of critical
    components.

    Args:
        line (str): Path to the object to remove.

    Returns:
        Message: Message containing error details for invalid operations,
            or empty message on success.

    Examples:
        rm file.txt              # Remove file
        rm directory/            # Remove directory
        rm @/path/to/object      # Remove using project-relative path

    Note:
        - Cannot remove the current project root
        - Cannot remove objects outside the project boundary
        - Some objects may be protected from deletion
        - Returns Message with errors instead of raising exceptions
    """
    message = Message()
    line = os.path.abspath(line)
    # Deal with the illegal operation
    if line == csys.project_path():
        message.add("Unable to remove project", "error")
        return message
    if os.path.relpath(line, csys.project_path()).startswith(".."):
        message.add("Unable to remove directory outside the project", "error")
        return message
    if not csys.exists(line):
        message.add("File not exists", "error")
        return message
    result = VObject(line).rm()
    if result.messages:
        message.append(result)
    return message


def rm_file(file_name: str) -> Message:
    """Remove a file from current task or algorithm.

    Deletes files within the context of a task or algorithm object. Supports
    wildcard removal with '*' to delete all non-protected files.

    Args:
        file_name (str): Name of file to remove, or '*' for all files

    Returns:
        Message: Message containing error details for invalid operations,
            or empty message on success.

    Examples:
        rm_file("data.txt")      # Remove specific file
        rm_file("*")             # Remove all non-protected files

    Note:
        - Only works within task or algorithm contexts
        - Protects system files (.celebi, celebi.yaml) from deletion
        - Wildcard '*' removes all files except protected system files
        - Returns Message with errors for failed operations
    """
    message = Message()
    if MANAGER.current_object().object_type() not in ("task", "algorithm"):
        message.add("Unable to call rm_file if you are not in a task or algorithm.", "error")
        return message
    # Deal with * case
    if file_name == "*":
        path = MANAGER.current_object().path
        for current_file in os.listdir(path):
            # protect .celebi and celebi.yaml
            if current_file in (".celebi", "celebi.yaml"):
                continue
            result = MANAGER.current_object().rm_file(current_file)
            if result.messages:
                message.append(result)
        return message
    result = MANAGER.current_object().rm_file(file_name)
    if result.messages:
        message.append(result)
    return message


def mv_file(file_name: str, dest_file: str) -> Message:
    """Move a file within current task or algorithm.

    Relocates or renames files within the context of a task or algorithm object.
    Maintains file relationships and metadata during the move operation.

    Args:
        file_name (str): Name of the file to move
        dest_file (str): Destination file name or path

    Returns:
        Message: Message containing error details for invalid operations,
            or empty message on success.

    Examples:
        mv_file("old.txt", "new.txt")      # Rename file
        mv_file("data.txt", "subdir/data.txt")  # Move to subdirectory

    Note:
        - Only works within task or algorithm contexts
        - Preserves file metadata and relationships
        - Returns Message with errors for failed operations
        - Uses object-specific move_file() method
    """
    message = Message()
    if MANAGER.current_object().object_type() not in ("task", "algorithm"):
        message.add("Unable to call mv_file if you are not in a task or algorithm.", "error")
        return message
    result = MANAGER.current_object().move_file(file_name, dest_file)
    if result.messages:
        message.append(result)
    return message


def import_file(filename: str) -> Message:
    """Import a file into current task or algorithm.

    Copies external files into the current task or algorithm context. Supports
    wildcard imports with '/*' to import all files from a directory.

    Args:
        filename (str): Path to file to import, or directory path ending with '/*'

    Returns:
        Message: Message containing error details for invalid operations,
            or empty message on success.

    Examples:
        import_file("/external/data.txt")      # Import specific file
        import_file("/external/dir/*")         # Import all files from directory

    Note:
        - Only works within task or algorithm contexts
        - Supports directory wildcard imports with '/*' suffix
        - Validates that source paths exist and are accessible
        - Returns Message with errors for failed operations
        - Shows import progress messages for each file
    """
    message = Message()
    if MANAGER.current_object().object_type() not in ("task", "algorithm"):
        message.add("Unable to call importfile if you are not in a task or algorithm.", "error")
        return message

    # Check if the path is a format of /path/to/a/dir/*
    if filename.endswith("/*"):
        filename = filename[:-2]
        if not os.path.isdir(filename):
            message.add("The path is not a directory", "error")
            return message
        for file in os.listdir(filename):
            message.add(f"Importing: from {os.path.join(filename, file)}\n", "info")
            message.add(f"Importing: to {MANAGER.current_object().path}\n", "info")
            result = MANAGER.current_object().import_file(os.path.join(filename, file))
            if result.messages:
                message.append(result)
        return message
    result = MANAGER.current_object().import_file(filename)
    if result.messages:
        message.append(result)
    return message


def add_source(line: str) -> Message:
    """Add a source file or directory to the current object.

    Links external source files or directories to the current Celebi object.
    Sources are tracked for dependency management and can be referenced
    during execution. This is commonly used for adding code libraries,
    configuration files, or data sources to tasks and algorithms.

    Args:
        line (str): Path to the source file or directory to add.

    Returns:
        Message: Empty message after adding source to current object.

    Examples:
        add_source /path/to/library.py      # Add Python library
        add_source ../configs/               # Add configuration directory
        add_source @/data/source.csv         # Add project-relative source

    Note:
        - Source paths must exist and be accessible
        - Sources are tracked for version control and dependency resolution
        - Multiple sources can be added to a single object
        - Sources can be files or directories
    """
    message = Message()
    MANAGER.current_object().add_source(line)
    return message


def send(path: str) -> Message:
    """Send a path to current object.

    Transfers a file or directory path to the current object for processing.
    The object receives the path and may use it for various operations
    depending on the object type and context.

    Args:
        path (str): Filesystem path to send to the current object.

    Examples:
        send data/input.txt
        send results/output.csv

    Returns:
        Message: Empty message after executing path transfer operation.

    Note:
        - Path must be accessible from current working directory
        - Object type determines how path is processed
        - Some objects may have specific path requirements
        - Operation may involve file copying or linking
    """
    message = Message()
    MANAGER.current_object().send(path)
    return message
