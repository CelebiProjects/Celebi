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


@click.command(name="predecessors")
def predecessors_command() -> None:
    """List predecessors of current object."""
    try:
        from CelebiChrono.interface.shell import predecessors
        result = predecessors()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="gc-impressions")
@click.option("--grace-days", type=int, default=14, show_default=True)
@click.option("--dry-run/--execute", default=True, show_default=True)
def gc_impressions_command(grace_days: int, dry_run: bool) -> None:
    """Garbage collect unreachable CAS impression objects."""
    try:
        from CelebiChrono.interface.shell import gc_impressions
        result = gc_impressions(grace_days=grace_days, dry_run=dry_run)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="pack-impressions")
@click.option("--force/--no-force", default=False, show_default=True)
def pack_impressions_command(force: bool) -> None:
    """Evaluate packing thresholds for CAS impression objects."""
    try:
        from CelebiChrono.interface.shell import pack_impressions
        result = pack_impressions(force=force)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")
