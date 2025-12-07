"""
Shell interface module for Chern project management.

This module provides command-line interface functions for managing
projects, tasks, algorithms, and directories within the Chern system.
"""
import os
import subprocess

from ..utils import csys
from ..utils.message import Message
from ..kernel.vobject import VObject
from ..interface.ChernManager import get_manager
from ..kernel.vtask import create_task
from ..kernel.vtask import create_data
from ..kernel.valgorithm import create_algorithm
from ..kernel.vdirectory import create_directory
from ..utils.pretty import color_print
from ..utils.pretty import colorize
from ..utils import metadata
from ..kernel.chern_communicator import ChernCommunicator

MANAGER = get_manager()


def cd_project(line: str) -> None:
    """Switch to a different project and change directory to its path."""
    MANAGER.switch_project(line)
    os.chdir(MANAGER.current_object().path)


def shell_cd_project(line: str) -> None:
    """Switch to a different project and print the new path."""
    cd_project(line)
    print(MANAGER.current_object().path)


def cd(line: str) -> None:
    """
    Change the directory.
    The standalone Chern.cd command is protected.
    """
    line = line.rstrip("\n")
    if line.isdigit():
        _cd_by_index(int(line))
    else:
        _cd_by_path(line)


def _cd_by_index(index: int) -> None:
    """Change directory by numeric index."""
    sub_objects = MANAGER.current_object().sub_objects()
    successors = MANAGER.current_object().successors()
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
    total = len(successors)
    if index < total:
        cd(MANAGER.current_object().relative_path(successors[index].path))
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
    """
    Move or rename file. Will keep the link relationship.
    mv SOURCE DEST
    or
    mv SOURCE DIRECTORY
    BECAREFULL!!
    mv SOURCE1 SOURCE2 SOURCE3 ... DIRECTORY is not supported
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
    """
    Copy file or directory. Will handle Chern object relationships.
    cp SOURCE DEST
    or
    cp SOURCE DIRECTORY
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


def ls(_: str):
    """List the contents of the current object."""
    return MANAGER.current_object().ls()


def short_ls(_: str) -> None:
    """Show short listing of the current object."""
    MANAGER.current_object().short_ls()


def mkalgorithm(obj: str, use_template: bool = False) -> None:
    """Create a new algorithm."""
    line = csys.refine_path(obj, MANAGER.current_object().path)
    parent_path = os.path.abspath(line+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("directory", "project"):
        print("Not allowed to create algorithm here")
        return
    create_algorithm(line, use_template)


def mktask(line: str) -> None:
    """Create a new task."""
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
    """Create a new directory."""
    line = csys.refine_path(line, MANAGER.current_object().path)
    parent_path = os.path.abspath(line+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("directory", "project"):
        print("Not allowed to create directory here")
        return
    create_directory(line)


def rm(line: str) -> None:
    """Remove a file or directory."""
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
    """Remove a file from current task or algorithm."""
    if MANAGER.current_object().object_type() not in ("task", "algorithm"):
        print("Unable to call rm_file if you are not in a task or algorithm.")
        return
    # Deal with * case
    if file_name == "*":
        path = MANAGER.current_object().path
        for current_file in os.listdir(path):
            # protect .chern and chern.yaml
            if current_file in (".chern", "chern.yaml"):
                continue
            result = MANAGER.current_object().rm_file(current_file)
            if result.messages:  # If there are error messages
                print(result.colored())
        return
    result = MANAGER.current_object().rm_file(file_name)
    if result.messages:  # If there are error messages
        print(result.colored())


def mv_file(file_name: str, dest_file: str) -> None:
    """Move a file within current task or algorithm."""
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
    """Import a file into current task or algorithm."""
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
    """Add an input to current task or algorithm."""
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
        print("Unable to call add_input if you are not in a task.")
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
        print("Unable to call add_input if you are not in a task.")
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

def runners() -> None:
    """Display all available runners."""
    cherncc = ChernCommunicator.instance()
    dite_status = cherncc.dite_status()
    if dite_status == "unconnected":
        print(colorize("DITE unconnected, please connect first", "warning"))
        return
    runner_list = cherncc.runners()
    print(f"Number of runners registered at DITE: {len(runner_list)}")
    if runner_list:
        urls = cherncc.runners_url()
        for runner, url in zip(runner_list, urls):
            print(f"{runner:<20}{url:20}")
            info = cherncc.runner_connection(runner)
            # print(info)
            print(f"{'Status: ':<20}{info['status']:20}")


def register_runner(runner: str, url: str, secret: str) -> None:
    """Register a runner with DITE."""
    cherncc = ChernCommunicator.instance()
    cherncc.register_runner(runner, url, secret)


def remove_runner(runner: str) -> None:
    """Remove a runner from DITE."""
    cherncc = ChernCommunicator.instance()
    cherncc.remove_runner(runner)


def send(path: str) -> None:
    """Send a path to current object."""
    MANAGER.current_object().send(path)


def submit(runner: str = "local") -> None:
    """Submit to the runner."""
    message = MANAGER.current_object().submit(runner)
    print(message.colored())


def view(browser: str = "open") -> None:
    """View impressions for current task."""
    is_task = MANAGER.current_object().is_task()
    if not is_task:
        print("Not able to view")
        return
    url = MANAGER.current_object().impview()
    subprocess.call([browser, url])


def edit_script(obj: str) -> None:
    """Edit a script object using configured editor."""
    path = os.path.join(os.environ["HOME"], ".chern", "config.yaml")
    yaml_file = metadata.YamlFile(path)
    editor = yaml_file.read_variable("editor", "vi")
    subprocess.call([editor, f"{MANAGER.current_object().path}/{obj}"])


def config() -> None:
    """Edit configuration for current task or algorithm."""
    if not MANAGER.current_object().is_task_or_algorithm():
        print("Not able to config")
        return
    path = os.path.join(os.environ["HOME"], ".chern", "config.yaml")
    yaml_file = metadata.YamlFile(path)
    editor = yaml_file.read_variable("editor", "vi")
    # Generate a template file if the config file does not exist
    if not os.path.exists(f"{MANAGER.current_object().path}/chern.yaml"):
        with open(f"{MANAGER.current_object().path}/chern.yaml", "w", encoding="utf-8") as f:
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
    subprocess.call([editor, f"{MANAGER.current_object().path}/chern.yaml"])

def danger_call(cmd: str) -> None:
    """Execute a dangerous command and print the result."""
    message = MANAGER.current_object().danger_call(cmd)
    print(message.colored())


def workaround_preshell() -> tuple[bool, str]:
    """Execute pre-shell workaround for the current task."""
    if not MANAGER.current_object().is_task():
        return (False, "Not able to call workaround if you are not in a task.")
    return MANAGER.current_object().workaround_preshell()


def workaround_postshell() -> None:
    """Execute post-shell workaround for the current task."""
    if not MANAGER.current_object().is_task():
        print("Not able to call workaround if you are not in a task.")
        return
    MANAGER.current_object().workaround_postshell("")


def trace(impression: str) -> None:
    """Trace back to the task or algorithm that generated the impression."""
    MANAGER.current_object().trace(impression)


def history() -> Message:
    """Print the history of a task or algorithm."""
    return MANAGER.current_object().history()

def changes() -> Message:
    """Print the changes of a task or algorithm."""
    return MANAGER.current_object().changes()
