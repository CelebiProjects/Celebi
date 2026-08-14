"""Object Creation commands for Celebi CLI."""

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


@click.command(name="register-data")
@click.argument("runner", type=str)
@click.argument("remote_path", type=str)
@click.option("--descriptor", type=str, default="",
              help="Task descriptor (defaults to remote path basename)")
def register_data_command(runner: str, remote_path: str, descriptor: str) -> None:
    """Register data living on an ssh runner (MD5 + managed staging).

    RUNNER is an ssh runner; REMOTE_PATH is a directory on that runner.
    The data is copied into Yuki's managed impressions area on the runner
    and registered as an impression; a local rawdata pointer task is
    created or filled.
    """
    try:
        from CelebiChrono.interface.shell import register_data
        _handle_result(register_data(runner, remote_path, descriptor))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")
