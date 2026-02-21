"""Utility commands for Celebi CLI."""
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


@click.command(name="watermark")
def watermark_command() -> None:
    """Show watermark of current object."""
    try:
        from CelebiChrono.interface.shell import watermark
        result = watermark()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="doctor")
def doctor_command() -> None:
    """Run diagnostics on current object."""
    try:
        from CelebiChrono.interface.shell import doctor
        result = doctor()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="bookkeep")
def bookkeep_command() -> None:
    """Perform project-wide impression bookkeeping."""
    try:
        from CelebiChrono.interface.shell import bookkeep
        result = bookkeep()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="bookkeep-url")
def bookkeep_url_command() -> None:
    """Get the bookkeeping URL."""
    try:
        from CelebiChrono.interface.shell import bookkeep_url
        result = bookkeep_url()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="successors")
def successors_command() -> None:
    """List successors of current object."""
    try:
        from CelebiChrono.interface.shell import successors
        result = successors()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")
