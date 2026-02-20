"""Navigation commands for Celebi CLI."""
import click
from CelebiChrono.celebi_cli.utils import format_output


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
    from CelebiChrono.interface.shell import tree
    result = tree()
    output = format_output(result)
    if output:
        print(output)


@click.command(name="status")
def status_command():
    """Show status."""
    from CelebiChrono.interface.shell import status
    result = status()
    output = format_output(result)
    if output:
        print(output)


@click.command(name="navigate")
def navigate_command():
    """Change to current project directory."""
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
    from CelebiChrono.interface.shell import short_ls
    result = short_ls("")
    output = format_output(result)
    if output:
        print(output)


@click.command(name="jobs")
def jobs_command():
    """Show jobs."""
    from CelebiChrono.interface.shell import jobs
    result = jobs("")
    output = format_output(result)
    if output:
        print(output)
