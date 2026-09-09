"""Execution management commands for Celebi CLI."""
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


def _raw_output(result: Optional[Any]) -> str:
    """Return the raw text of a shell result for byte-offset tracking."""
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    if hasattr(result, "messages"):
        return "".join(text for text, _ in result.messages)
    return str(result)


_RUNNER_SETTING_OPTIONS = [
    click.option("--ssh-host", type=str, default=None, help="SSH host (ssh backend)"),
    click.option("--ssh-user", type=str, default=None, help="SSH user (ssh backend)"),
    click.option("--ssh-key-path", type=str, default=None, help="SSH private key path"),
    click.option("--ssh-port", type=int, default=None, help="SSH port"),
    click.option("--remote-workdir", type=str, default=None,
                 help="Remote working directory (ssh backend)"),
    click.option("--workdir", type=str, default=None,
                 help="Local working directory (native backend)"),
    click.option("--cores", type=int, default=None, help="Snakemake cores"),
    click.option("--mem-mb", type=int, default=None, help="Snakemake memory (MB)"),
    click.option("--conda-path", type=str, default=None,
                 help="Path to conda executable"),
    click.option("--snakemake-path", type=str, default=None,
                 help="Path to snakemake executable"),
]

_SETTING_KEYS = ("ssh_host", "ssh_user", "ssh_key_path", "ssh_port",
                 "remote_workdir", "workdir", "cores", "mem_mb",
                 "conda_path", "snakemake_path")


def _runner_setting_options(func):
    """Runner setting options."""
    for option in reversed(_RUNNER_SETTING_OPTIONS):
        func = option(func)
    return func


def _collect_cli_settings(kwargs):
    """Collect cli settings."""
    return {key: kwargs[key] for key in _SETTING_KEYS
            if kwargs.get(key) is not None}


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
@_runner_setting_options
def register_runner_command(name: str, url: str, secret: str,
                            backend_type: str, **kwargs) -> None:
    """Register a new runner with DITE.

    Registers a task execution runner with the Distributed Task Execution
    (DITE) system. Runners must be registered before they can be used for
    distributed computation.

    NAME: Unique identifier for the runner.
    URL: Network address where the runner service is accessible.
    SECRET: Authentication secret or token for runner access.
    BACKEND_TYPE: Type of execution backend (e.g., "docker", "slurm").

    Additional runner settings (SSH connection, workdir, snakemake
    resources, conda/snakemake paths) can be supplied as options.

    Note:
        - Runner names must be unique within DITE
        - URL must be accessible from DITE server
        - Secret is used for secure communication
        - Backend type determines execution environment
    """
    try:
        from CelebiChrono.interface.shell import register_runner
        _handle_result(register_runner(name, url, secret, backend_type,
                                       **_collect_cli_settings(kwargs)))
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


@click.command(name="update-runner")
@click.argument("name", type=str)
@click.option("--url", type=str, default=None, help="Runner service URL")
@click.option("--token", type=str, default=None, help="Authentication token")
@click.option("--backend-type", type=str, default=None, help="Backend type (reana/native)")
@click.option("--use-kerberos/--no-use-kerberos", default=None, help="Enable/disable Kerberos")
@click.option("--eos-mount-point", type=str, default=None, help="EOS mount point path")
@_runner_setting_options
# Click options mirror the public CLI; number of options is expected.
# pylint: disable=too-many-arguments,too-many-positional-arguments
def update_runner_command(name, url, token, backend_type, use_kerberos,
                          eos_mount_point, **kwargs):
    """Update settings for an existing runner.

    NAME is the runner to update. Only the provided options are changed.
    """
    try:
        from CelebiChrono.interface.shell import update_runner
        settings = {}
        if url is not None:
            settings["url"] = url
        if token is not None:
            settings["token"] = token
        if backend_type is not None:
            settings["backend_type"] = backend_type
        if use_kerberos is not None:
            settings["use_kerberos"] = use_kerberos
        if eos_mount_point is not None:
            settings["eos_mount_point"] = eos_mount_point
        settings.update(_collect_cli_settings(kwargs))
        _handle_result(update_runner(name, **settings))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="test-runner")
@click.argument("runner", type=str)
@click.option("--timeout", type=int, default=None,
              help="Probe command timeout in seconds (default: server default)")
def test_runner_command(runner: str, timeout: int) -> None:
    """Probe a runner's capabilities (snakemake/conda/workdir) via DITE.

    RUNNER is the name of the registered runner to test. Results are stored
    on the server and shown in 'celebi-cli runners'.
    """
    try:
        from CelebiChrono.interface.shell import test_runner
        _handle_result(test_runner(runner, timeout=timeout))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="yuki-overview")
def yuki_overview_command() -> None:
    """Show an aggregate overview of Yuki runners and usage."""
    try:
        from CelebiChrono.interface.shell import yuki_overview
        _handle_result(yuki_overview())
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="refresh-distribution")
def refresh_distribution_command() -> None:
    """Refresh the current project's distribution registry."""
    try:
        from CelebiChrono.interface.shell import refresh_distribution
        _handle_result(refresh_distribution())
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="purge-ssh-runner-cache")
@click.argument("runner", type=str)
@click.option("--project", type=str, default=None,
              help="Only purge cached impressions of this project.")
