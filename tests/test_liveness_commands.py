"""Tests for the liveness CLI commands."""
from unittest import mock

from click.testing import CliRunner
from CelebiChrono.celebi_cli.cli import cli
from CelebiChrono.interface.shell_modules import execution_management
from CelebiChrono.kernel.chern_communicator import ChernCommunicator
from CelebiChrono.kernel.vobj_execution import ExecutionManagement


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


def test_kill_command_calls_shell_for_current_task():
    """kill delegates to the shell function for the current task."""
    runner = CliRunner()
    with mock.patch("CelebiChrono.interface.shell.kill") as fn:
        fn.return_value = "Killed impression"
        result = runner.invoke(cli, ["kill"])
    assert result.exit_code == 0
    assert "Killed impression" in result.output
    fn.assert_called_once_with()


def test_kill_directory_kills_all_nested_tasks():
    """Directory kill recursively kills each task impression."""
    directory = mock.MagicMock(spec=ExecutionManagement)
    directory.is_task.return_value = False
    nested_directory = mock.MagicMock()
    nested_directory.is_task.return_value = False
    first_object = mock.MagicMock(path="first")
    first_object.is_task.return_value = True
    second_object = mock.MagicMock(path="nested/second")
    second_object.is_task.return_value = True
    new_object = mock.MagicMock(path="new-task")
    new_object.is_task.return_value = True
    directory.sub_objects_recursively.return_value = [
        directory, first_object, nested_directory, second_object, new_object
    ]

    first_task = mock.MagicMock()
    first_task.impression.return_value.uuid = "impression-1"
    second_task = mock.MagicMock()
    second_task.impression.return_value.uuid = "impression-2"
    new_task = mock.MagicMock()
    new_task.impression.return_value = None
    directory.get_vtask.side_effect = [first_task, second_task, new_task]
    directory.kill.side_effect = lambda: ExecutionManagement.kill(directory)

    with mock.patch.object(execution_management.MANAGER, "current_object",
                           return_value=directory), \
            mock.patch.object(ChernCommunicator, "instance") as communicator:
        result = execution_management.kill()

    assert result.success
    assert result.data == {}
    assert "impression-1" in result.colored()
    assert "impression-2" in result.colored()
    assert communicator.return_value.kill.call_args_list == [
        mock.call(first_task.impression.return_value),
        mock.call(second_task.impression.return_value),
    ]
