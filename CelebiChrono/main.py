"""
    main function
    The purpose is to start: Celebi

    Functions:
        cli:
            default entrance, to start chern command line
        ipython: [deprecated]
            start the ipython shell of chern
        * start_chern_ipython:
            function for cli:ipython
        * start_chern_command_line:
            function for default cli

        machine:
            start or stop the chernmachine

        config:
            set the configurations: inavailable yet
        prologue:
            print the prologue
"""

# pylint: disable=broad-exception-caught,import-outside-toplevel
import os
import logging
from os.path import join
from logging import getLogger

import click

from .kernel import vproject
from .utils import csys
from .utils import metadata
from .interface.ChernShell import ChernShell


def is_first_time():
    """ Check if it is the first time to use the software """
    return not os.path.exists(csys.local_config_dir())


def start_first_time():
    """ Start the first time """
    print("Starting the first time")
    print("Creating the config directory $HOME/.celebi")
    csys.mkdir(csys.local_config_dir())


def start_chern_command_line():
    """Start the Chern command line interface."""
    logger = getLogger("ChernLogger")
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)

    logger.debug("def start_chern_command_line")
    print("Welcome to the CELEBI Shell environment")
    print("Please type: 'helpme' to get more information")
    chern_shell = ChernShell()
    chern_shell.init()
    chern_shell.cmdloop()
    logger.debug("end start_chern_command_line")


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """ Chern command only is equal to `Chern ipython`
    """
    if is_first_time():
        start_first_time()
    if ctx.invoked_subcommand is None:
        try:
            config_file = metadata.ConfigFile(
                csys.local_config_dir() + "/config.json"
            )
            current_project = config_file.read_variable("current_project", "")
            print("Current project: ", current_project)
            if (
                current_project is None or current_project == "" or
                current_project not in config_file.read_variable(
                    "projects_path"
                ).keys()
            ):

                print("No project is selected as the current project")
                msg = "Please use ``chern workon PROJECT''' to select"
                print(msg + " a project")
                print("Please use ``chern projects'' to list all the projects")
            else:
                start_chern_command_line()
        except Exception as e:
            print(e)
            print("Chern shell ended")


@cli.command()
def config():
    """ Configure the software"""
    print("Configuration is not supported yet")


@cli.command()
def chern_command_line():
    """ Start Chern command line with cmd """
    try:
        start_chern_command_line()
    except Exception as e:
        print("Fail to start Chern command line:", e)


@cli.command()
def init():
    """ Add the current directory to project """
    try:
        vproject.init_project()
        start_chern_command_line()
    except Exception as e:
        print(e)
        print("Chern Shell Ended")


@cli.command()
@click.argument("path", type=str)
def use(path):
    """ Use a directory as the project"""
    try:
        vproject.use_project(path)
        start_chern_command_line()
    except Exception as e:
        print("Fail to start ipython:", e)


@cli.command()
def projects():
    """ List all the projects """
    try:
        config_path = csys.local_config_dir() + "/config.json"
        config_file = metadata.ConfigFile(config_path)
        projects_list = config_file.read_variable("projects_path")
        current_project = config_file.read_variable("current_project")
        for project in projects_list.keys():
            if project == current_project:
                print("*", project, ":", projects_list[project])
            else:
                print(project, ":", projects_list[project])
    except Exception as e:
        print("Fail to list all the projects:", e)


@cli.command()
@click.argument("project", type=str)
def workon(project):
    """ Switch to the project ``PROJECT' """
    try:
        config_file = metadata.ConfigFile(
            join(csys.local_config_dir(), "config.json")
        )
        projects_list = config_file.read_variable("projects_path")
        if project in projects_list.keys():
            config_file.write_variable("current_project", project)
            print("Switch to project: ", project)
        else:
            print(f"Project ``{project}'' not found")
    except Exception as e:
        print("Fail to switch to the project:", e)


