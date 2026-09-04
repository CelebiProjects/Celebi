"""Tests for the purge-data client chain (communicator, VTaskJob, CLI)."""
import unittest
from unittest import mock

import requests
from click.testing import CliRunner

from CelebiChrono.kernel.chern_communicator import ChernCommunicator
from CelebiChrono.kernel.vtask_job import JobManager


class MockResponse:  # pylint: disable=too-few-public-methods
    """Minimal requests.Response stand-in."""

    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        """Return the canned body."""
        return self._json


def test_purge_impression_data_posts_to_server():
    """The purge POST carries force and returns the server report."""
    cc = ChernCommunicator.instance()
    cc.project_uuid = "proj-1"
    impression = mock.Mock(uuid="imp-a")
    summary = {"purged": True, "impression": "imp-a", "machines": {},
               "freed_bytes": 0}
    with mock.patch("requests.post") as post:
        post.return_value = MockResponse(200, summary)
        result = cc.purge_impression_data(impression, force=True)
        assert result == summary
        post.assert_called_once()
        args, kwargs = post.call_args
        assert args[0].endswith("/purge-impression-data/proj-1/imp-a")
        assert kwargs["json"] == {"force": True}


def test_purge_impression_data_returns_server_error():
    """A refusal body is returned as {"error": ...}."""
    cc = ChernCommunicator.instance()
    cc.project_uuid = "proj-1"
    impression = mock.Mock(uuid="imp-a")
    with mock.patch("requests.post") as post:
        post.return_value = MockResponse(400, {"error": "cannot verify"})
        result = cc.purge_impression_data(impression)
        assert result == {"error": "cannot verify"}


def test_purge_impression_data_connection_error():
    """Transport failures raise ConnectionError."""
    cc = ChernCommunicator.instance()
    cc.project_uuid = "proj-1"
    impression = mock.Mock(uuid="imp-a")
    with mock.patch("requests.post") as post:
        post.side_effect = requests.exceptions.ConnectionError("refused")
        try:
            cc.purge_impression_data(impression)
        except ConnectionError as e:
            assert "refused" in str(e)
        else:
            raise AssertionError("expected ConnectionError")


class FakeJobManager(JobManager):
    """Job manager double exposing only what purge_data uses."""

    def algorithm(self):
        """Algorithm."""
        return mock.Mock()

    def auto_download(self):
        """Auto download."""
        return False

    def cache_on_runner(self):
        """Cache on runner."""
        return False

    def default_runner(self):
        """Default runner."""
        return "local"

    def environment(self):
        """Environment."""
        return "python:3.9"

    def get_task(self, path):
        """Get task."""
        return self

    def input_md5(self):
        """Input md5."""
        return "abc123"

    def inputs(self):
        """Inputs."""
        return []

    def memory_limit(self):
        """Memory limit."""
        return "2G"

    def output_files(self):
        """Output files."""
        return []

    def parameters(self):
        """Parameters."""
        return ([], {})

    def set_input_md5(self, path):
        """Set input md5."""

    def validated(self):
        """Validated."""
        return True

    def impression(self):
        """Impression."""
        return mock.Mock(uuid="abc")


def _patch_cc():
    """Patch the communicator singleton."""
    cc = mock.Mock()
    return mock.patch(
        "CelebiChrono.kernel.vtask_job.ChernCommunicator.instance",
        return_value=cc), cc


def test_vtask_purge_data_calls_communicator():
    """purge_data forwards force to the communicator."""
    jm = FakeJobManager.__new__(FakeJobManager)
    p, cc = _patch_cc()
    cc.purge_impression_data.return_value = {
        "purged": True, "machines": {"cern": {}}, "freed_bytes": 0}
    with p:
        msg = jm.purge_data(force=True)
    cc.purge_impression_data.assert_called_once()
    args = cc.purge_impression_data.call_args
    assert args.args[0].uuid == "abc"
    assert args.kwargs == {"force": True}
    assert msg is not None


def test_vtask_purge_data_reports_refusal():
    """A server refusal surfaces as an error message."""
    jm = FakeJobManager.__new__(FakeJobManager)
    p, cc = _patch_cc()
    cc.purge_impression_data.return_value = {"error": "cannot verify"}
    with p:
        msg = jm.purge_data()
    assert any(msg_type == "error" for _text, msg_type in msg.messages)


def test_purge_data_shell_delegates():
    """The shell function forwards force to the current object."""
    from CelebiChrono.interface.shell_modules import execution_management as em
    with mock.patch.object(em.MANAGER, "current_object") as co:
        em.purge_data(force=True)
    co.return_value.purge_data.assert_called_once_with(force=True)


class TestPurgeDataCommand(unittest.TestCase):
    """Test the purge-data CLI command surface."""

    def test_purge_data_command_invokes_shell_function(self):
        """purge-data forwards --force to the shell purge_data."""
        from CelebiChrono.celebi_cli.commands.execution_management import (
            purge_data_command)
        with mock.patch(
            "CelebiChrono.interface.shell.purge_data"
        ) as fn:
            fn.return_value = mock.Mock(messages=[])
            result = CliRunner().invoke(purge_data_command, ["--force"])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with(force=True)

    def test_purge_data_command_is_registered(self):
        """purge-data is a registered subcommand of the CLI."""
        from CelebiChrono.celebi_cli.cli import cli
        names = [cmd.name for cmd in cli.commands.values()]
        self.assertIn("purge-data", names)


class TestDoPurgeData(unittest.TestCase):
    """Test the interactive-shell purge_data command handler."""

    def setUp(self):
        """Set up."""
        from CelebiChrono.interface.chern_shell import commands_environment
        self.cmds = commands_environment.EnvironmentCommands.__new__(
            commands_environment.EnvironmentCommands)

    def test_do_purge_data_dispatches_with_confirmation(self):
        """purge_data dispatches to the shell function after confirmation."""
        from CelebiChrono.interface.chern_shell import commands_environment
        with mock.patch.object(commands_environment.shell,
                               "purge_data") as purge_data, \
                mock.patch("builtins.input", return_value="y"), \
                mock.patch("builtins.print") as pr:
            purge_data.return_value = _message("purged")
            self.cmds.do_purge_data("")
        purge_data.assert_called_once_with(force=False)
        self.assertTrue(pr.called)

    def test_do_purge_data_force_flag(self):
        """--force reaches the shell function as force=True."""
        from CelebiChrono.interface.chern_shell import commands_environment
        with mock.patch.object(commands_environment.shell,
                               "purge_data") as purge_data, \
                mock.patch("builtins.input", return_value="y"), \
                mock.patch("builtins.print"):
            purge_data.return_value = _message("purged")
            self.cmds.do_purge_data("--force")
        purge_data.assert_called_once_with(force=True)

    def test_do_purge_data_cancels_without_confirmation(self):
        """Declining the confirmation runs nothing."""
        from CelebiChrono.interface.chern_shell import commands_environment
        with mock.patch.object(commands_environment.shell,
                               "purge_data") as purge_data, \
                mock.patch("builtins.input", return_value="n"), \
                mock.patch("builtins.print"):
            self.cmds.do_purge_data("")
        purge_data.assert_not_called()


def _message(text):
    """A Message stand-in with a colored() renderer."""
    msg = mock.MagicMock()
    msg.messages = [(text, "info")]
    msg.colored.return_value = "rendered"
    return msg


if __name__ == "__main__":
    unittest.main()
