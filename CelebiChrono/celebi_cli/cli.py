import click

@click.group()
def cli():
    """Celebi CLI - Command line interface for Celebi Chrono"""
    pass

# Import command modules here
# from .commands import project, task, etc.

if __name__ == '__main__':
    cli()