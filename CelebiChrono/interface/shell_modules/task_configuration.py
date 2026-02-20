"""
Task configuration functions for shell interface.

Functions for configuring tasks and algorithms: inputs, parameters, environment, etc.
"""
import os
import subprocess

from ...kernel.vobject import VObject
from ...utils import metadata
from ...utils.message import Message
from ._manager import MANAGER


def jobs(_: str) -> Message:
    """Display job information for current algorithm or task.

    Shows execution jobs associated with the current algorithm or task object.
    Jobs represent individual executions with their status, parameters, and
    results. This command provides visibility into the execution history
    and current state of computational workflows.

    Args:
        _ (str): Unused parameter (maintained for interface consistency).

    Returns:
        Message: Message with job information or error message.

    Examples:
        jobs          # Show jobs for current algorithm/task
        jobs          # No arguments needed, parameter is unused

    Note:
        - Only works within algorithm or task contexts
        - Shows job ID, status, creation time, and parameters
        - Jobs can be in states: pending, running, completed, failed
        - Use this command to monitor execution progress
    """
    message = Message()
    object_type = MANAGER.current_object().object_type()
    if object_type not in ("algorithm", "task"):
        message.add("Not able to found job", "error")
        return message
    MANAGER.current_object().jobs()
    return message


def status() -> Message:
    """Display status information for the current Celebi object.

    Shows comprehensive status information including object type, metadata,
    configuration, and execution state. The status provides a snapshot of
    the object's current condition and readiness for operations.

    Returns:
        Message: Message containing formatted status information.

    Examples:
        status()      # Show status of current object
        print(status())  # Display status in scripts

    Note:
        - Works with all Celebi object types (project, task, algorithm, data, directory)
        - Status includes: object type, path, creation time, modification time
        - For tasks/algorithms: shows input/output configuration, parameters
        - For data objects: shows size, format, metadata
        - For directories: shows contents and structure
    """
    message = Message()
    result = MANAGER.current_object().printed_status()
    message.add(str(result), "normal")
    return message


