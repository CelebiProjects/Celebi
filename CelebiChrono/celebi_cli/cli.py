import click
from .commands import navigation

@click.group()
def cli():
    """Celebi CLI commands for project management."""
    pass

# Commands will be registered here
cli.add_command(navigation.cd_command)
cli.add_command(navigation.tree_command)
cli.add_command(navigation.status_command)
cli.add_command(navigation.navigate_command)
cli.add_command(navigation.cdproject_command)
cli.add_command(navigation.short_ls_command)
cli.add_command(navigation.jobs_command)