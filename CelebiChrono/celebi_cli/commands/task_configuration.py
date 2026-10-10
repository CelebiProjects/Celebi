"""Task Configuration commands for Celebi CLI."""

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

@click.command(name="remove-input")
@click.argument("input_file", type=str)
def remove_input_command(input_file):
    """Remove input from task."""
    try:
        from CelebiChrono.interface.shell import remove_input
        result = remove_input(input_file)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


def _numbered_range(start: int, stop: int) -> range:
    """Validate and return a bounded half-open range for bulk commands."""
    count = stop - start
    if count <= 0 or count > 10000:
        raise click.BadParameter(
            "STOP must be greater than START and select at most 10000 items"
        )
    return range(start, stop)


@click.command(name="add-multi-inputs")
@click.argument("path_base", type=str)
@click.argument("alias_base", type=str)
@click.argument("stop", type=int)
@click.option("--start", type=int, default=0, show_default=True)
def add_multi_inputs_command(path_base, alias_base, stop, start):
    """Add a numbered range of task inputs and aliases.

    Adds PATH_BASE_N as ALIAS_BASE_N for every N in the half-open range
    START <= N < STOP. At most 10000 inputs may be added in one invocation.

    Example: add-multi-inputs ../sim/run input 10 --start 2
    """
    try:
        from CelebiChrono.interface.shell import add_input
        for index in _numbered_range(start, stop):
            result = add_input(
                f"{path_base}_{index}",
                f"{alias_base}_{index}",
            )
            _handle_result(result)
    except click.ClickException:
        raise
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="remove-multi-inputs")
@click.argument("alias_base", type=str)
@click.argument("stop", type=int)
@click.option("--start", type=int, default=0, show_default=True)
def remove_multi_inputs_command(alias_base, stop, start):
    """Remove a numbered range of input aliases.

    Removes ALIAS_BASE_N for every N in the half-open range START <= N < STOP.
    At most 10000 inputs may be removed in one invocation.

    Example: remove-multi-inputs input 10 --start 2
    """
    try:
        from CelebiChrono.interface.shell import remove_input
        for index in _numbered_range(start, stop):
            _handle_result(remove_input(f"{alias_base}_{index}"))
    except click.ClickException:
        raise
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

@click.command(name="set-parameter")
@click.argument("name", type=str)
@click.argument("value", type=str)
def add_parameter_command(name, value):
    """Set a parameter on the current task."""
    try:
        from CelebiChrono.interface.shell import add_parameter
        result = add_parameter(name, value)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")

@click.command(name="remove-parameter")
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
@click.argument("subtask", type=str)
@click.argument("name", type=str)
@click.argument("value", type=str)
def add_parameter_subtask_command(subtask, name, value):
    """Set a parameter on one subtask of the current directory."""
    try:
        from CelebiChrono.interface.shell import add_parameter_subtask
        result = add_parameter_subtask(subtask, name, value)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")

@click.command(name="set-environment")
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

@click.command(name="set-memory-limit")
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

@click.command(name="set-descriptor")
@click.argument("descriptor", type=str)
def set_descriptor_command(descriptor):
    """Set descriptor for task or algorithm."""
    try:
        from CelebiChrono.interface.shell import set_descriptor
        result = set_descriptor(descriptor)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="auto-download")
@click.argument("state", type=click.Choice(["on", "off"]))
def auto_download_command(state):
    """Enable or disable automatic result downloads for the current task.

    STATE is `on` or `off`. The setting applies to subsequent executions.
    """
    try:
        from CelebiChrono.interface.shell import MANAGER
        MANAGER.current_object().set_auto_download(state == "on")
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="cache-on-runner")
@click.argument("state", type=click.Choice(["on", "off"]))
def cache_on_runner_command(state):
    """Enable or disable retaining results in the runner cache.

    STATE is `on` or `off`. Retained results can later be inspected or
    transferred without an immediate local collection.
    """
    try:
        from CelebiChrono.interface.shell import MANAGER
        MANAGER.current_object().set_cache_on_runner(state == "on")
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

@click.command(name="add-apd-token")
@click.argument("token", type=str)
def add_apd_token_command(token):
    """Add an APD access token to the current LHCb AP data list task.

    Stores the token in .celebi/config.local.json and writes
    lbapi_key.json to the task directory for REANA submission.
    """
    try:
        from CelebiChrono.interface.shell import add_apd_token
        result = add_apd_token(token)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")

@click.command(name="user-config")
@click.option("--list", "-l", "list_only", is_flag=True,
              help="Show the settings in force without opening an editor.")
def user_config_command(list_only):
    """Create and edit the user configuration (~/.celebi/config.yaml).

    Creates the file from a documented template if it does not exist yet,
    then opens it in the configured editor. An existing file is never
    rewritten. Unlike `config`, which edits the current object's
    celebi.yaml, this edits your own user-level settings.
    """
    try:
        from CelebiChrono.interface.shell import user_config
        result = user_config(list_only=list_only)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")
