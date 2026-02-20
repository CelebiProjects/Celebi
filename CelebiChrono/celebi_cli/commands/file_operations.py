"""File operations commands for Celebi CLI."""
import sys
from typing import Optional, Any, Tuple
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


@click.command(name="ls")
@click.argument("args", nargs=-1, type=str)
def ls_command(args: Tuple[str, ...]) -> None:
    """List directory contents."""
    try:
        from CelebiChrono.interface.shell import ls
        result = ls(*args)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="mv")
@click.argument("src", type=str)
@click.argument("dst", type=str)
def mv_command(src: str, dst: str) -> None:
    """Move file or directory."""
    try:
        from CelebiChrono.interface.shell import mv
        _handle_result(mv(src, dst))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="cp")
@click.argument("src", type=str)
@click.argument("dst", type=str)
def cp_command(src: str, dst: str) -> None:
    """Copy file or directory."""
    try:
        from CelebiChrono.interface.shell import cp
        _handle_result(cp(src, dst))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="rm")
@click.argument("path", type=str)
def rm_command(path: str) -> None:
    """Remove file or directory."""
    try:
        from CelebiChrono.interface.shell import rm
        _handle_result(rm(path))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="rmfile")
@click.argument("path", type=str)
def rmfile_command(path: str) -> None:
    """Remove file."""
    try:
        from CelebiChrono.interface.shell import rm_file
        _handle_result(rm_file(path))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="mvfile")
@click.argument("src", type=str)
@click.argument("dst", type=str)
def mvfile_command(src: str, dst: str) -> None:
    """Move file."""
    try:
        from CelebiChrono.interface.shell import mv_file
        _handle_result(mv_file(src, dst))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="import")
@click.argument("path", type=str)
def import_command(path: str) -> None:
    """Import file."""
    try:
        from CelebiChrono.interface.shell import import_file
        _handle_result(import_file(path))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="send")
@click.argument("path", type=str)
def send_command(path: str) -> None:
    """Send file."""
    try:
        from CelebiChrono.interface.shell import send
        _handle_result(send(path))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="add-input")
@click.argument("task", type=str)
@click.argument("input_file", type=str)
def add_input_command(task: str, input_file: str) -> None:
    """Add input to task."""
    try:
        from CelebiChrono.interface.shell import add_input
        _handle_result(add_input(task, input_file))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")
