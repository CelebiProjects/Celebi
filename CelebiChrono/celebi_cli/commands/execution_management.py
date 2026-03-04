"""Execution management commands for Celebi CLI."""
import os
import sys
import subprocess
from typing import Optional, Any
import click
from CelebiChrono.celebi_cli.utils import format_output


def _handle_result(result: Optional[Any]) -> None:
    """Handle result from shell function."""
    output = format_output(result)
    if output:
        print(output)


def _handle_error(error: str) -> None:
    """Handle error from shell function."""
    print(f"Error: {error}", file=sys.stderr)
    sys.exit(1)


@click.command(name="test")
def test_command() -> None:
    """Test execution management functions.

    Run a specified command inside a Docker container using the given Docker image.

    Must be used within a task context. The current task's algorithm is tested
    in a Docker container to verify execution environment compatibility.

    Note:
        This is a placeholder function for testing purposes and may not be fully implemented.
    """
    try:
        from CelebiChrono.interface.shell import test
        result = test()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="runners")
def runners_command() -> None:
    """Display all available runners.

    Retrieves and displays information about all task execution runners
    available through the DITE system. Shows runner names, connection URLs,
    and current status (Connected/Disconnected).

    Returns:
        Message containing runner information table with status indicators.

    Note:
        Requires DITE connection to be established.
    """
    try:
        from CelebiChrono.interface.shell import runners
        result = runners()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="register-runner")
@click.argument("name", type=str)
@click.argument("url", type=str)
@click.argument("secret", type=str)
@click.argument("backend_type", type=str)
def register_runner_command(name: str, url: str, secret: str, backend_type: str) -> None:
    """Register a new runner with DITE.

    Registers a task execution runner with the Distributed Task Execution
    (DITE) system. Runners must be registered before they can be used for
    distributed computation.

    NAME: Unique identifier for the runner.
    URL: Network address where the runner service is accessible.
    SECRET: Authentication secret or token for runner access.
    BACKEND_TYPE: Type of execution backend (e.g., "docker", "slurm").

    Note:
        - Runner names must be unique within DITE
        - URL must be accessible from DITE server
        - Secret is used for secure communication
        - Backend type determines execution environment
    """
    try:
        from CelebiChrono.interface.shell import register_runner
        _handle_result(register_runner(name, url, secret, backend_type))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="remove-runner")
@click.argument("runner", type=str)
def remove_runner_command(runner: str) -> None:
    """Remove a runner from DITE.

    Unregisters a task execution runner from the Distributed Task Execution
    (DITE) system. Removed runners will no longer be available for task
    execution.

    RUNNER: Name of the runner to remove.

    Note:
        - Runner must be registered to be removed
        - Removal affects future task submissions
        - Currently executing tasks may be affected
        - Requires appropriate permissions in DITE
    """
    try:
        from CelebiChrono.interface.shell import remove_runner
        _handle_result(remove_runner(runner))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="submit")
@click.argument("runner", type=str, default="local", required=False)
def submit_command(runner: str) -> None:
    """Submit current task for execution.

    Sends the current task to a runner for processing. The runner executes
    the task's algorithm with the specified inputs and parameters.

    RUNNER is the name of the execution environment to use (defaults to "local").
    """
    try:
        from CelebiChrono.interface.shell import submit
        result = submit(runner)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="collect")
@click.argument("contents", type=str, default="all", required=False)
def collect_command(contents: str) -> None:
    """Collect task execution results.

    Retrieves outputs, logs, or both from a completed task execution.
    Results are gathered from the runner and made available locally.

    CONTENTS specifies what to collect: "all", "outputs", or "logs" (default: "all").
    """
    try:
        from CelebiChrono.interface.shell import collect
        result = collect(contents)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="log")
@click.argument("index", type=int, default=0, required=False)
def log_command(index: int) -> None:
    """View error log for the current task.

    Retrieves error log entries for the current object. Error logs
    capture execution failures, warnings, and diagnostic information.

    INDEX specifies which log entry to retrieve (default: 0 for most recent).
    """
    try:
        from CelebiChrono.interface.shell import error_log
        result = error_log(index)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="edit")
@click.argument("script", type=str)
def edit_command(script: str) -> None:
    """Edit a script file.

    Opens the specified script file in the configured editor (default: vi).
    The editor can be configured in ~/.celebi/config.yaml.

    SCRIPT is the name of the script file to edit.
    """
    try:
        from CelebiChrono.interface.shell import get_script_path
        from CelebiChrono.utils import metadata

        result = get_script_path(script)
        if not result.success:
            _handle_error(result.messages[0][0] if result.messages else "Script not found")
            return

        file_path = result.data["path"]
        config_path = os.path.join(os.environ["HOME"], ".celebi", "config.yaml")
        yaml_file = metadata.YamlFile(config_path)
        editor = yaml_file.read_variable("editor", "vi")
        subprocess.call([editor, file_path])
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="purge")
def purge_command() -> None:
    """Purge temporary files and cleanup current object.

    Removes temporary files, cache data, and other non-essential artifacts
    associated with the current object. This helps free up disk space and
    resolve potential consistency issues.

    Note:
        The exact behavior depends on the object type.
        Some objects may have protected data that cannot be purged.
        Use with caution as purged data cannot be recovered.
    """
    try:
        from CelebiChrono.interface.shell import purge
        result = purge()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="purge-old-impressions")
def purge_old_impressions_command() -> None:
    """Purge old impression data from current object.

    Removes historical impression data that is no longer needed, preserving
    only recent or essential impressions. Impressions are visualization
    or snapshot data generated during task execution.

    Note:
        The age threshold for 'old' impressions is configurable.
        Some impression data may be protected from deletion.
        Helps manage storage usage for long-running projects.
    """
    try:
        from CelebiChrono.interface.shell import purge_old_impressions
        result = purge_old_impressions()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="collect-outputs")
def collect_outputs_command() -> None:
    """Collect only task outputs.

    Retrieves output files and data from a completed task execution,
    excluding logs. This is a convenience wrapper for collect("outputs").

    Note:
        - The current object must be a task
        - Task must have been submitted and completed
        - Output files are downloaded from the runner to local storage
    """
    try:
        from CelebiChrono.interface.shell import collect_outputs
        result = collect_outputs()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="collect-logs")
def collect_logs_command() -> None:
    """Collect only task logs.

    Retrieves log files from a completed task execution,
    excluding output data. This is a convenience wrapper for collect("logs").

    Note:
        - The current object must be a task
        - Task must have been submitted and completed
        - Log files are downloaded from the runner to local storage
    """
    try:
        from CelebiChrono.interface.shell import collect_logs
        result = collect_logs()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="engine-logs")
def engine_logs_command() -> None:
    """Fetch and display engine logs for the current task.

    Retrieves documented engine logs from the DITE server for the current
    task's impression. Engine logs provide detailed information about the
    execution environment, workflow engine operations, and runtime events.

    Must be used within a task context and requires connection to DITE server.
    """
    try:
        from CelebiChrono.interface.shell import engine_logs
        result = engine_logs()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")