def add_input(path: str, alias: str) -> Message:  # pylint: disable=too-many-branches
    """Add an input to the current task or algorithm.

    Links an existing object (data, task output, or algorithm) as an input
    to the current task or algorithm. Inputs are referenced by alias within
    the execution context.

    Args:
        path (str): Path to the object to add as input.
        alias (str): Name to reference this input within the task/algorithm.

    Returns:
        Message: Message with status information or error messages.

    Examples:
        add-input data/file.txt input_data  # Add file as input with alias
        add-input @/tasks/prev/output result  # Add task output as input

    Note:
        - The current object must be a task or algorithm
        - Input objects must exist within the project
        - Aliases must be unique within the task/algorithm
    """
    message = Message()
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
                message.add("The number of sub-objects does not match.", "error")
                return message
            # Check whether the sub-objects name ends with _<index>
            # By getting the _<index> and check whether <index> is a digit
            for obj in sub_objects:
                ending = obj.path.split("_")[-1]
                if not ending.isdigit():
                    message.add("The sub-objects are not in indexed format.", "error")
                    return message
            for dest_obj in sub_objects:
                ending = dest_obj.path.split("_")[-1]
                if not ending.isdigit():
                    message.add("The dest-sub-objects are not in indexed format.", "error")
                    return message
            # Sort both lists by the index
            sub_objects.sort(key=lambda x: int(x.path.split("_")[-1]))
            dest_sub_objects.sort(key=lambda x: int(x.path.split("_")[-1]))
            length = len(sub_objects)
            for obj, dest_obj in zip(sub_objects, dest_sub_objects):
                if obj.path.split("_")[-1] != dest_obj.path.split("_")[-1]:
                    message.add("The sub-objects are not aligned.", "error")
                    return message
                obj_path = MANAGER.current_object().relative_path(obj.path)
                task = MANAGER.sub_object(obj_path)
                task.add_input(dest_obj.path, alias)
                if length > 100 and not int(dest_obj.path.split("_")[-1]) % (length // 10):
                    message.add(f"Progress: {int(dest_obj.path.split('_')[-1])}/{length}\n", "info")
        return message
    if MANAGER.current_object().object_type() not in ("task", "algorithm"):
        message.add("Unable to call add_input if you are not in a task or algorithm.", "error")
        return message
    MANAGER.current_object().add_input(path, alias)
    return message


def add_algorithm(path: str) -> Message:
    """Add an algorithm to the current task.

    Links an existing algorithm object to the current task for execution.
    Algorithms define computational procedures that tasks can execute.
    Multiple algorithms can be added to a single task for complex workflows.

    Args:
        path (str): Path to the algorithm object to add.

    Returns:
        Message: Message with status information or error messages.

    Examples:
        add_algorithm @/algorithms/process_data  # Add algorithm from project path
        add_algorithm ../other_project/algo      # Add algorithm from relative path

    Note:
        - Only works within task contexts
        - Algorithm must exist within the project
        - Tasks can have multiple algorithms for sequential execution
        - Algorithms are referenced by their object path within the task
    """
    message = Message()
    if MANAGER.current_object().object_type() == "directory":
        sub_objects = MANAGER.current_object().sub_objects()
        for obj in sub_objects:
            if obj.object_type() != "task":
                continue
            obj_path = MANAGER.current_object().relative_path(obj.path)
            task = MANAGER.sub_object(obj_path)
            task.add_algorithm(path)
        return message
    if MANAGER.current_object().object_type() != "task":
        message.add("Unable to call add_algorithm if you are not in a task.", "error")
        return message
    MANAGER.current_object().add_algorithm(path)
    return message


def add_parameter(par: str, value: str) -> Message:
    """Add a parameter to the current task.

    Defines execution parameters for the current task. Parameters are
    key-value pairs that configure algorithm behavior and control
    execution flow. Parameters can be referenced within algorithm code
    and affect computational results.

    Args:
        par (str): Parameter name (key).
        value (str): Parameter value.

    Returns:
        Message: Message with status information or error messages.

    Examples:
        add_parameter batch_size 32        # Add numeric parameter
        add_parameter model_name "resnet"  # Add string parameter
        add_parameter learning_rate 0.001  # Add float parameter

    Note:
        - Only works within task contexts
        - Parameter names must be valid Python identifiers
        - Values are stored as strings but can be interpreted as appropriate types
        - Parameters are passed to algorithms during execution
        - Use set_environment for environment variables instead
    """
    message = Message()
    if MANAGER.current_object().object_type() == "directory":
        sub_objects = MANAGER.current_object().sub_objects()
        for obj in sub_objects:
            if obj.object_type() != "task":
                continue
            obj_path = MANAGER.current_object().relative_path(obj.path)
            task = MANAGER.sub_object(obj_path)
            task.add_parameter(par, value)
        return message
    if MANAGER.current_object().object_type() != "task":
        message.add("Unable to call add_input if you are not in a task.", "error")
        return message
    MANAGER.current_object().add_parameter(par, value)
    return message


def add_parameter_subtask(dirname: str, par: str, value: str) -> Message:
    """Add a parameter to a specific subtask within a directory.

    Defines execution parameters for a specific task within a directory
    structure. This command allows bulk parameter configuration across
    multiple tasks organized in directories with indexed naming conventions.

    Args:
        dirname (str): Directory name containing the target task.
        par (str): Parameter name (key).
        value (str): Parameter value.

    Returns:
        Message: Message with status information or error messages.

    Examples:
        add_parameter_subtask task_1 batch_size 32        # Add to task_1
        add_parameter_subtask @/tasks/model learning_rate 0.001  # Add to task in project path

    Note:
        - Only works within directory or project contexts
        - Target directory must contain a valid task object
        - Useful for configuring multiple tasks with similar parameters
        - Directory tasks should follow indexed naming (task_1, task_2, etc.)
        - Parameters are applied to the specific task, not all tasks in directory
    """
    message = Message()
    if MANAGER.current_object().object_type() not in ("directory", "project"):
        message.add("Unable to call add_parameter_subtask if you are not in a dir", "error")
        return message
    obj = MANAGER.sub_object(dirname)
    if not obj.is_task():
        message.add("Unable to call add_parameter if you are not in a task.", "error")
        return message
    obj.add_parameter(par, value)
    return message


def set_environment(env: str) -> Message:
    """Set execution environment for the current task.

    Configures the computational environment for task execution. Environment
    settings control runtime behavior, resource allocation, and system
    dependencies. This is essential for reproducible computational workflows.

    Args:
        env (str): Environment specification string.

    Returns:
        Message: Message with status information or error messages.

    Examples:
        set_environment "python=3.8"          # Set Python version
        set_environment "cuda=11.0"           # Set CUDA version
        set_environment "conda_env=myenv"     # Set Conda environment

    Note:
        - Only works within task contexts
        - Environment specifications are parsed and validated
        - Multiple environment variables can be set in a single string
        - Environment affects algorithm execution and resource availability
        - Use add_parameter for task-specific parameters instead
    """
    message = Message()
    if MANAGER.current_object().object_type() == "directory":
        sub_objects = MANAGER.current_object().sub_objects()
        for obj in sub_objects:
            if obj.object_type() != "task":
                continue
            obj_path = MANAGER.current_object().relative_path(obj.path)
            task = MANAGER.sub_object(obj_path)
            task.set_environment(env)
        return message
    if MANAGER.current_object().object_type() != "task":
        message.add("Unable to call set_environment if you are not in a task.", "error")
        return message
    MANAGER.current_object().set_environment(env)
    return message


def set_memory_limit(limit: str) -> Message:
    """Set memory allocation limit for the current task.

    Configures the maximum memory (RAM) that can be used by task execution.
    Memory limits prevent resource exhaustion and enable fair sharing of
    computational resources across multiple tasks.

    Args:
        limit (str): Memory limit specification (e.g., "4G", "512M", "2GB").

    Returns:
        Message: Message with status information or error messages.

    Examples:
        set_memory_limit "4G"        # Set 4 gigabyte limit
        set_memory_limit "512M"      # Set 512 megabyte limit
        set_memory_limit "2GB"       # Set 2 gigabyte limit

    Note:
        - Only works within task contexts
        - Limit format: number followed by unit (M, MB, G, GB, etc.)
        - Memory limits are enforced during algorithm execution
        - Exceeding the limit may cause task termination
        - Default limits may be configured at project or system level
    """
    message = Message()
    if MANAGER.current_object().object_type() == "directory":
        sub_objects = MANAGER.current_object().sub_objects()
        for obj in sub_objects:
            if obj.object_type() != "task":
                continue
            obj_path = MANAGER.current_object().relative_path(obj.path)
            task = MANAGER.sub_object(obj_path)
            task.set_memory_limit(limit)
        return message
    if MANAGER.current_object().object_type() != "task":
        message.add("Unable to call set_memory_limit if you are not in a task.", "error")
        return message
    MANAGER.current_object().set_memory_limit(limit)
    return message


def rm_parameter(par: str) -> Message:
    """Remove a parameter from the current task.

    Deletes a previously defined parameter from the task configuration.
    This command removes the parameter key-value pair, making it unavailable
    for algorithm execution.

    Args:
        par (str): Parameter name to remove.

    Returns:
        Message: Message with status information or error messages.

    Examples:
        rm_parameter batch_size        # Remove batch_size parameter
        rm_parameter learning_rate     # Remove learning_rate parameter

    Note:
        - Only works within task contexts
        - Parameter must exist to be removed
        - Removing non-existent parameters has no effect
        - Use add_parameter to define new parameters
        - Parameter removal affects future executions, not running jobs
    """
    message = Message()
    if MANAGER.current_object().object_type() != "task":
        message.add("Unable to call remove_parameter if you are not in a task.", "error")
        return message
    MANAGER.current_object().remove_parameter(par)
    return message


def remove_input(alias: str) -> Message:
    """Remove an input from the current task or algorithm.

    Deletes a previously defined input reference from the task or algorithm
    configuration. This command removes the input alias, making the associated
    data or object unavailable for execution.

    Args:
        alias (str): Input alias to remove.

    Returns:
        Message: Message with status information or error messages.

    Examples:
        remove_input data_file        # Remove input with alias 'data_file'
        remove_input model_weights    # Remove input with alias 'model_weights'

    Note:
        - Works within task or algorithm contexts
        - Input alias must exist to be removed
        - Removing non-existent inputs has no effect
        - Use add_input to define new inputs
        - Input removal affects future executions, not running jobs
        - The underlying data object is not deleted, only the reference
    """
    message = Message()
    if MANAGER.current_object().object_type() == "directory":
        sub_objects = MANAGER.current_object().sub_objects()
        for obj in sub_objects:
            if obj.object_type() != "task":
                continue
            obj_path = MANAGER.current_object().relative_path(obj.path)
            task = MANAGER.sub_object(obj_path)
            task.remove_input(alias)
        return message
    if not MANAGER.current_object().is_task_or_algorithm():
        message.add("Unable to call remove_input if you are not in a task.", "error")
        return message
    MANAGER.current_object().remove_input(alias)
    return message


def get_script_path(filename: str) -> Message:
    """Get the script path for a algorithm or a task object.

    Resolves a filename to its full filesystem path within the context of
    the current algorithm or task. Handles special prefixes like "code/"
    to reference algorithm code from within tasks.

    Args:
        filename (str): Filename to resolve, optionally with "code/" or
            "code:" prefix to reference algorithm code.

    Examples:
        get_script_path("script.py")  # Path in current object
        get_script_path("code/main.py")  # Path in associated algorithm
        get_script_path("code:utils.py")  # Alternative prefix syntax

    Returns:
        Message: Message containing resolved path in data["path"], or error message.

    Note:
        - Current object must be a task or algorithm
        - "code/" prefix resolves to associated algorithm's path
        - Returns absolute filesystem path
        - Useful for script execution or file operations
    """
    message = Message()
    if not MANAGER.current_object().is_task_or_algorithm():
        message.add("Not able to get script path if you are not in a task or algorithm.", "error")
        return message
    if MANAGER.current_object().object_type() == "task":
        if filename.startswith("code/"):
            algorithm = MANAGER.current_object().algorithm()
            path = f"{algorithm.path}/{filename[5:]}"
            message.add(path, "normal")
            message.data["path"] = path
            return message
        if filename.startswith("code:"):
            algorithm = MANAGER.current_object().algorithm()
            path = f"{algorithm.path}/{filename[5:]}"
            message.add(path, "normal")
            message.data["path"] = path
            return message
        path = f"{MANAGER.current_object().path}/{filename}"
        message.add(path, "normal")
        message.data["path"] = path
        return message
    path = f"{MANAGER.current_object().path}/{filename}"
    message.add(path, "normal")
    message.data["path"] = path
    return message


def config() -> Message:
    """Edit configuration for current task or algorithm.

    Opens the configuration file (celebi.yaml) for the current task or
    algorithm in the system's default text editor. Creates a template
    configuration file if one doesn't exist.

    Args:
        None: Function takes no parameters.

    Examples:
        config()  # Edit configuration for current object

    Returns:
        Message: Message with status information or error message.

    Note:
        - Current object must be a task or algorithm
        - Uses editor from ~/.celebi/config.yaml or defaults to "vi"
        - Creates template with appropriate defaults for object type
        - Configuration changes affect object behavior and execution
    """
    message = Message()
    if not MANAGER.current_object().is_task_or_algorithm():
        message.add("Not able to config", "error")
        return message
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
    return message
