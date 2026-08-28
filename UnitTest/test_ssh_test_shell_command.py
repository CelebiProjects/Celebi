"""Tests for the `test ssh <runner>` shell command wiring."""
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


class TestDoTestDispatch(unittest.TestCase):

    """Test the do_test mode dispatch."""

    def setUp(self):
        """Set up."""
        self.cmds = CommandsExecution.__new__(CommandsExecution)

    def test_do_test_ssh_dispatches_to_ssh_test(self):
        """`test ssh <runner>` calls the ssh_test shell function."""
        with mock.patch.object(commands_execution, "ssh_test") as ssh_test, \
                mock.patch("builtins.print") as pr:
            ssh_test.return_value = _message("ok")
            self.cmds.do_test("ssh farm")
        ssh_test.assert_called_once_with("farm")
        self.assertTrue(pr.called)

    def test_do_test_ssh_requires_runner(self):
        """`test ssh` without a runner prints an error and runs nothing."""
        with mock.patch.object(commands_execution, "ssh_test") as ssh_test, \
                mock.patch("builtins.print") as pr:
            self.cmds.do_test("ssh")
        ssh_test.assert_not_called()
        self.assertTrue(pr.called)

    def test_do_test_docker_keeps_existing_behavior(self):
        """`test docker <image> <command>` still calls test()."""
        with mock.patch.object(commands_execution, "test") as test, \
                mock.patch.object(commands_execution, "ssh_test") as ssh_test:
            self.cmds.do_test("docker ubuntu:latest ls -l")
        test.assert_called_once_with()
        ssh_test.assert_not_called()

    def test_do_test_requires_arguments(self):
        """`test` with no arguments prints usage."""
        with mock.patch.object(commands_execution, "test") as test, \
                mock.patch.object(commands_execution, "ssh_test") as ssh_test, \
                mock.patch("builtins.print") as pr:
            self.cmds.do_test("")
        test.assert_not_called()
        ssh_test.assert_not_called()
        self.assertTrue(pr.called)

    def test_do_test_unknown_mode(self):
        """An unknown mode prints usage and runs nothing."""
        with mock.patch.object(commands_execution, "test") as test, \
                mock.patch.object(commands_execution, "ssh_test") as ssh_test, \
                mock.patch("builtins.print") as pr:
            self.cmds.do_test("bogus arg")
        test.assert_not_called()
        ssh_test.assert_not_called()
        self.assertTrue(pr.called)


class TestExecutionManagementSshTest(unittest.TestCase):

    """Test the execution_management.ssh_test wrapper."""

    def test_ssh_test_delegates_to_current_object(self):
        """ssh_test forwards to the current object."""
        obj = mock.MagicMock()
        obj.ssh_test.return_value = _message("ok")
        with mock.patch.object(execution_management, "MANAGER") as manager:
            manager.current_object.return_value = obj
            execution_management.ssh_test("farm")
        obj.ssh_test.assert_called_once_with("farm")


class TestCompleteTest(unittest.TestCase):

    """Test runner-name completion for `test ssh`."""

    def setUp(self):
        """Set up."""
        self.completions = ChernShellCompletions.__new__(ChernShellCompletions)
        self.completions.readline_file = mock.MagicMock()
        self.completions.readline_file.read_variable.return_value = [
            "farm1", "farm2", "reana1"]

    def test_complete_test_suggests_modes(self):
        """The first word completes to docker/ssh."""
        self.assertEqual(
            self.completions.complete_test("", "test ", 0, 5),
            ["docker", "ssh"])
        self.assertEqual(
            self.completions.complete_test("s", "test s", 0, 6),
            ["ssh"])

    def test_complete_test_suggests_runners_after_ssh(self):
        """After `test ssh`, runner names are completed."""
        self.assertEqual(
            self.completions.complete_test("fa", "test ssh fa", 0, 12),
            ["farm1", "farm2"])

    def test_complete_test_no_runners_after_docker(self):
        """After `test docker`, no runner completions are offered."""
        self.assertEqual(
            self.completions.complete_test("u", "test docker u", 0, 14),
            [])
