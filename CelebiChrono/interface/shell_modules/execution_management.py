"""
Execution management functions for shell interface.

Functions for submitting, purging, and collecting task execution results.
"""
from ...utils.message import Message
from ._manager import MANAGER


def submit(runner: str = "local") -> Message:
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
        Message containing submission confirmation, runner assignment details,
        and task execution status information.

    Note:
        - The current object must be a task
        - The task must have a valid algorithm and inputs configured
        - Runner must be available and configured
    """
    message = MANAGER.current_object().submit(runner)
    return message


def submit_objects(object_names: list[str], runner: str = "local") -> Message:
    """Submit named sub-objects of the current object for execution.

    Resolves each name relative to the current working directory, then calls
    submit_objects() on the current object so the selected tasks are deposited,
    validated and submitted in one batch (matching the behaviour of submit in
    a directory).

    Args:
        object_names: List of sub-object names or relative paths.
        runner (str, optional): Name of the runner to use. Defaults to "local".

    Returns:
        Message containing submission confirmation for each object.
    """
    message = Message()
    objects = []
    for name in object_names:
        try:
            objects.append(MANAGER.sub_object(name))
        except Exception as e:  # pylint: disable=broad-except
            message.add(f"Error resolving {name}: {e}", "error")
            return message
    return MANAGER.current_object().submit_objects(objects, runner)


def purge() -> Message:
    """Purge temporary files and cleanup current object.

    Removes temporary files, cache data, and other non-essential artifacts
    associated with the current object. This helps free up disk space and
    resolve potential consistency issues.

    Args:
        None: Function takes no parameters.

    Examples:
        purge()  # Clean up temporary files for current object

    Returns:
        Message containing cleanup confirmation and details about purged data.

    Note:
        The exact behavior depends on the object type.
        Some objects may have protected data that cannot be purged.
        Use with caution as purged data cannot be recovered.
    """
    message = MANAGER.current_object().purge()
    return message


def purge_old_impressions() -> Message:
    """Purge old impression data from current object.

    Removes historical impression data that is no longer needed, preserving
    only recent or essential impressions. Impressions are visualization
    or snapshot data generated during task execution.

    Args:
        None: Function takes no parameters.

    Examples:
        purge_old_impressions()  # Remove outdated impressions

    Returns:
        Message containing cleanup confirmation and details about purged impressions.

    Note:
        The age threshold for 'old' impressions is configurable.
        Some impression data may be protected from deletion.
        Helps manage storage usage for long-running projects.
    """
    message = MANAGER.current_object().purge_old_impressions()
    return message


def collect(contents: str = "") -> Message:
    """Collect task results. contents: '', 'all', 'plots', 'data', 'logs',
    or a glob/filename. Default ('') collects plots + logs."""
    return MANAGER.current_object().collect(contents)


def collect_outputs() -> Message:
    """Collect only task outputs.

    Retrieves output files and data from a completed task execution,
    excluding logs. This is a convenience wrapper for `collect("outputs")`.

    Returns:
        Message containing outputs collection success/failure status,
        list of retrieved output files, and any download statistics.

    Examples:
        collect_outputs()  # Retrieve only output files from completed task

    Note:
        - The current object must be a task
        - Task must have been submitted and completed
        - Output files are downloaded from the runner to local storage
        - Related functions: `collect()` for both outputs and logs, `collect_logs()` for only logs
    """
    return MANAGER.current_object().collect("outputs")


def refresh_filelists() -> Message:
    """Force a live re-listing of the runner's stageout and logs.

    Terminal workflows are no longer polled, so their saved file listing
    freezes at the terminal stamp; this re-lists the runner on demand so
    status shows a fresh table.

    Returns:
        Message with per-runner listing counts (or kept-listing warnings).

    Note:
        - The current object must be a task
        - Requires connection to DITE server
    """
    return MANAGER.current_object().refresh_filelists()


def purge_data(force: bool = False) -> Message:
    """Purge the collected data of the current task's impression.

    Removes locally collected stageout, logs, and watermarks on the
    DITE server, freeing local disk. The server refuses when the runner
    no longer holds a copy unless force is True.

    Returns:
        Message with the freed byte counts or the refusal reason.

    Note:
        - The current object must be a task
        - Requires connection to DITE server
    """
    return MANAGER.current_object().purge_data(force=force)


def collect_logs() -> Message:
    """Collect only task logs.

    Retrieves log files from a completed task execution,
    excluding output data. This is a convenience wrapper for `collect("logs")`.

    Returns:
        Message containing logs collection success/failure status,
        list of retrieved log files, and any download statistics.

    Examples:
        collect_logs()  # Retrieve only log files from completed task

    Note:
        - The current object must be a task
        - Task must have been submitted and completed
        - Log files are downloaded from the runner to local storage
        - Related functions: `collect()` for both outputs and logs,
          `collect_outputs()` for only outputs
    """
    return MANAGER.current_object().collect("logs")

def test() -> Message:
    """Test execution management functions.

    Run a specified command inside a Docker container using the given Docker image.

    Returns:
        Message containing test results, including any errors or failures encountered.

    Note:
        This is a placeholder function for testing purposes and may not be fully implemented.
    """
    return MANAGER.current_object().docker_test()


def ssh_test(runner: str = "") -> Message:
    """Run the task's algorithm commands on a registered ssh runner.

    The connection details are fetched from the DITE server; the client
    then connects directly and streams the remote output. No impression
    is created.

    Note:
        - The current object must be a task
        - Requires connection to DITE server to look up the runner config
        - Related function: `test()` for the local docker test
    """
    return MANAGER.current_object().ssh_test(runner)


def check_results(runner: str = "") -> Message:
    """Mount the current impression's cached results into a check dir on an
    ssh runner.

    Each cache entry is symlinked individually into a fresh timestamped
    check dir under ``<remote_workdir>/tests/check/``; the remote path is
    reported for manual inspection.

    Note:
        - The current object must be a task
        - Requires connection to DITE server to look up the runner config
        - Related function: `cache_results()` to cache results on the runner
    """
    return MANAGER.current_object().check_results(runner)


def engine_logs(fetch: bool = False) -> Message:
    """Fetch and display engine logs for the current task.

    Retrieves documented engine logs from the DITE server for the current
    task's impression. Engine logs provide detailed information about the
    execution environment, workflow engine operations, and runtime events.

    Args:
        None: Function takes no parameters.

    Examples:
        engine_logs()  # Display engine logs for current task

    Returns:
        Message containing engine log content or error message if logs
        cannot be retrieved.

    Note:
        - The current object must be a task with an active impression
        - Requires connection to DITE server
        - Logs are fetched from http://localhost:3315/engine-log/
        - Useful for debugging execution issues and monitoring workflow
    """
    return MANAGER.current_object().engine_logs(fetch=fetch)
