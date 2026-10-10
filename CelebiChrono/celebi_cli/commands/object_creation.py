"""Object Creation commands for Celebi CLI."""

import os
import sys
import click

from CelebiChrono.celebi_cli.utils import format_output

def _handle_result(result):
    """Handle result from shell function."""
    output = format_output(result)
    if output:
        print(output)

def _handle_error(error):
    """Handle error from shell function."""
    print(f"Error: {error}", file=sys.stderr)
    sys.exit(1)

@click.command(name="create-algorithm")
@click.argument("name", type=str)
def create_algorithm_command(name):
    """Create algorithm."""
    try:
        from CelebiChrono.interface.shell import mkalgorithm
        result = mkalgorithm(name)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")

@click.command(name="create-task")
@click.argument("name", type=str)
def create_task_command(name):
    """Create task."""
    try:
        from CelebiChrono.interface.shell import mktask
        result = mktask(name)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="create-multi-tasks")
@click.argument("base_name", type=str)
@click.argument("stop", type=int)
@click.option("--start", type=int, default=0, show_default=True)
def create_multi_tasks_command(base_name, stop, start):
    """Create a numbered range of tasks.

    Creates BASE_NAME_N for each N in the half-open range START <= N < STOP
    and sets that task's `index` parameter to N. The range may contain at
    most 10000 tasks.

    Example: create-multi-tasks simulation 20 --start 10
    """
    try:
        from CelebiChrono.interface.shell import mktask, add_parameter_subtask
        count = stop - start
        if count <= 0 or count > 10000:
            raise click.BadParameter(
                "STOP must be greater than START and select at most 10000 items"
            )
        for index in range(start, stop):
            task_name = f"{base_name}_{index}"
            result = mktask(task_name)
            _handle_result(result)
            if result is None or getattr(result, "success", True):
                _handle_result(add_parameter_subtask(task_name, "index", str(index)))
    except click.ClickException:
        raise
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")

@click.command(name="create-data")
@click.argument("name", type=str)
def create_data_command(name):
    """Create data."""
    try:
        from CelebiChrono.interface.shell import mkdata
        result = mkdata(name)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="create-multi-data")
@click.argument(
    "path", type=click.Path(exists=True, file_okay=False, resolve_path=True)
)
def create_multi_data_command(path):
    """Create and upload one data object for each child directory in PATH.

    Each immediate child directory becomes a data object with the same name.
    Its contents are uploaded through the normal DITE data path.
    """
    try:
        from CelebiChrono.interface.shell import cd, mkdata, upload_data
        for name in sorted(os.listdir(path)):
            child = os.path.join(path, name)
            if not os.path.isdir(child):
                continue
            result = mkdata(name)
            _handle_result(result)
            if result is not None and not getattr(result, "success", True):
                continue
            cd(name)
            try:
                _handle_result(upload_data(child))
            finally:
                cd("..")
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")

@click.command(name="create-data-list")
@click.argument("name", type=str)
def create_data_list_command(name):
    """Create data list."""
    try:
        from CelebiChrono.interface.shell import mkdatalist
        result = mkdatalist(name)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")

@click.command(name="create-lhcb-ap-list")
@click.argument("name", type=str)
def create_lhcb_ap_list_command(name):
    """Create an LHCb AP data list.

    Creates a new lhcb_ap_datalist task with empty ap_config.
    Edit celebi.yaml to fill in the AP query parameters.
    """
    try:
        from CelebiChrono.interface.shell import create_lhcb_ap_list
        result = create_lhcb_ap_list(name)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")

@click.command(name="mkdir")
@click.argument("name", type=str)
def mkdir_command(name):
    """Create directory."""
    try:
        from CelebiChrono.interface.shell import mkdir
        result = mkdir(name)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="verify-data")
@click.option("--timeout", type=click.IntRange(min=1), default=None,
              help="HTTP request timeout in seconds (default: 3600); not a total job limit")
def verify_data_command(timeout: int = None) -> None:
    """Verify the current data task: recompute md5 vs registered uuid."""
    try:
        from CelebiChrono.interface.shell import verify_data
        _handle_result(verify_data(**({"timeout": timeout} if timeout is not None else {})))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="attach-data")
@click.argument("impression_uuid", type=str)
@click.option("--path", type=str, default=None, help="Optional task path override")
def attach_data_command(impression_uuid, path):
    """Attach a Yuki impression to a rawdata task in the current project."""
    try:
        from CelebiChrono.interface.shell import attach_data
        result = attach_data(impression_uuid, path or "")
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="register-ssh-data")
@click.argument("runner", type=str)
@click.argument("remote_path", type=str)
@click.option("--descriptor", type=str, default="",
              help="Task descriptor (defaults to remote path basename)")
@click.option("--timeout", type=click.IntRange(min=1), default=None,
              help="HTTP request timeout in seconds (default: 10); not a total job limit")
def register_ssh_data_command(runner: str, remote_path: str,
                              descriptor: str, timeout: int = None) -> None:
    """Register data living on an ssh runner (MD5 + managed staging).

    RUNNER is an ssh runner; REMOTE_PATH is a directory on that runner.
    The data is copied into Yuki's managed impressions area on the runner
    and registered as an impression; a local rawdata pointer task is
    created or filled.
    """
    try:
        from CelebiChrono.interface.shell import register_ssh_data
        _handle_result(register_ssh_data(
            runner, remote_path, descriptor,
            **({"timeout": timeout} if timeout is not None else {})))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")
