"""Tests for the liveness CLI commands."""
from unittest import mock

from click.testing import CliRunner
from CelebiChrono.celebi_cli.cli import cli


def test_sync_live_command_calls_shell():
    """/sync-live delegates to the shell function."""
    runner = CliRunner()
    with mock.patch("CelebiChrono.interface.shell.sync_live") as fn:
        fn.return_value = "Synced live set: 1 live"
        result = runner.invoke(cli, ["sync-live"])
    assert result.exit_code == 0
    fn.assert_called_once_with()


def test_purge_stale_cache_command_calls_shell():
    """purge-stale-cache passes the runner, honoring dry-run/yes."""
    runner = CliRunner()
    with mock.patch(
            "CelebiChrono.interface.shell.purge_stale_cache") as fn:
        fn.return_value = "Purged 1 cache entries"
        result = runner.invoke(
            cli, ["purge-stale-cache", "pkufarm",
                  "--dry-run", "--yes"])
    assert result.exit_code == 0
    fn.assert_called_once_with("pkufarm", dry_run=True)


def test_purge_stale_workflows_command_calls_shell():
    """purge-stale-workflows passes the runner, honoring --yes."""
    runner = CliRunner()
    with mock.patch(
            "CelebiChrono.interface.shell.purge_stale_workflows") as fn:
        fn.return_value = "Purged 0 workflows"
        result = runner.invoke(
            cli, ["purge-stale-workflows", "pkufarm", "--yes"])
    assert result.exit_code == 0
    fn.assert_called_once_with("pkufarm", dry_run=False)
