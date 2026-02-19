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


@click.command(name="test")
def test_command():
    """
    Run a specified command inside a Docker container using the given image.
    """
    try:
        from CelebiChrono.interface.shell import test
        result = test()
        print(result)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")

@click.command(name="runners")
def runners_command():
    """List available runners."""
    try:
        from CelebiChrono.interface.shell import runners
        result = runners()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="register-runner")
@click.argument("arg1", type=str)
@click.argument("arg2", type=str)
@click.argument("arg3", type=str)
@click.argument("arg4", type=str)
def register_runner_command(arg1, arg2, arg3, arg4):
    """Register a new runner."""
    try:
        from CelebiChrono.interface.shell import register_runner
        result = register_runner(arg1, arg2, arg3, arg4)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="remove-runner")
@click.argument("runner", type=str)
def remove_runner_command(runner):
    """Remove a runner."""
    try:
        from CelebiChrono.interface.shell import remove_runner
        result = remove_runner(runner)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="submit")
@click.argument("task", type=str)
def submit_command(task):
    """Submit a task for execution."""
    try:
        from CelebiChrono.interface.shell import submit
        result = submit(task)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="collect")
@click.argument("task", type=str)
def collect_command(task):
    """Collect results from a task."""
    try:
        from CelebiChrono.interface.shell import collect
        result = collect(task)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="error-log")
@click.argument("task", type=str)
def error_log_command(task):
    """View error log for a task."""
    try:
        from CelebiChrono.interface.shell import error_log
        result = error_log(task)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="view")
@click.argument("object", type=str)
def view_command(object):
    """View an object."""
    try:
        from CelebiChrono.interface.shell import view
        result = view(object)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="edit")
@click.argument("script", type=str)
def edit_command(script):
    """Edit a script."""
    try:
        from CelebiChrono.interface.shell import edit_script
        result = edit_script(script)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")