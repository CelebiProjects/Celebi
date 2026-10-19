"""Project registry commands for the non-interactive Celebi CLI."""

import click

from CelebiChrono.kernel import vproject
from CelebiChrono.utils import csys, metadata


def _registry():
    """Return the per-user project registry."""
    return metadata.ConfigFile(csys.local_config_path())


@click.command(name="init")
@click.option("--uuid", "project_uuid", default=None,
              help="Use the analysis UUID issued by the bookkeeping website.")
def init_command(project_uuid=None):
    """Initialize the current empty directory as a Celebi project.

    Creates the project metadata and README, registers the project in the
    per-user project registry, and selects it as the current project.

    The directory must be empty. The command asks whether to keep the
    directory name as the project name.
    """
    try:
        if project_uuid:
            import re
            if not re.fullmatch(r"(?:[0-9a-f]{32}|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})",
                                project_uuid):
                raise ValueError("Invalid project UUID")
            vproject.init_project(project_uuid=project_uuid)
        else:
            vproject.init_project()
    except Exception as error:
        raise click.ClickException(str(error)) from error


@click.command(name="list-projects")
def list_projects_command():
    """List registered projects and mark the current selection.

    The selected project is prefixed with `*`. Project files are not scanned;
    this command reads the per-user project registry.
    """
    config = _registry()
    projects = config.read_variable("projects_path", {}) or {}
    current = config.read_variable("current_project", "")
    if not projects:
        click.echo("No registered Celebi projects.")
        return
    for name, path in sorted(projects.items()):
        marker = "*" if name == current else " "
        click.echo(f"{marker} {name}: {path}")


@click.command(name="use-project")
@click.argument("project", type=str)
def use_project_command(project):
    """Select a registered PROJECT for subsequent Celebi sessions.

    This changes the project opened by a later `celebi` invocation. It does
    not change the working directory of the calling system shell.
    """
    config = _registry()
    projects = config.read_variable("projects_path", {}) or {}
    if project not in projects:
        raise click.ClickException(f"Project '{project}' is not registered")
    config.write_variable("current_project", project)
    click.echo(f"Current project: {project}")


@click.command(name="register-project")
@click.argument("path", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--new-project",
    is_flag=True,
    help="Assign the registered project a newly generated UUID.",
)
def register_project_command(path, new_project):
    """Register an existing Celebi project at PATH.

    PATH must contain valid Celebi project metadata. The command adds it to
    the per-user registry and selects it as the current project without
    copying or moving project files. Use ``--new-project`` when registering a
    copied project that should have an identity distinct from its source.
    """
    try:
        vproject.use_project(path, new_project=new_project)
    except Exception as error:
        raise click.ClickException(str(error)) from error


@click.command(name="remove-project")
@click.argument("project", type=str)
def remove_project_command(project):
    """Remove PROJECT from the registry without deleting its files.

    If PROJECT is currently selected, the selection is cleared. No project
    directory or analysis data is removed from disk.
    """
    config = _registry()
    projects = config.read_variable("projects_path", {}) or {}
    if project not in projects:
        raise click.ClickException(f"Project '{project}' is not registered")
    projects.pop(project)
    config.write_variable("projects_path", projects)
    if config.read_variable("current_project", "") == project:
        config.write_variable("current_project", "")
    click.echo(f"Removed project from registry: {project}")
