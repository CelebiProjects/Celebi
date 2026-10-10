"""Navigation commands for Celebi CLI."""
import os

import click
from CelebiChrono.celebi_cli.utils import format_output


def _require_project():
    """Return whether the command is running inside a Celebi project."""
    from CelebiChrono.utils import csys
    if csys.project_path(os.getcwd()):
        return True
    print("Error: Not inside a Celebi project.")
    return False


@click.command(name="cd")
@click.argument("path", type=str)
def cd_command(path):
    """Change directory within project."""
    from CelebiChrono.interface.shell import cd
    result = cd(path)
    output = format_output(result)
    if output:
        print(output)


@click.command(name="tree")
def tree_command():
    """Show tree view."""
    if not _require_project():
        return
    from CelebiChrono.interface.shell import tree
    result = tree()
    output = format_output(result)
    if output:
        print(output)


@click.command(name="status")
@click.option("--wait", is_flag=True, default=False,
              help="Poll live runner state until the job becomes terminal.")
@click.option("--poll-interval", "-i", type=click.FloatRange(min=0.1),
              default=2.0, show_default=True,
              help="Seconds between live status refreshes.")
def status_command(wait, poll_interval):
    """Show status, optionally waiting on live runner refreshes."""
    if not _require_project():
        return
    from CelebiChrono.interface.shell import status, status_updates
    try:
        updates = status_updates(poll_interval) if wait else [status()]
        first = True
        for result in updates:
            output = format_output(result)
            if output:
                if not first:
                    print("---")
                print(output)
                first = False
    except KeyboardInterrupt:
        return


@click.command(name="project-path")
def navigate_command():
    """Print the current project's filesystem path."""
    from CelebiChrono.interface.shell import navigate
    result = navigate()
    output = format_output(result)
    if output:
        print(output)


@click.command(name="cdproject")
@click.argument("project", type=str)
def cdproject_command(project):
    """Change to project directory."""
    from CelebiChrono.interface.shell import shell_cd_project
    result = shell_cd_project(project)
    output = format_output(result)
    if output:
        print(output)


@click.command(name="short-ls")
def short_ls_command():
    """Short listing."""
    if not _require_project():
        return
    from CelebiChrono.interface.shell import short_ls
    result = short_ls("")
    output = format_output(result)
    if output:
        print(output)


@click.command(name="project-uuid")
def project_uuid_command():
    """Print the stable UUID of the project containing the current directory.

    The command fails cleanly outside a Celebi project. The UUID identifies
    the project in DITE, Yuki, and impression metadata.
    """
    from CelebiChrono.utils import csys
    from CelebiChrono.kernel.vproject import VProject
    project_path = csys.project_path(os.getcwd())
    if not project_path:
        print("Error: Not inside a Celebi project.")
        return
    uuid = VProject(project_path).project_uuid()
    print(uuid)
