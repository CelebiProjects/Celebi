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


@click.command(name="cat")
@click.argument("path", type=str)
def cat_command(path: str) -> None:
    """Print a text file from the current Celebi object.

    PATH is resolved relative to the current object. This is the one-shot
    equivalent of `cat` in the interactive Celebi shell.
    """
    try:
        from CelebiChrono.interface.shell import MANAGER
        MANAGER.current_object().cat(path)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="display")
@click.argument("filename", type=str)
def display_command(filename: str) -> None:
    """Open a result file from the current task in the default browser.

    FILENAME identifies a file belonging to the current impression. Its DITE
    display URL is opened using the operating system's configured browser.
    """
    try:
        from CelebiChrono.interface.shell import MANAGER
        MANAGER.current_object().display(filename)
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


@click.command(name="remove-file")
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


@click.command(name="move-file")
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


@click.command(name="workaround-vre")
@click.argument("pattern", required=False, default="*", type=str)
def workaround_vre_command(pattern: str) -> None:
    """Export matching results and create a Jupyter notebook to view them."""
    try:
        from CelebiChrono.interface.shell import workaround_vre
        _handle_result(workaround_vre(pattern))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="replace")
@click.argument("a", type=str)
@click.argument("b", type=str)
@click.option("--dry-run", is_flag=True, default=False,
              help="Print the planned changes without applying them.")
def replace_command(a: str, b: str, dry_run: bool) -> None:
    """Replace A with B in names, inputs, and aliases of the current folder."""
    try:
        from CelebiChrono.interface.shell import replace
        _handle_result(replace(a, b, dry_run=dry_run))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="upload-data")
@click.argument("path", type=str)
def upload_data_command(path: str) -> None:
    """Upload a local path's data to DITE (registers an impression on the server)."""
    try:
        from CelebiChrono.interface.shell import upload_data
        _handle_result(upload_data(path))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="add-input")
@click.argument("path", type=str)
@click.argument("alias", type=str)
def add_input_command(path: str, alias: str) -> None:
    """Add an input object at PATH under ALIAS."""
    try:
        from CelebiChrono.interface.shell import add_input
        _handle_result(add_input(path, alias))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="add-source")
@click.argument("path", type=str)
def add_source_command(path: str) -> None:
    """Add a source file or directory to current object."""
    try:
        from CelebiChrono.interface.shell import add_source
        result = add_source(path)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="transfer")
@click.argument("source", type=str)
@click.argument("destination", type=str)
@click.option("--pattern", type=str, default=None,
              help="Glob pattern to filter transferred files")
@click.option("--force", is_flag=True, default=False,
              help="Overwrite existing files at destination")
@click.option("--timeout", type=click.IntRange(min=1), default=None,
              help="HTTP request timeout in seconds (default: 10); not a total job limit")
def transfer_command(source: str, destination: str,
                     pattern: str = None, force: bool = False,
                     timeout: int = None) -> None:
    """Transfer stageout results between Yuki and runner cache.

    SOURCE and DESTINATION are 'yuki' or 'runner:<runner-id>'.
    """
    try:
        from CelebiChrono.interface.shell import transfer
        result = transfer(source, destination, pattern=pattern, force=force,
                          **({"timeout": timeout} if timeout is not None else {}))
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="export")
@click.argument("pattern", type=str, default="*", required=False)
def export_command(pattern: str) -> None:
    """Export matching result files to the project's export directory.

    PATTERN is a glob evaluated against the current task's results and
    defaults to all files.
    """
    try:
        from CelebiChrono.interface.shell import export
        _handle_result(export(pattern))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")
