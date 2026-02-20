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
