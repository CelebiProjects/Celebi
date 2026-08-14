"""
Object creation functions for shell interface.

Functions for creating new algorithms, tasks, data objects, and directories.
"""
import os
import time

from ...utils import csys
from ...utils import metadata
from ...utils.message import Message
from ...kernel.vobject import VObject
from ...kernel.vtask import create_task
from ...kernel.vtask import create_data
from ...kernel.vtask import create_data_list
from ...kernel.vtask import create_lhcb_ap_data_list
from ...kernel.vtask import create_rawdata_task
from ...kernel.valgorithm import create_algorithm
from ...kernel.vdirectory import create_directory
from ...kernel.chern_communicator import ChernCommunicator
from ._manager import MANAGER


def _is_rawdata_task(obj_path):
    """Return True if the object at obj_path is a rawdata task."""
    yaml_path = os.path.join(obj_path, "celebi.yaml")
    if not os.path.exists(yaml_path):
        return False
    yaml_file = metadata.YamlFile(yaml_path)
    return yaml_file.read_variable("environment", "") == "rawdata"


def _fill_or_create_pointer_task(project_path, current_obj, descriptor,
                                 data_md5, path_override, origin,
                                 default_runner=None):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    """Fill an existing rawdata task or create a pointer task (shared tail
    of attach-data and register-data).

    With default_runner set (register-data), the task's default runner is
    pointed at the runner hosting the data.
    """
    message = Message()
    task_path = path_override if path_override else descriptor
    task_path = csys.refine_path(task_path, current_obj.path)
    full_path = os.path.join(current_obj.path, task_path)
    if not os.path.exists(full_path):
        parent_path = os.path.abspath(full_path + "/..")
        object_type = VObject(parent_path).object_type()
        if object_type not in ("directory", "project"):
            message.add("Not allowed to create data task here", "warning")
            return message
        create_rawdata_task(full_path, descriptor, data_md5)
        if default_runner:
            metadata.ConfigFile(
                os.path.join(full_path, ".celebi", "config.json")
            ).write_variable("default_runner", default_runner)
        message.add(f"Created rawdata task at {task_path}", "success")
        return message
    existing = VObject(full_path, project_path)
    if existing.object_type() != "task":
        message.add(f"Path {task_path} exists but is not a task "
                    f"(type: {existing.object_type()})", "error")
        return message
    yaml_path = os.path.join(full_path, "celebi.yaml")
    yaml_file = metadata.YamlFile(yaml_path)
    env = yaml_file.read_variable("environment", "")
    if env != "rawdata":
        message.add(f"Path {task_path} exists but is not a rawdata task "
                    f"(environment: {env})", "error")
        return message
    yaml_file.write_variable("uuid", data_md5)
    yaml_file.write_variable("descriptor", descriptor)
    if default_runner:
        metadata.ConfigFile(
            os.path.join(full_path, ".celebi", "config.json")
        ).write_variable("default_runner", default_runner)
    message.add(f"Updated rawdata task at {task_path} "
                f"({origin}) with new impression data", "success")
    return message


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


def create_lhcb_ap_list(line: str) -> Message:
    """Create a new LHCb AP data list object.

    Creates a new LHCb AP data list object within the current project. This task type
    dynamically generates dataList.txt by querying the LHCb Analysis Productions (AP)
    tool. The ap_config field in celebi.yaml is initialized with empty values — the
    user fills in the AP query parameters later.

    Args:
        line (str): Path where the LHCb AP data list object should be created. Must be
            within a valid directory or project location.

    Returns:
        Message: A Message object containing success or warning information

    Examples:
        create_lhcb_ap_list my_ap_list       # Create at my_ap_list/
        create_lhcb_ap_list path/to/ap_list  # Create at specific path
    """
    line = csys.refine_path(line, MANAGER.current_object().path)
    message = Message()
    parent_path = os.path.abspath(line+"/..")
    object_type = VObject(parent_path).object_type()
    if object_type not in ("directory", "project"):
        message.add("Not allowed to create LHCb AP data list here", "warning")
        return message
    create_lhcb_ap_data_list(line)
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


