"""Liveness commands: sync the live set and purge stale runner data."""
import click

from .execution_management import _handle_error, _handle_result


@click.command(name="sync-live")
def sync_live_command() -> None:
    """Push the project's live impression set to DITE."""
    try:
        from CelebiChrono.interface.shell import sync_live
        _handle_result(sync_live())
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="purge-stale-cache")
@click.argument("runner", type=str)
@click.option("--dry-run", is_flag=True,
              help="List what would be purged without deleting anything.")
@click.option("--yes", "-y", is_flag=True,
              help="Skip the confirmation prompt.")
def purge_stale_cache_command(runner, dry_run, yes) -> None:
    """Purge superseded impressions' cache entries from a runner.

    RUNNER is the name of the registered runner. Only impressions that
    the project's synced live set marks superseded are selected.
    """
    try:
        from CelebiChrono.interface.shell import purge_stale_cache
        if not dry_run and not yes:
            click.confirm(
                f"Purge superseded impressions' cache on runner "
                f"'{runner}'?", abort=True)
        _handle_result(purge_stale_cache(runner, dry_run=dry_run))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="purge-stale-workflows")
@click.argument("runner", type=str)
@click.option("--dry-run", is_flag=True,
              help="List what would be purged without deleting anything.")
@click.option("--yes", "-y", is_flag=True,
              help="Skip the confirmation prompt.")
def purge_stale_workflows_command(runner, dry_run, yes) -> None:
    """Delete non-live workflow workspaces from a runner.

    RUNNER is the name of the registered runner. Workflows whose
    project's synced live set excludes them (and which are not running)
    are deleted; the local Workflows mirror is always kept.
    """
    try:
        from CelebiChrono.interface.shell import purge_stale_workflows
        if not dry_run and not yes:
            click.confirm(
                f"Purge non-live workflows on runner '{runner}'?",
                abort=True)
        _handle_result(purge_stale_workflows(runner, dry_run=dry_run))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")