@cli.command()
@click.argument("project", type=str)
def remove(project):
    """ Remove the project ``PROJECT' """
    try:
        config_file = metadata.ConfigFile(
            join(csys.local_config_dir, "config.json")
        )
        projects_list = config_file.read_variable("projects_path")
        current_project = config_file.read_variable("current_project")
        if project == current_project:
            config_file.write_variable("current_project", "")

        if project in projects_list:
            projects_list.pop(project)
            config_file.write_variable("projects_path", projects_list)
            print("Remove project: ", project)
        else:
            print(f"Project ``{project}'' not found")
    except Exception:
        print("Fail to remove the project")


@cli.command()
def prologue():
    """ A prologue from the author """
    print("""
    Celebi: A data analysis management toolkit
    Author: Mingrui Zhao
            2013 - 2017
          @ Center of High Energy Physics, Tsinghua University
            2017 - 2025
          @ Department of Nuclear Physics, China Institute of Atomic Energy
            2020 - 2024
          @ Niels Bohr Institute, Copenhagen University
            2025 - now
          @ Peking University
    Email: mingrui.zhao@mail.labz0.org


    """)


@click.group()
def cli_sh():
    """ celebi command line command
    """

# Dynamic shell command registration

def _get_command_description(func_name: str, fallback_desc: str) -> str:
    """Extract short command description from function docstring.

    Attempts to import the shell module and extract the docstring from the
    given function name. Returns a cleaned version of the docstring (first
    sentence or paragraph), or the fallback description if extraction fails
    or produces an unsatisfactory result.

    Args:
        func_name: Name of the function in the shell module
        fallback_desc: Fallback description to use if extraction fails

    Returns:
        Extracted short description or fallback
    """
    try:
        from .interface import shell
        func = getattr(shell, func_name, None)
        if func is None:
            return fallback_desc

        docstring = func.__doc__
        if not docstring:
            return fallback_desc

        # Clean the docstring: get first paragraph
        lines = docstring.strip().split('\n')
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in lines]
        # Join and get first sentence (up to period or end of first paragraph)
        clean_doc = ' '.join(lines)
        # Split into sentences, take first
        sentences = clean_doc.split('. ')
        if sentences:
            first_sentence = sentences[0]
            # Add period if not present
            if not first_sentence.endswith('.'):
                first_sentence += '.'
            # Ensure it's not too short (minimum 10 chars) and not just a single word
            if len(first_sentence) > 20 and ' ' in first_sentence:
                return first_sentence

        # If first sentence extraction failed, use the whole cleaned docstring
        # but limit length for Click help
        if len(clean_doc) > 20 and ' ' in clean_doc:
            # Truncate if too long for Click help
            if len(clean_doc) > 200:
                return clean_doc[:197] + '...'
            return clean_doc

    except Exception:
        # Catch any exception during import or processing
        # Fall back to the hardcoded description
        pass

    return fallback_desc


def _get_command_docstring(func_name: str) -> str:
    """Get full docstring from shell function.

    Args:
        func_name: Name of the function in the shell module

    Returns:
        Full docstring or empty string if not available
    """
    import sys
    try:
        from .interface import shell
        func = getattr(shell, func_name, None)
        if func is None:
            # print(f"DEBUG: Function {func_name} not found in shell module", file=sys.stderr)
            return ""

        docstring = func.__doc__
        if not docstring:
            return ""

        # Split docstring into lines and skip the first line
        lines = docstring.splitlines()
        if len(lines) <= 1:
            # Single line or empty after first line
            return ""

        # Skip the first line
        remaining_lines = lines[1:]

        # Remove leading empty lines
        while remaining_lines and not remaining_lines[0].strip():
            remaining_lines.pop(0)

        # If nothing left after removing empty lines, return empty string
        if not remaining_lines:
            return ""

        # Rejoin the remaining lines
        result = "\n".join(remaining_lines)

        # Dedent the result to remove common leading whitespace
        import textwrap
        result = textwrap.dedent(result)

        # print(f"DEBUG: Retrieved docstring for {func_name}, length: {len(result)}", file=sys.stderr)
        # if result: print(f"DEBUG: First 100 chars: {result[:100]}", file=sys.stderr)
        return result
    except Exception as e:
        # print(f"DEBUG: Error getting docstring for {func_name}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return ""