def verify_data() -> Message:
    """Verify the current data task: recompute its md5 against the
    registered uuid (remote-hosted data is hashed on the host runner)."""
    message = Message()
    current_obj = MANAGER.current_object()
    if current_obj is None:
        message.add("No current object selected", "error")
        return message
    if current_obj.object_type() != "task" or \
            current_obj.environment() != "rawdata":
        message.add("verify-data works on rawdata tasks", "error")
        return message
    impression = current_obj.impression()
    if impression is None:
        message.add("Task not impressed yet; run 'impress' first", "error")
        return message
    cherncc = ChernCommunicator.instance()
    try:
        result = cherncc.verify_data(current_obj.project_uuid(),
                                     impression.uuid)
    except ConnectionError as e:
        message.add(str(e), "error")
        return message
    if result.get("error"):
        message.add(result["error"], "error")
        return message
    if result["match"]:
        message.add(f"Data verified: md5 matches "
                    f"({result['expected']}) "
                    f"on {result['location']}\n", "success")
    else:
        message.add(f"Data mismatch on {result['location']}:\n", "error")
        message.add(f"  expected: {result['expected']}\n")
        message.add(f"  actual:   {result['actual']}\n")
    return message


def attach_data(impression_uuid: str, path_override: str = "") -> Message:
    """Attach a Yuki impression to a rawdata task in the current project.

    Queries Yuki for the impression info (descriptor and MD5), creates a
    matching canonical rawdata task, impresses it to generate the same UUID,
    and marks the Yuki impression as ready ('raw').

    Args:
        impression_uuid (str): The impression UUID created by yuki-create-data.
        path_override (str, optional): Custom task path. Defaults to automatic
            path based on the descriptor.

    Examples:
        attach_data abc123...
        attach_data abc123... --path my_custom_data

    Returns:
        Message: Status message for the operation.
    """
    message = Message()
    current_obj = MANAGER.current_object()
    if current_obj is None:
        message.add("No current object selected", "error")
        return message
    project_path = current_obj.project_path()
    if not project_path:
        message.add("No current project selected", "error")
        return message

    cherncc = ChernCommunicator.instance()
    info = cherncc.get_impression_info(impression_uuid)
    descriptor = info.get("descriptor", "")
    data_md5 = info.get("md5", "")

    if not descriptor or not data_md5:
        message.add(
            f"Could not retrieve impression info from Yuki for {impression_uuid}",
            "error",
        )
        return message

    if current_obj.object_type() == "task" and _is_rawdata_task(current_obj.path):
        full_path = current_obj.path
        task_path = current_obj.invariant_path()
        yaml_file = metadata.YamlFile(os.path.join(full_path, "celebi.yaml"))
        yaml_file.write_variable("uuid", data_md5)
        yaml_file.write_variable("descriptor", descriptor)
        print(
            f"attach-data: updated rawdata task via metadata.YamlFile.write_variable("
            f"{full_path}/celebi.yaml, uuid={data_md5}, descriptor={descriptor})"
        )
        message.add(
            f"Updated rawdata task at {task_path} with new impression data",
            "success",
        )
    else:
        task_path = path_override if path_override else descriptor
        task_path = csys.refine_path(task_path, current_obj.path)
        full_path = os.path.join(current_obj.path, task_path)
        result = _fill_or_create_pointer_task(
            project_path, current_obj, descriptor, data_md5,
            path_override, "attach-data")
        message.append(result)
        if any(msg_type in ("warning", "error")
               for _, msg_type in result.messages):
            return message
        print(
            f"attach-data: created or updated rawdata task via "
            f"_fill_or_create_pointer_task({full_path})"
        )

    task_obj = VObject(full_path, project_path)
    task_obj.impress()
    local_uuid = task_obj.config_file.read_variable("impression", "")

    if local_uuid != impression_uuid:
        message.add(
            f"UUID mismatch: local={local_uuid}, yuki={impression_uuid}. "
            "The task configuration may differ from the canonical rawdata task.",
            "error",
        )
        return message

    result = cherncc.set_impression_status(impression_uuid, "archived")
    if result == "OK":
        message.add(
            f"Successfully adopted impression {impression_uuid} as task {task_path}",
            "success",
        )
    else:
        message.add(
            f"Impressed locally but failed to mark Yuki status as archived: {result}",
            "warning",
        )
    return message


