"""Tests for celebi-cli log --follow flag."""
from unittest import mock

from click.testing import CliRunner
from CelebiChrono.celebi_cli.cli import cli


class FakeMessage:
    """Minimal Message stand-in for offset tests."""

    def __init__(self, text):
        """Create a fake message wrapping the given raw text."""
        self.messages = [(text, "")]

    def colored(self):
        """Return a display string longer than the raw text (simulates ANSI)."""
        return f"\033[32m{self.messages[0][0]}\033[0m"

    def raw_text(self):
        """Return the raw underlying text."""
        return self.messages[0][0]


def test_log_command_without_follow_calls_error_log_once():
    """Without --follow the command calls error_log once and prints it."""
    runner = CliRunner()
    with mock.patch("CelebiChrono.interface.shell.error_log") as mock_error_log:
        mock_error_log.return_value = "log line\n"
        result = runner.invoke(cli, ["log", "0"])

    assert not result.exit_code
    assert "log line" in result.output
    mock_error_log.assert_called_once_with(0)


def test_log_command_without_follow_prints_placeholder_when_empty():
    """Without --follow an empty log prints the 'No log content found' message."""
    runner = CliRunner()
    with mock.patch("CelebiChrono.interface.shell.error_log") as mock_error_log:
        mock_error_log.return_value = ""
        result = runner.invoke(cli, ["log", "0"])

    assert not result.exit_code
    assert result.output == "No log content found\n"
    mock_error_log.assert_called_once_with(0)


def test_log_follow_polls_with_offset_and_stops_on_keyboard_interrupt():
    """--follow polls repeatedly with increasing offset until interrupted."""
    runner = CliRunner()
    with mock.patch("CelebiChrono.interface.shell.error_log") as mock_error_log:
        mock_error_log.side_effect = ["first\n", "second\n", "third\n"]
        with mock.patch("time.sleep") as mock_sleep:
            mock_sleep.side_effect = [None, None, KeyboardInterrupt]
            result = runner.invoke(cli, ["log", "--follow", "0"])

    assert not result.exit_code
    assert "first" in result.output
    assert "second" in result.output
    assert "third" in result.output
    assert mock_error_log.call_count == 3
    mock_error_log.assert_has_calls([
        mock.call(0, offset=0),
        mock.call(0, offset=6),
        mock.call(0, offset=13),
    ])


def test_log_follow_tracks_raw_bytes_for_offset():
    """Offset must advance by raw message length, not colored display length."""
    runner = CliRunner()
    with mock.patch("CelebiChrono.interface.shell.error_log") as mock_error_log:
        raw_text = "hi\n"
        mock_error_log.side_effect = [FakeMessage(raw_text), KeyboardInterrupt]
        with mock.patch("time.sleep") as mock_sleep:
            mock_sleep.side_effect = [None, KeyboardInterrupt]
            result = runner.invoke(cli, ["log", "--follow", "0"])

    assert not result.exit_code
    assert "hi" in result.output
    assert mock_error_log.call_count == 2
    mock_error_log.assert_has_calls([
        mock.call(0, offset=0),
        mock.call(0, offset=3),
    ])


def test_log_follow_uses_custom_poll_interval():
    """--poll-interval controls the sleep duration between polls."""
    runner = CliRunner()
    with mock.patch("CelebiChrono.interface.shell.error_log") as mock_error_log:
        mock_error_log.return_value = ""
        with mock.patch("time.sleep") as mock_sleep:
            mock_sleep.side_effect = [None, KeyboardInterrupt]
            result = runner.invoke(cli, ["log", "--follow", "--poll-interval", "5", "0"])

    assert not result.exit_code
    mock_sleep.assert_called_with(5)


def test_log_follow_stays_silent_and_keeps_offset_on_empty():
    """--follow must not print or advance the offset for empty responses."""
    runner = CliRunner()
    with mock.patch("CelebiChrono.interface.shell.error_log") as mock_error_log:
        mock_error_log.side_effect = ["", "line\n", KeyboardInterrupt]
        with mock.patch("time.sleep") as mock_sleep:
            mock_sleep.side_effect = [None, None, KeyboardInterrupt]
            result = runner.invoke(cli, ["log", "--follow", "0"])

    assert not result.exit_code
    assert result.output == "line\n"
    mock_error_log.assert_has_calls([
        mock.call(0, offset=0),
        mock.call(0, offset=0),
        mock.call(0, offset=5),
    ])


def test_log_command_registered_with_follow_flag():
    """The log command exposes --follow and --poll-interval options."""
    log_cmd = cli.commands["log"]
    params = {p.name for p in log_cmd.params}
    assert "follow" in params
    assert "poll_interval" in params
