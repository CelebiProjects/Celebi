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


@click.command(name="remove-input")
@click.argument("input", type=str)
def remove_input_command(input):
    """Remove input from task."""
    try:
        from CelebiChrono.interface.shell import remove_input
        result = remove_input(input)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="add-algorithm")
@click.argument("algorithm", type=str)
def add_algorithm_command(algorithm):
    """Add algorithm to task."""
    try:
        from CelebiChrono.interface.shell import add_algorithm
        result = add_algorithm(algorithm)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="add-parameter")
@click.argument("task", type=str)
@click.argument("parameter", type=str)
def add_parameter_command(task, parameter):
    """Add parameter to task."""
    try:
        from CelebiChrono.interface.shell import add_parameter
        result = add_parameter(task, parameter)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="rm-parameter")
@click.argument("parameter", type=str)
def rm_parameter_command(parameter):
    """Remove parameter from task."""
    try:
        from CelebiChrono.interface.shell import rm_parameter
        result = rm_parameter(parameter)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="add-parameter-subtask")
@click.argument("task", type=str)
@click.argument("parameter", type=str)
@click.argument("subtask", type=str)
def add_parameter_subtask_command(task, parameter, subtask):
    """Add parameter subtask to task."""
    try:
        from CelebiChrono.interface.shell import add_parameter_subtask
        result = add_parameter_subtask(task, parameter, subtask)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="set-env")
@click.argument("environment", type=str)
def set_env_command(environment):
    """Set environment for task."""
    try:
        from CelebiChrono.interface.shell import set_environment
        result = set_environment(environment)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="set-mem")
@click.argument("memory", type=str)
def set_mem_command(memory):
    """Set memory limit for task."""
    try:
        from CelebiChrono.interface.shell import set_memory_limit
        result = set_memory_limit(memory)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="add-host")
@click.argument("host", type=str)
@click.argument("port", type=str)
def add_host_command(host, port):
    """Add host for task execution."""
    try:
        from CelebiChrono.interface.shell import add_host
        result = add_host(host, port)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="hosts")
def hosts_command():
    """List available hosts."""
    try:
        from CelebiChrono.interface.shell import hosts
        result = hosts()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")