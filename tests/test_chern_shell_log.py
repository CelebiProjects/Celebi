"""Tests for the chern shell `log` command, including --follow."""
from unittest import mock

import pytest

from CelebiChrono.interface.chern_shell.commands_basic import BasicCommands


class FakeMessage:
    """Minimal Message stand-in carrying raw text."""

    def __init__(self, text):
        """Wrap the given raw text."""
        self.messages = [(text, "")]

    def colored(self):
        """Return the display text."""
        return self.messages[0][0]


def test_do_log_follow_polls_with_growing_offset(capsys):
    """`log 0 --follow` polls error_log with increasing offsets until Ctrl-C."""
    cmd = BasicCommands()
    with mock.patch("CelebiChrono.interface.shell.error_log") as mock_error_log, \
         mock.patch("time.sleep") as mock_sleep:
        mock_error_log.side_effect = [FakeMessage("first\n"), FakeMessage("second\n")]
        mock_sleep.side_effect = [None, KeyboardInterrupt]
        with pytest.raises(KeyboardInterrupt):
            cmd.do_log("0 --follow")

    out = capsys.readouterr().out
    assert "first" in out
    assert "second" in out
    mock_error_log.assert_has_calls([
        mock.call(0, offset=0),
        mock.call(0, offset=6),
    ])


def test_do_log_without_follow_prints_placeholder_when_empty(capsys):
    """`log 0` prints 'No log content found' when the log is empty."""
    cmd = BasicCommands()
    with mock.patch("CelebiChrono.interface.shell.error_log") as mock_error_log:
        mock_error_log.return_value = FakeMessage("")
        cmd.do_log("0")

    assert capsys.readouterr().out == "No log content found\n"
    mock_error_log.assert_called_once_with(0)


def test_do_log_without_follow_prints_content_once(capsys):
    """`log 0` prints the log content and returns."""
    cmd = BasicCommands()
    with mock.patch("CelebiChrono.interface.shell.error_log") as mock_error_log:
        mock_error_log.return_value = FakeMessage("log line\n")
        cmd.do_log("0")

    assert capsys.readouterr().out == "log line\n"
    mock_error_log.assert_called_once_with(0)
