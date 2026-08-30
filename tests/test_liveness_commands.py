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


def test_impress_hook_fires_and_survives_raising_sync():
    """impress fires the sync-live hook; a raising sync never breaks it."""
    runner = CliRunner()
    with mock.patch("CelebiChrono.interface.shell.impress",
                    return_value="") as impress_fn, \
            mock.patch("CelebiChrono.interface.shell.sync_live",
                       side_effect=OSError("boom")) as sync_fn:
        result = runner.invoke(cli, ["impress"])
    assert result.exit_code == 0
    impress_fn.assert_called_once_with()
    sync_fn.assert_called_once_with()


def test_kill_workflow_command_calls_shell():
    """kill-workflow delegates to the shell function."""
    runner = CliRunner()
    with mock.patch("CelebiChrono.interface.shell.kill_workflow") as fn:
        fn.return_value = "Killed workflow: wf-1"
        result = runner.invoke(cli, ["kill-workflow", "wf-1"])
    assert result.exit_code == 0
    fn.assert_called_once_with("wf-1")
