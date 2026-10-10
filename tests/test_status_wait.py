"""Live status waiting bypasses cached workflow snapshots."""
import json
from unittest import mock

from click.testing import CliRunner

from CelebiChrono.celebi_cli.cli import cli
from CelebiChrono.interface.chern_shell.commands_basic import (
    BasicCommands, _parse_status_args)
from CelebiChrono.interface.shell_modules import task_configuration
from CelebiChrono.kernel.chern_communicator import ChernCommunicator
from CelebiChrono.utils.message import Message


def _status_message(status, text=None):
    message = Message()
    message.add(text or f"Job status: [{status}]\n")
    message.data["job_status"] = status
    return message


def test_communicator_wait_requests_synchronous_live_refresh():
    """A live status request uses Yuki's wait query and long timeout."""
    communicator = object.__new__(ChernCommunicator)
    communicator.timeout = 10
    communicator.transfer_timeout = 600
    communicator.project_uuid = "project"
    communicator.serverurl = lambda: "localhost:3315"
    impression = mock.Mock(uuid="impression")
    response = mock.Mock(text=json.dumps({
        "status": "running", "status_legacy": "running"}))

    with mock.patch(
            "CelebiChrono.kernel.chern_communicator.requests.get",
            return_value=response) as get:
        result = communicator.job_status(impression, wait=True)

    assert result["status"] == "running"
    assert get.call_args.args[0].endswith(
        "/status/project/impression?wait=true")
    assert get.call_args.kwargs["timeout"] == 600


def test_status_updates_skips_unchanged_snapshots_and_stops_at_terminal():
    """Waiting reports changes and treats unknown/running as non-terminal."""
    running = _status_message("running")
    unchanged = _status_message("running")
    finished = _status_message("finished")
    with mock.patch.object(task_configuration, "status",
                           side_effect=[running, unchanged, finished]) as status, \
         mock.patch.object(task_configuration.time, "sleep") as sleep:
        updates = list(task_configuration.status_updates(3.0))

    assert updates == [running, finished]
    assert status.call_args_list == [mock.call(live=True)] * 3
    assert sleep.call_args_list == [mock.call(3.0), mock.call(3.0)]


def test_cli_status_wait_streams_live_updates():
    """The CLI exposes --wait and prints each changed live snapshot."""
    updates = [_status_message("running"), _status_message("finished")]
    with mock.patch(
            "CelebiChrono.celebi_cli.commands.navigation._require_project",
            return_value=True), \
         mock.patch("CelebiChrono.interface.shell.status_updates",
                    return_value=updates) as status_updates, \
         mock.patch("CelebiChrono.interface.shell.status") as status:
        result = CliRunner().invoke(
            cli, ["status", "--wait", "--poll-interval", "4"])

    assert not result.exit_code, result.output
    assert "Job status: [running]" in result.output
    assert "Job status: [finished]" in result.output
    status_updates.assert_called_once_with(4.0)
    status.assert_not_called()


def test_interactive_status_wait_uses_same_live_updates(capsys):
    """The interactive shell accepts the same status --wait spelling."""
    updates = [_status_message("running"), _status_message("finished")]
    with mock.patch("CelebiChrono.interface.shell.status_updates",
                    return_value=updates) as status_updates:
        BasicCommands().do_status("--wait -i 5")

    assert "Job status: [running]" in capsys.readouterr().out
    status_updates.assert_called_once_with(5.0)


def test_status_argument_parser_rejects_unknown_options():
    """Interactive status options fail explicitly instead of being ignored."""
    assert _parse_status_args("--wait -i 1") == (True, 1.0)
    try:
        _parse_status_args("--cached")
    except ValueError as exc:
        assert "Unknown status option" in str(exc)
    else:
        raise AssertionError("unknown status option should fail")