@click.option("--impression", type=str, default=None,
              help="Only purge this cached impression.")
@click.option("--dry-run", is_flag=True,
              help="List what would be purged without deleting anything.")
@click.option("--yes", "-y", is_flag=True,
              help="Skip the confirmation prompt.")
def purge_ssh_runner_cache_command(runner: str, project: str,
                                   impression: str, dry_run: bool,
                                   yes: bool) -> None:
    """Purge cached impressions from an ssh runner via DITE.

    RUNNER is the name of the registered runner whose remote cache is
    purged. Registered data only lives on the runner — restore it with
    register-ssh-data.
    """
    try:
        from CelebiChrono.interface.shell import purge_ssh_runner_cache
        if not dry_run and not yes:
            click.confirm(
                f"Purge the impressions cache on ssh runner '{runner}'?",
                abort=True)
        _handle_result(purge_ssh_runner_cache(
            runner, project=project, impression=impression,
            dry_run=dry_run))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="whereabouts")
def whereabouts_command() -> None:
    """Report where the current impression's data lives via DITE.

    Shows which runners hold the data, whether it is cached in their
    managed impressions caches, and whether it is in yuki storage.
    """
    try:
        from CelebiChrono.interface.shell import whereabouts
        _handle_result(whereabouts())
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="cache-results")
@click.argument("runner", type=str)
def cache_results_command(runner: str) -> None:
    """Cache the current impression's results on an ssh runner via DITE.

    RUNNER is the name of the registered runner hosting the results. The
    workflow's stageout is copied into the runner's managed impressions
    cache and recorded in the distribution registry.
    """
    try:
        from CelebiChrono.interface.shell import cache_results
        _handle_result(cache_results(runner))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="runner-envs")
@click.argument("runner", type=str)
def runner_envs_command(runner: str) -> None:
    """List conda environments available on a runner (ssh/native).

    RUNNER is the name of the registered runner. The list is fetched live
    from the runner via the DITE server.
    """
    try:
        from CelebiChrono.interface.shell import runner_envs
        _handle_result(runner_envs(runner))
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
@click.argument("contents", type=str, default="", required=False)
def collect_command(contents: str) -> None:
    """Collect task results: [all|plots|data|logs|<glob>|<name>] (default: plots+logs)."""
    try:
        from CelebiChrono.interface.shell import collect
        _handle_result(collect(contents))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="log")
@click.argument("index", type=int, default=0, required=False)
@click.option("--follow", "-f", is_flag=True, default=False,
              help="Continuously poll for new log content.")
@click.option("--poll-interval", "-i", type=float, default=2.0,
              help="Seconds between polls when --follow is set (default: 2).")
def log_command(index: int, follow: bool, poll_interval: float) -> None:
    """View error log for the current task.

    Retrieves error log entries for the current object. Error logs
    capture execution failures, warnings, and diagnostic information.

    INDEX specifies which log entry to retrieve (default: 0 for most recent).

    With --follow, the command prints the current log and then polls for
    new content every --poll-interval seconds until interrupted.
    """
    try:
        from CelebiChrono.interface.shell import error_log
        if not follow:
            result = error_log(index)
            output = format_output(result)
            if output:
                print(output, end="")
            else:
                print("No log content found")
            return

        import time

        offset = 0
        while True:
            result = error_log(index, offset=offset)
            output = format_output(result)
            if output:
                print(output, end="")
                offset += len(_raw_output(result).encode("utf-8"))
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        return
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
        from CelebiChrono.utils import user_config

        result = get_script_path(script)
        if not result.success:
            _handle_error(result.messages[0][0] if result.messages else "Script not found")
            return

        file_path = result.data["path"]
        editor = user_config.get("editor")
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


@click.command(name="refresh-filelists")
def refresh_filelists_command() -> None:
    """Force a live re-listing of the runner's stageout and logs.

    Terminal workflows are no longer polled, so their saved file listing
    freezes at the terminal stamp; this re-lists the runner on demand so
    status shows a fresh table.

    Note:
        - The current object must be a task
        - Requires connection to DITE server
    """
    try:
        from CelebiChrono.interface.shell import refresh_filelists
        result = refresh_filelists()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="purge-data")
@click.option("--force", is_flag=True, default=False,
              help="Purge even when the data cannot be re-collected "
                   "from a runner.")
def purge_data_command(force: bool) -> None:
    """Purge the collected data of the current impression.

    Removes the locally collected stageout, logs, and watermarks of the
    current task's impression on the DITE server, freeing local disk.
    The server refuses when the runner no longer holds a copy of the
    data unless --force is given.

    Note:
        - The current object must be a task
        - Requires connection to DITE server
    """
    try:
        from CelebiChrono.interface.shell import purge_data
        result = purge_data(force=force)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="engine-logs")
@click.option("--fetch", is_flag=True, default=False,
              help="Generate the engine logs on the server if missing.")
def engine_logs_command(fetch: bool) -> None:
    """Fetch and display engine logs for the current task.

    Retrieves documented engine logs from the DITE server for the current
    task's impression. Engine logs provide detailed information about the
    execution environment, workflow engine operations, and runtime events.

    Must be used within a task context and requires connection to DITE server.
    """
    try:
        from CelebiChrono.interface.shell import engine_logs
        result = engine_logs(fetch=fetch)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")
