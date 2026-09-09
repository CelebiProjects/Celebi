"""Preview, confirmation, and sync failure coverage for bulk cancellation."""
from unittest import mock

import pytest
from click.testing import CliRunner

from CelebiChrono.celebi_cli.cli import cli
from CelebiChrono.interface.chern_shell.commands_environment import EnvironmentCommands
from CelebiChrono.interface.shell_modules import communication
from CelebiChrono.utils.message import Message


def plan():
    message = Message()
    message.add("Would force-stop: old\n")
    message.data["workflows"] = ["old"]
    return message


@pytest.mark.parametrize("flags,answer,execute", [
    (["--dry-run"], "", False), ([], "n\n", False),
    ([], "y\n", True), (["--yes"], "", True),
])
def test_cli_previews_before_confirmation(flags, answer, execute):
    with mock.patch("CelebiChrono.interface.shell.kill_running_workflows") as kill:
        kill.side_effect = [plan(), Message()]
        result = CliRunner().invoke(
            cli, ["kill-running-workflows", "farm", *flags], input=answer)
    assert result.exit_code == 0, result.output
    assert "Would force-stop: old" in result.output
    assert kill.call_args_list[0] == mock.call("farm", dry_run=True)
    assert kill.call_count == (2 if execute else 1)
    if execute:
        assert kill.call_args_list[1] == mock.call(
            "farm", dry_run=False, workflows=["old"])


def test_interactive_shell_confirms_exact_preview():
    with mock.patch("CelebiChrono.interface.shell.kill_running_workflows") as kill, \
            mock.patch("builtins.input", return_value="y"):
        kill.side_effect = [plan(), Message()]
        EnvironmentCommands().do_kill_running_workflows("farm")
    assert kill.call_args_list == [mock.call("farm", dry_run=True),
                                  mock.call("farm", dry_run=False, workflows=["old"])]


def test_sync_failure_prevents_bulk_kill():
    failed = Message()
    failed.add("Live-set sync failed", "warning")
    with mock.patch.object(communication, "_current_project_uuid", return_value="proj"), \
            mock.patch.object(communication, "sync_live", return_value=failed), \
            mock.patch.object(communication.ChernCommunicator, "instance") as comm:
        result = communication.kill_running_workflows("farm")
    assert not result.success
    comm.assert_not_called()


def test_shell_service_preserves_selected_ids():
    with mock.patch.object(communication, "_current_project_uuid", return_value="proj"), \
            mock.patch.object(communication, "sync_live", return_value=Message()), \
            mock.patch.object(communication.ChernCommunicator, "instance") as comm:
        comm.return_value.kill_running_workflows.return_value = {
            "selected": [{"workflow": "old"}], "skipped": [], "failed": []}
        result = communication.kill_running_workflows("farm")
    assert result.success
    assert result.data["workflows"] == ["old"]
    comm.return_value.kill_running_workflows.assert_called_once_with(
        "farm", "proj", dry_run=True, workflows=None)
