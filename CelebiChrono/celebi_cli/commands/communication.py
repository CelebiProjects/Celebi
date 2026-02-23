"""Communication commands for Celebi CLI."""
import sys
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


@click.command(name="config")
def config_command() -> None:
    """Configure settings."""
    try:
        from CelebiChrono.interface.shell import config
        _handle_result(config())
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="danger")
@click.argument("operation", type=str)
def danger_command(operation: str) -> None:
    """Execute dangerous operation."""
    try:
        from CelebiChrono.interface.shell import danger_call
        _handle_result(danger_call(operation))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="trace")
@click.argument("obj", type=str)
def trace_command(obj: str) -> None:
    """Trace object to its source impression and show DAG differences.

    Compares the current dependency DAG with the DAG stored in the impression
    and displays differences in human-readable format:

    - Short UUIDs (7 characters) with type prefixes: [TASK], [ALGO], [DATA], [PROJ]
    - Bulleted lists for added/removed nodes and edges
    - Formatted as "parent → child" for edge relationships
    - Detailed file and edge change information

    Args:
        obj: UUID or identifier of the impression to trace.

    Examples:
        celebi trace abc123-def456-ghi789
        celebi trace impression_2024_01_15
    """
    try:
        from CelebiChrono.interface.shell import trace
        _handle_result(trace(obj))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="history")
def history_command() -> None:
    """Show history."""
    try:
        from CelebiChrono.interface.shell import history
        _handle_result(history())
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="changes")
def changes_command() -> None:
    """Show changes."""
    try:
        from CelebiChrono.interface.shell import changes
        result = changes()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="preshell")
def preshell_command() -> None:
    """Pre-shell workaround."""
    try:
        from CelebiChrono.interface.shell import workaround_preshell
        result = workaround_preshell()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="postshell")
@click.argument("command", type=str)
def postshell_command(command: str) -> None:
    """Post-shell workaround."""
    try:
        from CelebiChrono.interface.shell import workaround_postshell
        _handle_result(workaround_postshell(command))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="impress")
def impress_command() -> None:
    """Show impression."""
    try:
        from CelebiChrono.interface.shell import impress
        result = impress()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="dite")
def dite_command() -> None:
    """Show DITE information."""
    try:
        from CelebiChrono.interface.shell import dite
        result = dite()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="set-dite")
@click.argument("url", type=str)
def set_dite_command(url: str) -> None:
    """Set DITE connection URL."""
    try:
        from CelebiChrono.interface.shell import set_dite
        result = set_dite(url)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="request-runner")
@click.argument("runner", type=str)
def request_runner_command(runner: str) -> None:
    """Request a runner for current task."""
    try:
        from CelebiChrono.interface.shell import request_runner
        result = request_runner(runner)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="search-impression")
@click.argument("partial_uuid", type=str)
def search_impression_command(partial_uuid: str) -> None:
    """Search impressions by partial UUID."""
    try:
        from CelebiChrono.interface.shell import search_impression
        result = search_impression(partial_uuid)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")
