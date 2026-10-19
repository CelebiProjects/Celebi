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

# pylint: disable=broad-exception-caught
import os
import inspect
import copy
from os.path import join
from logging import getLogger

import click

from .kernel import vproject
from .interface.shell_modules.reana_booking import book_reana
from .utils import csys
from .utils import metadata
from .utils.debug_logging import setup_logging
from .interface.ChernShell import ChernShell
from .celebi_cli.commands.object_creation import attach_data_command


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
    setup_logging()
    logger = getLogger("ChernLogger")

    logger.debug("def start_chern_command_line")
    print("Welcome to the CELEBI Shell environment")
    print("Please type: 'helpme' to get more information")
    chern_shell = ChernShell()
    chern_shell.init()
    chern_shell.cmdloop()
    logger.debug("end start_chern_command_line")


def _get_command_docstring(func_name: str) -> str:
    """Get long description from shell function (docstring without first line).

    Args:
        func_name: Name of the function in the shell module

    Returns:
        Docstring without first line, or empty string if not available
    """
    try:
        from .interface import shell
        func = getattr(shell, func_name, None)
        if func is None:
            return ""

        docstring = inspect.cleandoc(func.__doc__ or "")
        if not docstring:
            return ""

        lines = docstring.split('\n')
        if len(lines) > 1:
            remaining_lines = lines[1:]
            while remaining_lines and not remaining_lines[0].strip():
                remaining_lines.pop(0)

            if remaining_lines:
                return '\n'.join(remaining_lines).strip()

        return ""
    except Exception:
        return ""


# Expected command registration pattern for help system tests:
# command_func = cli_sh.command(name=cname, short_help=desc, help=full_doc)(command_func)


class ShellEntryGroup(click.Group):
    """Keep legacy subcommands callable without advertising them as the API."""

    def format_usage(self, ctx, formatter):
        formatter.write_usage(ctx.command_path, "[OPTIONS]")


@click.group(cls=ShellEntryGroup, invoke_without_command=True)
@click.option("--debug", is_flag=True, default=False,
              help="Enable verbose logging in ~/.celebi/logs/celebi.log")
@click.option("--project", "--workon", "workon_project", type=str, default=None,
              help="Open PROJECT in the interactive Celebi shell.")
@click.pass_context
def cli(ctx, debug, workon_project):
    """Start the interactive Celebi shell."""
    if is_first_time():
        start_first_time()
    setup_logging(debug=debug)
    if ctx.invoked_subcommand is None:
        try:
            config_file = metadata.ConfigFile(
                csys.local_config_dir() + "/config.json"
            )

            # If --project is specified, switch project first.
            if workon_project:
                projects_list = config_file.read_variable("projects_path")
                if workon_project in projects_list:
                    config_file.write_variable("current_project", workon_project)
                    print("Switch to project:", workon_project)
                else:
                    print(f"Project '{workon_project}' not found")
                    return

            current_project = config_file.read_variable("current_project", "")
            print("Current project: ", current_project)
            if (
                not current_project or
                current_project not in config_file.read_variable(
                    "projects_path"
                ).keys()
            ):

                print("No project is selected as the current project")
                print("Use `celebi-cli use-project PROJECT` to select a project")
                print("Use `celebi-cli list-projects` to list registered projects")
            else:
                start_chern_command_line()
        except Exception as e:
            print(e)
            print("Celebi shell ended")


@cli.command(hidden=True)
def config():
    """ Configure the software"""
    print("Use `celebi-cli user-config` to edit your user settings")
    print("(~/.celebi/config.yaml), or `celebi-cli user-config --list`")
    print("to see the settings in force.")


@cli.command(hidden=True)
def chern_command_line():
    """ Start Chern command line with cmd """
    try:
        start_chern_command_line()
    except Exception as e:
        print("Fail to start Chern command line:", e)


@cli.command(hidden=True)
def init():
    """ Add the current directory to project """
    try:
        vproject.init_project()
        start_chern_command_line()
    except Exception as e:
        print(e)
        print("Chern Shell Ended")


@cli.command(hidden=True)
@click.argument("path", type=str)
@click.option(
    "--new-project",
    is_flag=True,
    help="Assign the registered project a newly generated UUID.",
)
def use(path, new_project):
    """Use a directory as the project."""
    try:
        vproject.use_project(path, new_project=new_project)
        start_chern_command_line()
    except Exception as e:
        print("Fail to start ipython:", e)