def _fill_registered_data(project_path, current_obj, descriptor, data_md5,
                          origin, default_runner=None):
    """Dual-mode tail of register-data: fill the current rawdata task, or
    create/update a pointer task via the shared tail."""
    message = Message()
    if current_obj.object_type() == "task" and _is_rawdata_task(current_obj.path):
        task_path = current_obj.invariant_path()
        yaml_file = metadata.YamlFile(
            os.path.join(current_obj.path, "celebi.yaml"))
        yaml_file.write_variable("uuid", data_md5)
        yaml_file.write_variable("descriptor", descriptor)
        if default_runner:
            current_obj.set_default_runner(default_runner)
        message.add(
            f"Updated rawdata task at {task_path} ({origin}) with new "
            "impression data", "success")
        return message
    message.messages.extend(_fill_or_create_pointer_task(
        project_path, current_obj, descriptor, data_md5, "", origin,
        default_runner=default_runner).messages)
    return message


def register_data(runner: str, remote_path: str, descriptor: str = "") -> Message:
    # pylint: disable=too-many-return-statements
    """Register data living on an ssh runner into Yuki's managed staging.

    Computes the data MD5 and copies it into the runner's managed
    impressions area (hashing/copying run as a background job on Yuki).
    On success, fills the current rawdata task (or creates a pointer task)
    with the registered impression.
    """
    message = Message()
    current_obj = MANAGER.current_object()
    if current_obj is None:
        message.add("No current object selected", "error")
        return message
    project_path = current_obj.project_path()
    if not project_path:
        message.add("No current project selected", "error")
        return message
    if current_obj.object_type() == "task" and \
            not _is_rawdata_task(current_obj.path):
        message.add("Current task is not a rawdata task; run register-data "
                    "from a rawdata task or outside a task", "error")
        return message

    cherncc = ChernCommunicator.instance()
    resp = cherncc.register_remote_data(runner, remote_path,
                                        current_obj.project_uuid(),
                                        descriptor or None)
    if "error" in resp:
        message.add(resp["error"], "error")
        return message
    if "result" in resp:
        # Idempotent re-registration: the impression already exists, so the
        # server returned the final result without starting a job.
        result = resp["result"]
        message.add(
            f"Registered: md5={result['uuid']} "
            f"impression={result['impression_uuid']}", "success")
        message.messages.extend(_fill_registered_data(
            project_path, current_obj, result["descriptor"],
            result["uuid"], "register-data",
            default_runner=runner).messages)
        return message
    if "job_id" not in resp:
        message.add("Registration failed: server returned neither a job id "
                    "nor a result", "error")
        return message
    job_id = resp["job_id"]
    print(f"register-data: job {job_id[:8]}... started on '{runner}'")
    consecutive_unknowns = 0
    while True:
        state = cherncc.register_remote_data_status(job_id)
        status = state.get("status", "unknown")
        if status == "unknown":
            consecutive_unknowns += 1
            if consecutive_unknowns >= 10:
                message.add(
                    f"Registration job {job_id[:8]}... status 'unknown' "
                    f"{consecutive_unknowns} times in a row (job not found on "
                    "the server); aborting after ~30s. The server may have "
                    "restarted or dropped the job.", "error")
                return message
        else:
            consecutive_unknowns = 0
        if status == "done":
            result = state["result"]
            message.add(
                f"Registered: md5={result['uuid']} "
                f"impression={result['impression_uuid']}\n", "success")
            message.messages.extend(_fill_registered_data(
                project_path, current_obj, result["descriptor"],
                result["uuid"], "register-data",
            default_runner=runner).messages)
            return message
        if status == "failed":
            message.add(f"Registration failed: {state.get('error')}", "error")
            return message
        print(f"register-data: {status}...")
        time.sleep(3)
