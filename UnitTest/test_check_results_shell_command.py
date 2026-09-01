"""Tests for the `check-results <runner>` shell command wiring."""
import unittest
from unittest import mock

from CelebiChrono.interface.chern_shell import commands_execution
from CelebiChrono.interface.chern_shell.commands_execution import (
    CommandsExecution)
from CelebiChrono.interface.chern_shell.completions import (
    ChernShellCompletions)
from CelebiChrono.interface.shell_modules import execution_management


def _message(text):
    """A Message stand-in with a colored() renderer."""
    msg = mock.MagicMock()
    msg.messages = [(text, "info")]
    msg.colored.return_value = "rendered"
    return msg


class TestDoCheckResults(unittest.TestCase):

    """Test the do_check_results command."""

    def setUp(self):
        """Set up."""
        self.cmds = CommandsExecution.__new__(CommandsExecution)

    def test_do_check_results_dispatches_to_check_results(self):
        """`check-results <runner>` calls the check_results shell function."""
        with mock.patch.object(commands_execution,
                               "check_results") as check_results, \
                mock.patch("builtins.print") as pr:
            check_results.return_value = _message("ok")
            self.cmds.do_check_results("farm")
        check_results.assert_called_once_with("farm")
        self.assertTrue(pr.called)

    def test_do_check_results_requires_runner(self):
        """`check-results` without a runner prints an error and runs nothing."""
        with mock.patch.object(commands_execution,
                               "check_results") as check_results, \
                mock.patch("builtins.print") as pr:
            self.cmds.do_check_results("")
        check_results.assert_not_called()
        self.assertTrue(pr.called)


class TestExecutionManagementCheckResults(unittest.TestCase):

    """Test the execution_management.check_results wrapper."""

    def test_check_results_delegates_to_current_object(self):
        """check_results forwards to the current object."""
        obj = mock.MagicMock()
        obj.check_results.return_value = _message("ok")
        with mock.patch.object(execution_management, "MANAGER") as manager:
            manager.current_object.return_value = obj
            execution_management.check_results("farm")
        obj.check_results.assert_called_once_with("farm")


class TestCompleteCheckResults(unittest.TestCase):

    """Test runner-name completion for `check-results`."""

    def setUp(self):
        """Set up."""
        self.completions = ChernShellCompletions.__new__(ChernShellCompletions)
        self.completions.readline_file = mock.MagicMock()
        self.completions.readline_file.read_variable.return_value = [
            "farm1", "farm2", "reana1"]

    def test_complete_check_results_suggests_runners(self):
        """Runner names are completed after `check-results`."""
        self.assertEqual(
            self.completions.complete_check_results("fa", "check-results fa",
                                                    0, 16),
            ["farm1", "farm2"])
