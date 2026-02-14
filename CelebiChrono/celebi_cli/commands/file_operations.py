import click
import sys
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


@click.command(name="ls")
@click.argument("args", nargs=-1, type=str)
def ls_command(args):
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
def mv_command(src, dst):
    """Move file or directory."""
    try:
        from CelebiChrono.interface.shell import mv
        result = mv(src, dst)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="cp")
@click.argument("src", type=str)
@click.argument("dst", type=str)
def cp_command(src, dst):
    """Copy file or directory."""
    try:
        from CelebiChrono.interface.shell import cp
        result = cp(src, dst)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="rm")
@click.argument("path", type=str)
def rm_command(path):
    """Remove file or directory."""
    try:
        from CelebiChrono.interface.shell import rm
        result = rm(path)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="rmfile")
@click.argument("path", type=str)
def rmfile_command(path):
    """Remove file."""
    try:
        from CelebiChrono.interface.shell import rm_file
        result = rm_file(path)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="mvfile")
@click.argument("src", type=str)
@click.argument("dst", type=str)
def mvfile_command(src, dst):
    """Move file."""
    try:
        from CelebiChrono.interface.shell import mv_file
        result = mv_file(src, dst)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="import")
@click.argument("path", type=str)
def import_command(path):
    """Import file."""
    try:
        from CelebiChrono.interface.shell import import_file
        result = import_file(path)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="send")
@click.argument("path", type=str)
def send_command(path):
    """Send file."""
    try:
        from CelebiChrono.interface.shell import send
        result = send(path)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="add-input")
@click.argument("task", type=str)
@click.argument("input", type=str)
def add_input_command(task, input):
    """Add input to task."""
    try:
        from CelebiChrono.interface.shell import add_input
        result = add_input(task, input)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")