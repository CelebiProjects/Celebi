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


def purge() -> None:
    """Purge temporary files and cleanup current object.

    Removes temporary files, cache data, and other non-essential artifacts
    associated with the current object. This helps free up disk space and
    resolve potential consistency issues.

    Args:
        None: Function takes no parameters.

    Examples:
        purge()  # Clean up temporary files for current object

    Returns:
        None: Function executes cleanup and prints confirmation message.

    Note:
        The exact behavior depends on the object type.
        Some objects may have protected data that cannot be purged.
        Use with caution as purged data cannot be recovered.
    """
    message = MANAGER.current_object().purge()
    print(message.colored())


def purge_old_impressions() -> None:
    """Purge old impression data from current object.

    Removes historical impression data that is no longer needed, preserving
    only recent or essential impressions. Impressions are visualization
    or snapshot data generated during task execution.

    Args:
        None: Function takes no parameters.

    Examples:
        purge_old_impressions()  # Remove outdated impressions

    Returns:
        None: Function executes cleanup and prints confirmation message.

    Note:
        The age threshold for 'old' impressions is configurable.
        Some impression data may be protected from deletion.
        Helps manage storage usage for long-running projects.
    """
    message = MANAGER.current_object().purge_old_impressions()
    print(message.colored())


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
        Message containing collection success/failure status, list of retrieved
        files, and any download or transfer statistics.

    Note:
        - The current object must be a task
        - Task must have been submitted and completed
        - Collection may download files from remote runners
        - Convenience functions: `collect_outputs()` for only outputs, `collect_logs()` for only logs
    """
    # Validate contents parameter
    valid_contents = {"all", "outputs", "logs"}
    if contents not in valid_contents:
        print(f"Error: contents must be one of {sorted(valid_contents)}, got '{contents}'")
        # Return an error message instead of raising exception to maintain API consistency
        return Message(f"Invalid contents parameter: '{contents}'", is_error=True)

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
        - Related functions: `collect()` for both outputs and logs, `collect_outputs()` for only outputs
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
