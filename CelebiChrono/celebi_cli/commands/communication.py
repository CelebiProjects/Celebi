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


@click.command(name="config")
def config_command():
    """Configure settings."""
    try:
        from CelebiChrono.interface.shell import config
        result = config()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="danger")
@click.argument("operation", type=str)
def danger_command(operation):
    """Execute dangerous operation."""
    try:
        from CelebiChrono.interface.shell import danger_call
        result = danger_call(operation)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="trace")
@click.argument("object", type=str)
def trace_command(object):
    """Trace object."""
    try:
        from CelebiChrono.interface.shell import trace
        result = trace(object)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="history")
def history_command():
    """Show history."""
    try:
        from CelebiChrono.interface.shell import history
        result = history()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="changes")
def changes_command():
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
def preshell_command():
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
def postshell_command(command):
    """Post-shell workaround."""
    try:
        from CelebiChrono.interface.shell import workaround_postshell
        result = workaround_postshell(command)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="impress")
def impress_command():
    """Show impression."""
    try:
        from CelebiChrono.interface.shell import impress
        result = impress()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")