@cli.command(hidden=True)
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


@cli.command(hidden=True)
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


@cli.command(hidden=True)
@click.argument("project", type=str)
def remove(project):
    """ Remove the project ``PROJECT' """
    try:
        config_file = metadata.ConfigFile(
            join(csys.local_config_dir(), "config.json")
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

@cli.command(name="project-uuid", hidden=True)
def project_uuid_command():
    """Print the current project's UUID."""
    project_path = csys.project_path(os.getcwd())
    if not project_path:
        print("Error: Not inside a Celebi project.")
        return
    uuid = vproject.VProject(project_path).project_uuid()
    print(uuid)


@cli.command(hidden=True)
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

# ----------------------------------------------------------------------
# Git Integration Commands
# ----------------------------------------------------------------------

@click.group()
@click.option("--debug", is_flag=True, default=False,
              help="Enable verbose logging in ~/.celebi/logs/celebi.log")
def git_cli(debug):
    """Celebi git integration commands."""
    setup_logging(debug=debug)


@git_cli.command(name="merge")
@click.argument("branch", type=str)
@click.option(
    "--strategy",
    "-s",
    type=click.Choice(["interactive", "auto", "local", "remote", "union"]),
    default="interactive",
    help="Merge strategy to use",
)
@click.option("--dry-run", "-n", is_flag=True, help="Simulate merge without making changes")
def git_merge(branch, strategy, dry_run):
    """Merge a git branch with Celebi validation and impression regeneration."""
    try:
        from .utils.git_merge_coordinator import GitMergeCoordinator, MergeStrategy

        # Map string to enum
        strategy_map = {
            "interactive": MergeStrategy.INTERACTIVE,
            "auto": MergeStrategy.AUTO,
            "local": MergeStrategy.LOCAL,
            "remote": MergeStrategy.REMOTE,
            "union": MergeStrategy.UNION
        }

        merge_strategy = strategy_map.get(strategy, MergeStrategy.INTERACTIVE)

        coordinator = GitMergeCoordinator()
        results = coordinator.execute_merge(branch, merge_strategy, dry_run)

        if dry_run:
            print("\nDRY RUN - No changes were made")

        if results['success']:
            print(f"\n✓ Merge completed successfully from {branch}")

            if results.get('git_conflicts'):
                print(f"  Git conflicts resolved: {len(results['git_conflicts'])}")

            if results.get('validation_conflicts'):
                print(f"  Celebi conflicts resolved: {len(results['validation_conflicts'])}")

            if results.get('regeneration_stats'):
                stats = results['regeneration_stats']
                print(f"  Impressions regenerated: {stats.get('regenerated', 0)}")

        else:
            print("\n✗ Merge failed")

            if results.get('errors'):
                print("  Errors:")
                for error in results['errors']:
                    print(f"    - {error}")

            if results.get('warnings'):
                print("  Warnings:")
                for warning in results['warnings']:
                    print(f"    - {warning}")

            if results.get('conflicts'):
                print(f"  Unresolved conflicts: {len(results['conflicts'])}")

    except Exception as e:
        print(f"Error during git merge: {e}")
        import traceback
        traceback.print_exc()

@git_cli.command(name="validate")
def git_validate():
    """Validate Celebi project state after git operations."""
    try:
        from .utils.git_merge_coordinator import GitMergeCoordinator

        coordinator = GitMergeCoordinator()
        results = coordinator.validate_post_merge()

        if results['success']:
            print("✓ Project validation successful")

            if results.get('repairs'):
                print("  Automatic repairs performed:")
                for repair in results['repairs']:
                    print(f"    - {repair}")
        else:
            print("✗ Project validation failed")

            if results.get('issues'):
                print("  Issues found:")
                for issue in results['issues']:
                    print(f"    - {issue}")

            if results.get('repairs'):
                print("  Attempted repairs:")
                for repair in results['repairs']:
                    print(f"    - {repair}")

    except Exception as e:
        print(f"Error during validation: {e}")

@git_cli.command(name="status")
def git_status():
    """Show git integration status and merge readiness."""
    try:
        from .utils.git_optional import GitOptionalIntegration

        git_integration = GitOptionalIntegration()
        git_info = git_integration.get_git_info()
        git_config_data = git_integration.get_config()

        print("Git Integration Status")
        print("=" * 80)

        # Git repository info
        if git_info['is_git_repo']:
            print("✓ Git repository detected")
            print(
                f"  Current branch: {git_info.get('current_branch', 'unknown')}"
            )
            print(f"  Remote: {git_info.get('remote_url', 'none')}")
            print(
                "  Uncommitted changes: "
                f"{'yes' if git_info['has_uncommitted_changes'] else 'no'}"
            )
        else:
            print("✗ Not a git repository")
            print("  Run 'git init' to initialize git in this directory")
            return

        # Integration status
        print(
            "\nCelebi Git Integration: "
            f"{'ENABLED' if git_config_data['enabled'] else 'DISABLED'}"
        )
        print(
            f"  Hooks installed: {'yes' if git_config_data['hooks_installed'] else 'no'}"
        )
        print(
            f"  Auto-validate: {'yes' if git_config_data['auto_validate'] else 'no'}"
        )
        print(
            f"  Auto-regenerate: {'yes' if git_config_data['auto_regenerate'] else 'no'}"
        )
        print(f"  Merge strategy: {git_config_data['merge_strategy']}")

        # Merge readiness
        from .utils.git_merge_coordinator import GitMergeCoordinator
        coordinator = GitMergeCoordinator()
        merge_status = coordinator.get_merge_status()

        print(f"\nMerge Readiness: {'READY' if merge_status['ready_to_merge'] else 'NOT READY'}")
        if merge_status['has_uncommitted_changes']:
            print("  ⚠ Uncommitted changes detected")
        if merge_status['merge_in_progress']:
            print("  ⚠ Merge already in progress")

        # Potential issues
        issues = git_integration.detect_potential_issues()
        if issues:
            print(f"\nPotential Issues ({len(issues)}):")
            for issue in issues:
                level = issue['level']
                message = issue['message']
                if level == 'error':
                    print(f"  ✗ {message}")
                else:
                    print(f"  ⚠ {message}")

                if 'suggestion' in issue:
                    print(f"     Suggestion: {issue['suggestion']}")

    except Exception as e:
        print(f"Error getting git status: {e}")

@git_cli.command(name="enable")
def git_enable():
    """Enable Celebi git integration for current project."""
    try:
        from .utils.git_optional import GitOptionalIntegration

        git_integration = GitOptionalIntegration()

        if not git_integration.is_git_repository():
            print("Error: Not a git repository")
            print("Run 'git init' first to initialize git")
            return

        if git_integration.enable_integration():
            print("✓ Git integration enabled")
            gitignore_created = git_integration.create_gitignore_if_missing()
            if gitignore_created:
                print("✓ Created .gitignore with recommended Celebi rules")

            # Offer to install hooks
            choice = input("Install git hooks for automatic validation? [Y/n]: ").strip().lower()
            if choice in ['', 'y', 'yes']:
                if git_integration.install_hooks():
                    print("✓ Git hooks installed")
                else:
                    print("⚠ Failed to install git hooks")

            if not gitignore_created:
                recommendations = git_integration.get_recommended_settings()
                print("\nRecommended settings:")
                print("  Add to .gitignore:")
                for line in recommendations['.gitignore_additions']:
                    print(f"    {line}")

        else:
            print("✗ Failed to enable git integration")

    except Exception as e:
        print(f"Error enabling git integration: {e}")

@git_cli.command(name="disable")
def git_disable():
    """Disable Celebi git integration for current project."""
    try:
        from .utils.git_optional import GitOptionalIntegration

        git_integration = GitOptionalIntegration()

        if git_integration.disable_integration():
            print("✓ Git integration disabled")
            print("  Hooks removed if installed")
            print("  Auto-validation disabled")
        else:
            print("✗ Failed to disable git integration")

    except Exception as e:
        print(f"Error disabling git integration: {e}")

@git_cli.command(name="hooks")
@click.option("--install/--uninstall", default=True, help="Install or uninstall git hooks")
def git_hooks(install):
    """Install or uninstall Celebi git hooks."""
    try:
        from .utils.git_optional import GitOptionalIntegration

        git_integration = GitOptionalIntegration()

        if not git_integration.is_git_repository():
            print("Error: Not a git repository")
            return

        if install:
            if git_integration.install_hooks():
                print("✓ Git hooks installed")
                print("  Post-merge hook will validate Celebi state after git merges")
            else:
                print("✗ Failed to install git hooks")
        else:
            if git_integration.uninstall_hooks():
                print("✓ Git hooks uninstalled")
            else:
                print("✗ Failed to uninstall git hooks")

    except Exception as e:
        print(f"Error managing git hooks: {e}")

@git_cli.command(name="config")
@click.argument("key", type=str)
@click.argument("value", type=str)
def git_config(key, value):
    """Set git integration configuration option."""
    try:
        from .utils.git_optional import GitOptionalIntegration

        git_integration = GitOptionalIntegration()

        # Convert value to appropriate type
        if value.lower() in ['true', 'yes', 'on', '1']:
            value = True
        elif value.lower() in ['false', 'no', 'off', '0']:
            value = False
        elif value.isdigit():
            value = int(value)

        if git_integration.set_config_option(key, value):
            print(f"✓ Configuration updated: {key} = {value}")
        else:
            print(f"✗ Invalid configuration key: {key}")
            print(
                "  Valid keys: enabled, auto_validate, auto_regenerate, "
                "prefer_local, merge_strategy"
            )

    except Exception as e:
        print(f"Error setting configuration: {e}")

_legacy_attach_data_command = copy.copy(attach_data_command)
_legacy_attach_data_command.hidden = True
cli.add_command(_legacy_attach_data_command)


@cli.command(name="booking-server", hidden=True)
def booking_server_command():
    """Check the registered booking server URL and status."""
    try:
        from .interface.shell_modules.reana_booking import check_booking_server

        result = check_booking_server()
        if result.messages:
            print(result.colored())
    except Exception as e:
        print(f"Error: {e}")


@cli.command(name="register-booking-server", hidden=True)
@click.option("--server", "server_url", default="",
              help="REANA server URL (or set REANA_SERVER_URL env var)")
@click.option("--token", "access_token", default="",
              help="REANA access token (or set REANA_ACCESS_TOKEN env var)")
def register_booking_server_command(server_url, access_token):
    """Register REANA server and token with Yuki for booking.

    Stores the credentials in Yuki's config so that 'book-reana'
    can be run without specifying --server and --token.
    """
    try:
        from .interface.shell_modules.reana_booking import register_booking_server

        result = register_booking_server(
            server_url=server_url,
            access_token=access_token,
        )
        if result.messages:
            print(result.colored())
    except Exception as e:
        print(f"Error: {e}")


@cli.command(name="book-reana", hidden=True)
@click.option("--server", "server_url", default="",
              help="REANA server URL (overrides stored credentials)")
@click.option("--token", "access_token", default="",
              help="REANA access token (overrides stored credentials)")
@click.option("--path", "project_path", default="",
              help="Path to Celebi project (default: current directory)")
@click.option("--insecure", is_flag=True, default=False,
              help="Disable SSL certificate verification")
@click.option("--upload", default="plots+logs",
              help="What to upload: plots+logs (default), plots, data, all, or a glob")
@click.option("--stageout", is_flag=True, default=False,
              help="[deprecated] alias for --upload all")
@click.option("--no-stream", is_flag=True, default=False,
              help="Disable live streaming; wait for all output before printing")
# Click options mirror the public CLI; number of options is expected.
# pylint: disable=too-many-arguments,too-many-positional-arguments
def book_reana_command(server_url, access_token, project_path,
                       insecure, stageout, upload, no_stream):
    """Book the current project to REANA as a file catalog via Yuki.

    If --server and --token are not provided, Yuki will use credentials
    previously registered via 'register-booking-server'.
    """
    try:
        result = book_reana(
            server_url=server_url,
            access_token=access_token,
            verify_ssl=not insecure,
            project_path=project_path,
            stageout=stageout,
            upload=upload,
            stream=not no_stream,
        )
        # In streaming mode, messages were already printed live.
        # Only print any remaining messages that weren't emitted.
        if not no_stream:
            # Messages already printed during streaming; nothing more to do
            pass
        elif result.messages:
            print(result.colored())
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main entry point for the Celebi CLI."""
    cli()  # pylint: disable=no-value-for-parameter