_shell_commands = [
    ('ls', 'ls', 999, 'List the contents of a Celebi object. Without a path, lists the current object; with a path, lists the specified object within the current project.'),
    ('tree', 'tree', 0, 'Show tree view'),
    ('status', 'status', 0, 'Show status'),
    ('cd', 'cd', 1, 'Change directory within project'),
    ('mv', 'mv', 2, 'Move object'),
    ('cp', 'cp', 2, 'Copy object'),
    ('rm', 'rm', 1, 'Remove object'),
    ('short-ls', 'short_ls', -1, 'Short listing'),
    ('jobs', 'jobs', -1, 'Show jobs'),
    ('create-algorithm', 'mkalgorithm', 1, 'Create algorithm'),
    ('create-task', 'mktask', 1, 'Create task'),
    ('create-data', 'mkdata', 1, 'Create data object'),
    ('mkdir', 'mkdir', 1, 'Create directory'),
    ('rmfile', 'rm_file', 1, 'Remove file'),
    ('mvfile', 'mv_file', 2, 'Move file'),
    ('import', 'import_file', 1, 'Import file'),
    ('add-input', 'add_input', 2, 'Add input to task'),
    ('remove-input', 'remove_input', 1, 'Remove input'),
    ('add-algorithm', 'add_algorithm', 1, 'Add algorithm to task'),
    ('add-parameter', 'add_parameter', 2, 'Add parameter'),
    ('rm-parameter', 'rm_parameter', 1, 'Remove parameter'),
    ('add-parameter-subtask', 'add_parameter_subtask', 3, 'Add parameter subtask'),
    ('set-env', 'set_environment', 1, 'Set environment'),
    ('set-mem', 'set_memory_limit', 1, 'Set memory limit'),
    ('hosts', 'hosts', 0, 'List hosts'),
    ('add-host', 'add_host', 2, 'Add host'),
    ('runners', 'runners', 0, 'List runners'),
    ('register-runner', 'register_runner', 4, 'Register runner'),
    ('remove-runner', 'remove_runner', 1, 'Remove runner'),
    ('send', 'send', 1, 'Send data'),
    ('submit', 'submit', 1, 'Submit task'),
    ('collect', 'collect', 1, 'Collect task outputs (all, outputs, logs)'),
    ('error-log', 'error_log', 1, 'Show error log'),
    ('view', 'view', 1, 'View in browser'),
    ('edit', 'edit_script', 1, 'Edit script'),
    ('config', 'config', 0, 'Show configuration'),
    ('danger', 'danger_call', 1, 'Dangerous operation'),
    ('trace', 'trace', 1, 'Trace dependencies'),
    ('history', 'history', 0, 'Show history'),
    ('changes', 'changes', 0, 'Show changes'),
    ('preshell', 'workaround_preshell', 0, 'Pre-shell workaround'),
    ('postshell', 'workaround_postshell', 1, 'Post-shell workaround'),
    ('impress', 'impress', 0, 'Create impression'),
    ('navigate', 'navigate', 0, 'Change to current project directory'),
    ('cdproject', 'shell_cd_project', 1, 'Change to project directory'),
]

