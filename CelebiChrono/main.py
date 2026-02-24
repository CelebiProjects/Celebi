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

        docstring = func.__doc__
        if not docstring:
            return ""

        lines = docstring.strip().split('\n')
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
                not current_project or
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

# ----------------------------------------------------------------------
# Git Integration Commands
# ----------------------------------------------------------------------

@click.group()
def git_cli():
    """Celebi git integration commands."""


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

            # Offer to install hooks
            choice = input("Install git hooks for automatic validation? [Y/n]: ").strip().lower()
            if choice in ['', 'y', 'yes']:
                if git_integration.install_hooks():
                    print("✓ Git hooks installed")
                else:
                    print("⚠ Failed to install git hooks")

            # Show recommended settings
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

def main():
    """Main entry point for the Celebi CLI."""
    cli()  # pylint: disable=no-value-for-parameter
