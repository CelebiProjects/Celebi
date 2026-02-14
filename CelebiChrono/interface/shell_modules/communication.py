"""
Communication functions for shell interface.

Functions for managing hosts, runners, and DITE communication.
"""
import os

from ...utils import csys
from ...utils.message import Message
from ...utils.pretty import colorize
from ...utils import metadata
from ...kernel.chern_communicator import ChernCommunicator
from ._manager import MANAGER


def add_host(host: str, url: str) -> None:
    """Add a host to the communicator.

    Registers a new host with the Chern communicator system, enabling
    communication with remote services and runners. Hosts are used for
    distributed task execution and data transfer.

    Args:
        host (str): Unique identifier name for the host.
        url (str): Network address or URL where the host is accessible.

    Examples:
        add_host localhost http://127.0.0.1:8080
        add_host cluster-01 https://cluster.example.com/api

    Returns:
        None: Function executes side effect of adding host configuration.

    Note:
        - Host names must be unique within the communicator
        - URL should be accessible from the current network
        - Host configuration is persisted in project settings
    """
    cherncc = ChernCommunicator.instance()
    cherncc.add_host(host, url)


def hosts() -> None:
    """Show all hosts and their status.

    Displays a formatted table of all configured hosts with their current
    connection status. Host status indicates whether the communicator can
    successfully connect to each host.

    Args:
        None: Function takes no parameters.

    Examples:
        hosts()  # Display all hosts and their status

    Returns:
        None: Output is printed to console in formatted table.

    Note:
        - Status "ok" indicates successful connection
        - Status "unconnected" indicates connection failure
        - Colors are used to visually distinguish statuses
        - Host list is retrieved from Chern communicator
    """
    cherncc = ChernCommunicator.instance()
    host_list = cherncc.hosts()
    print(f"{'HOSTS':<20}{'STATUS':20}")
    for host in host_list:
        host_status = cherncc.host_status(host)
        color_tag = {"ok": "ok", "unconnected": "warning"}[host_status]
        print(f"{host:<20}{colorize(host_status, color_tag):20}")


def dite() -> None:
    """Show DITE information.

    Displays information about the Distributed Task Execution (DITE) system,
    including connection status, configuration details, and available services.
    DITE manages distributed task execution across multiple runners.

    Args:
        None: Function takes no parameters.

    Examples:
        dite()  # Display DITE system information

    Returns:
        None: Output is printed to console with DITE details.

    Note:
        - DITE must be properly configured for distributed execution
        - Information includes connection URLs and service status
        - Requires Chern communicator to be initialized
    """
    cherncc = ChernCommunicator.instance()
    dite_info = cherncc.dite_info()
    print(dite_info)


def set_dite(url: str = "") -> None:
    """Set DITE connection.

    Configures or updates the Distributed Task Execution (DITE) server URL
    for the current project. The URL is persisted in project configuration
    and used for all subsequent distributed task operations.

    Args:
        url (str, optional): DITE server URL to connect to. If empty string,
            function displays current configuration without changes.

    Examples:
        set_dite https://dite.example.com/api
        set_dite()  # Show current DITE configuration

    Returns:
        None: Function updates configuration or displays current settings.

    Note:
        - URL is saved to project's .celebi/hosts.json file
        - Empty URL parameter displays current configuration
        - Changes affect all distributed operations in the project
        - Requires project to be initialized
    """
    project_path = csys.project_path()
    config_path = os.path.join(project_path, ".celebi", "hosts.json")
    config_file = metadata.ConfigFile(config_path)
    if url:
        config_file.write_variable("serverurl", url)
        print(f"DITE URL set to: {url}")


def runners() -> Message:
    """Display all available runners.

    Retrieves and displays information about all task execution runners
    available through the DITE system. Shows runner names, connection URLs,
    and current status (Connected/Disconnected).

    Args:
        None: Function takes no parameters.

    Examples:
        runners()  # List all available runners with status

    Returns:
        Message: Formatted message object containing runner information table,
        status indicators, and connection details. Includes warning if DITE
        is not connected.

    Note:
        - Requires DITE connection to be established
        - Runner status indicates current connectivity
        - Information is retrieved from Chern communicator
        - Message uses color coding for status display
    """
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
    """Register a runner with DITE.

    Registers a new task execution runner with the Distributed Task Execution
    (DITE) system. Runners execute tasks and must be registered before they
    can be used for distributed computation.

    Args:
        runner (str): Unique identifier name for the runner.
        url (str): Network address where the runner service is accessible.
        secret (str): Authentication secret or token for runner access.
        backend_type (str): Type of execution backend (e.g., "docker", "slurm").

    Examples:
        register_runner local-runner http://localhost:8080 secret123 docker
        register_runner gpu-cluster https://cluster.example.com token456 slurm

    Returns:
        None: Function executes side effect of registering runner with DITE.

    Note:
        - Runner names must be unique within DITE
        - URL must be accessible from DITE server
        - Secret is used for secure communication
        - Backend type determines execution environment
    """
    cherncc = ChernCommunicator.instance()
    cherncc.register_runner(runner, url, secret, backend_type)


def remove_runner(runner: str) -> None:
    """Remove a runner from DITE.

    Unregisters a task execution runner from the Distributed Task Execution
    (DITE) system. Removed runners will no longer be available for task
    execution.

    Args:
        runner (str): Name of the runner to remove.

    Examples:
        remove_runner old-runner
        remove_runner deprecated-cluster

    Returns:
        None: Function executes side effect of removing runner from DITE.

    Note:
        - Runner must be registered to be removed
        - Removal affects future task submissions
        - Currently executing tasks may be affected
        - Requires appropriate permissions in DITE
    """
    cherncc = ChernCommunicator.instance()
    cherncc.remove_runner(runner)


def request_runner(runner: str) -> None:
    """Set the requested runner for current task.

    Specifies which runner should be used for executing the current task.
    The runner must be available through DITE and properly configured.

    Args:
        runner (str): Name of the runner to use for task execution.

    Examples:
        request_runner local
        request_runner gpu-cluster-01

    Returns:
        None: Function sets runner preference on current task object.

    Note:
        - Runner must be registered with DITE
        - Current object must be a task
        - Runner preference is saved with task configuration
        - Default runner can be overridden at submission time
    """
    MANAGER.current_object().set_default_runner(runner)


def search_impression(partial_uuid: str) -> Message:
    """Search impressions by partial UUID.

    Searches for task execution impressions using a partial UUID match.
    Impressions are visualization snapshots or execution records that can
    be retrieved for analysis or debugging.

    Args:
        partial_uuid (str): Partial UUID string to search for impressions.

    Examples:
        search_impression abc123
        search_impression 2024-01

    Returns:
        Message: Search results containing matching impressions, including
        UUIDs, creation times, and associated task information.

    Note:
        - Partial UUID can match any part of the full UUID
        - Search is case-insensitive
        - Current object context affects search scope
        - Results may include impressions from related tasks
    """
    print("Search partial uuid", partial_uuid)
    message = MANAGER.current_object().search_impression(partial_uuid)
    return message