for cmd_name, func_name, arg_count, description in _shell_commands:
    # Create a closure to capture variables
    def make_command(cname, fname, expected_args, desc=''):
        # Define the command function dynamically with error handling
        if expected_args == -1:
            # Define function first
            def command_func():
                import sys
                try:
                    from CelebiChrono.interface import shell
                    func = getattr(shell, fname)
                    result = func("")
                    if result is not None:
                        if hasattr(result, 'colored'):
                            print(result.colored())
                        else:
                            print(result)
                except ImportError as e:
                    print(f'Error importing CelebiChrono module: {e}', file=sys.stderr)
                    print('Make sure CelebiChrono is installed and in PYTHONPATH', file=sys.stderr)
                    sys.exit(1)
                except Exception as e:
                    print(f'Error executing Celebi command: {e}', file=sys.stderr)
                    sys.exit(1)

            # Get full docstring for detailed help
            full_doc = _get_command_docstring(fname)
            if not full_doc:
                full_doc = desc  # Fallback to short description

            # Apply command decorator with both short and full help
            command_func = cli_sh.command(name=cname, short_help=desc, help=full_doc)(command_func)
        elif expected_args == 0:
            # Define function first
            def command_func():
                import sys
                try:
                    from CelebiChrono.interface import shell
                    func = getattr(shell, fname)
                    result = func()
                    if result is not None:
                        if hasattr(result, 'colored'):
                            print(result.colored())
                        else:
                            print(result)
                except ImportError as e:
                    print(f'Error importing CelebiChrono module: {e}', file=sys.stderr)
                    print('Make sure CelebiChrono is installed and in PYTHONPATH', file=sys.stderr)
                    sys.exit(1)
                except Exception as e:
                    print(f'Error executing Celebi command: {e}', file=sys.stderr)
                    sys.exit(1)

            # Get full docstring for detailed help
            full_doc = _get_command_docstring(fname)
            if not full_doc:
                full_doc = desc  # Fallback to short description

            # Apply command decorator with both short and full help
            command_func = cli_sh.command(name=cname, short_help=desc, help=full_doc)(command_func)
        elif expected_args == 1:
            # Define function first
            def command_func(arg1):
                import sys
                try:
                    from CelebiChrono.interface import shell
                    func = getattr(shell, fname)
                    result = func(arg1)
                    if result is not None:
                        if hasattr(result, 'colored'):
                            print(result.colored())
                        else:
                            print(result)
                except ImportError as e:
                    print(f'Error importing CelebiChrono module: {e}', file=sys.stderr)
                    print('Make sure CelebiChrono is installed and in PYTHONPATH', file=sys.stderr)
                    sys.exit(1)
                except Exception as e:
                    print(f'Error executing Celebi command: {e}', file=sys.stderr)
                    sys.exit(1)

            # Apply argument decorator first
            command_func = click.argument('arg1', type=str)(command_func)

            # Get full docstring for detailed help
            full_doc = _get_command_docstring(fname)
            if not full_doc:
                full_doc = desc  # Fallback to short description

            # Apply command decorator with both short and full help
            command_func = cli_sh.command(name=cname, short_help=desc, help=full_doc)(command_func)
        elif expected_args == 2:
            # Define function first
            def command_func(arg1, arg2):
                import sys
                try:
                    from CelebiChrono.interface import shell
                    func = getattr(shell, fname)
                    result = func(arg1, arg2)
                    if result is not None:
                        if hasattr(result, 'colored'):
                            print(result.colored())
                        else:
                            print(result)
                except ImportError as e:
                    print(f'Error importing CelebiChrono module: {e}', file=sys.stderr)
                    print('Make sure CelebiChrono is installed and in PYTHONPATH', file=sys.stderr)
                    sys.exit(1)
                except Exception as e:
                    print(f'Error executing Celebi command: {e}', file=sys.stderr)
                    sys.exit(1)

            # Get full docstring for detailed help
            full_doc = _get_command_docstring(fname)
            if not full_doc:
                full_doc = desc  # Fallback to short description

            # Apply argument decorators
            command_func = click.argument('arg2', type=str)(command_func)
            command_func = click.argument('arg1', type=str)(command_func)

            # Apply command decorator with both short and full help
            command_func = cli_sh.command(name=cname, short_help=desc, help=full_doc)(command_func)
        elif expected_args == 3:
            # Define function first
            def command_func(arg1, arg2, arg3):
                import sys
                try:
                    from CelebiChrono.interface import shell
                    func = getattr(shell, fname)
                    result = func(arg1, arg2, arg3)
                    if result is not None:
                        if hasattr(result, 'colored'):
                            print(result.colored())
                        else:
                            print(result)
                except ImportError as e:
                    print(f'Error importing CelebiChrono module: {e}', file=sys.stderr)
                    print('Make sure CelebiChrono is installed and in PYTHONPATH', file=sys.stderr)
                    sys.exit(1)
                except Exception as e:
                    print(f'Error executing Celebi command: {e}', file=sys.stderr)
                    sys.exit(1)

            # Set docstring from shell function
            full_doc = _get_command_docstring(fname)
            if full_doc:
                command_func.__doc__ = full_doc

            # Apply argument decorators, then command decorator
            command_func = click.argument('arg3', type=str)(command_func)
            command_func = click.argument('arg2', type=str)(command_func)
            command_func = click.argument('arg1', type=str)(command_func)
            command_func = cli_sh.command(name=cname, help=desc)(command_func)
        elif expected_args == 4:
            # Define function first
            def command_func(arg1, arg2, arg3, arg4):
                import sys
                try:
                    from CelebiChrono.interface import shell
                    func = getattr(shell, fname)
                    result = func(arg1, arg2, arg3, arg4)
                    if result is not None:
                        if hasattr(result, 'colored'):
                            print(result.colored())
                        else:
                            print(result)
                except ImportError as e:
                    print(f'Error importing CelebiChrono module: {e}', file=sys.stderr)
                    print('Make sure CelebiChrono is installed and in PYTHONPATH', file=sys.stderr)
                    sys.exit(1)
                except Exception as e:
                    print(f'Error executing Celebi command: {e}', file=sys.stderr)
                    sys.exit(1)

            # Set docstring from shell function
            full_doc = _get_command_docstring(fname)
            if full_doc:
                command_func.__doc__ = full_doc

            # Apply argument decorators, then command decorator
            command_func = click.argument('arg4', type=str)(command_func)
            command_func = click.argument('arg3', type=str)(command_func)
            command_func = click.argument('arg2', type=str)(command_func)
            command_func = click.argument('arg1', type=str)(command_func)
            command_func = cli_sh.command(name=cname, help=desc)(command_func)
        else:
            # Fallback: use variable arguments
            # Define function first
            def command_func(args):
                import sys
                try:
                    from CelebiChrono.interface import shell
                    func = getattr(shell, fname)
                    result = func(*args)
                    if result is not None:
                        if hasattr(result, 'colored'):
                            print(result.colored())
                        else:
                            print(result)
                except ImportError as e:
                    print(f'Error importing CelebiChrono module: {e}', file=sys.stderr)
                    print('Make sure CelebiChrono is installed and in PYTHONPATH', file=sys.stderr)
                    sys.exit(1)
                except Exception as e:
                    print(f'Error executing Celebi command: {e}', file=sys.stderr)
                    sys.exit(1)

            # Set docstring from shell function
            full_doc = _get_command_docstring(fname)
            if full_doc:
                command_func.__doc__ = full_doc

            # Apply argument decorator, then command decorator
            command_func = click.argument('args', nargs=-1, type=str)(command_func)
            command_func = cli_sh.command(name=cname, help=desc)(command_func)
        # Rename function to avoid duplication
        command_func.__name__ = f'{cname}_command'
        return command_func
    # Get description from docstring or use fallback
    extracted_desc = _get_command_description(func_name, description)
    command = make_command(cmd_name, func_name, arg_count, extracted_desc)
    # Keep reference to avoid garbage collection
    globals()[f'{cmd_name}_command'] = command

@cli_sh.command()
@click.argument("project", type=str)
def cd_project(project):
    """Switch to the project ``PROJECT'."""
    from CelebiChrono.interface import shell
    shell.cd_project(project)


def sh():
    """Entry point for shell commands."""
    cli_sh()


def main():
    """Main entry point for the Celebi CLI."""
    cli()  # pylint: disable=no-value-for-parameter
