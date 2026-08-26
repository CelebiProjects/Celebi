"""Tests for the chern shell `transfer` command."""
from unittest import mock

from CelebiChrono.interface.chern_shell.commands_file import FileCommands
from CelebiChrono.interface.chern_shell.completions import ChernShellCompletions


class FakeMessage:  # pylint: disable=too-few-public-methods
    """Minimal Message stand-in carrying raw text."""

    def __init__(self, text):
        """Wrap the given raw text."""
        self.messages = [(text, "")]

    def colored(self):
        """Return the display text."""
        return self.messages[0][0]


class _FakeReadline:  # pylint: disable=too-few-public-methods
    """Fake readline file returning a fixed runners list."""

    def __init__(self, runners):
        """Store the runners to report."""
        self.runners = runners

    def read_variable(self, name, default):
        """Return runners for the runners variable, else the default."""
        if name == "runners":
            return self.runners
        return default


def test_do_transfer_passes_positional_args_and_prints_result(capsys):
    """`transfer yuki runner:r1` calls shell.transfer and prints the result."""
    cmd = FileCommands()
    with mock.patch("CelebiChrono.interface.shell.transfer") as mock_transfer:
        mock_transfer.return_value = FakeMessage("Transferred 3, skipped 1")
        cmd.do_transfer("yuki runner:r1")

    mock_transfer.assert_called_once_with(
        "yuki", "runner:r1", pattern=None, force=False)
    assert "Transferred 3, skipped 1" in capsys.readouterr().out


def test_do_transfer_parses_pattern_and_force(capsys):
    """`transfer` forwards --pattern and --force to the shell function."""
    cmd = FileCommands()
    with mock.patch("CelebiChrono.interface.shell.transfer") as mock_transfer:
        mock_transfer.return_value = FakeMessage("done")
        cmd.do_transfer("runner:r1 yuki --pattern *.png --force")

    mock_transfer.assert_called_once_with(
        "runner:r1", "yuki", pattern="*.png", force=True)
    assert capsys.readouterr().out  # result printed


def test_do_transfer_missing_args_prints_error_without_calling_shell(capsys):
    """`transfer` with fewer than two arguments prints a usage error."""
    cmd = FileCommands()
    with mock.patch("CelebiChrono.interface.shell.transfer") as mock_transfer:
        cmd.do_transfer("yuki")

    mock_transfer.assert_not_called()
    assert "source and destination" in capsys.readouterr().out


def test_do_transfer_reports_shell_errors(capsys):
    """Exceptions from shell.transfer are reported, not raised."""
    cmd = FileCommands()
    with mock.patch("CelebiChrono.interface.shell.transfer") as mock_transfer:
        mock_transfer.side_effect = RuntimeError("boom")
        cmd.do_transfer("yuki runner:r1")

    assert "Error transferring" in capsys.readouterr().out


def test_complete_transfer_lists_yuki_and_runners():
    """Completing the first arg offers yuki and runner:<id> options."""
    completions = ChernShellCompletions()
    completions.readline_file = _FakeReadline(["r1", "r2"])

    result = completions.complete_transfer("", "transfer ", 0, 0)

    assert result == ["yuki", "runner:r1", "runner:r2"]


def test_complete_transfer_filters_by_prefix():
    """Runner options are filtered by the text prefix."""
    completions = ChernShellCompletions()
    completions.readline_file = _FakeReadline(["r1", "r2"])

    result = completions.complete_transfer("run", "transfer run", 0, 0)

    assert result == ["runner:r1", "runner:r2"]


def test_complete_transfer_empty_after_both_positional_args():
    """No completion after source and destination are given."""
    completions = ChernShellCompletions()
    completions.readline_file = _FakeReadline(["r1"])

    result = completions.complete_transfer("", "transfer yuki runner:r1 ", 0, 0)

    assert result == []
