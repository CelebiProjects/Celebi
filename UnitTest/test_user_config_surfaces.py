"""Tests for the `user-config` wiring on the shell and CLI surfaces."""
import unittest
from unittest import mock

from click.testing import CliRunner

from CelebiChrono.celebi_cli import cli as cli_module
from CelebiChrono.celebi_cli.commands import task_configuration as cli_task_config
from CelebiChrono.interface import shell
from CelebiChrono.interface.chern_shell import commands_environment
from CelebiChrono.interface.chern_shell.commands_environment import (
    EnvironmentCommands)


def _message(text="ok"):
    """A Message stand-in with a colored() renderer."""
    msg = mock.MagicMock()
    msg.messages = [(text, "normal")]
    msg.colored.return_value = "rendered"
    return msg


class TestShellFacade(unittest.TestCase):

    """The shell.py facade must re-export the function."""

    def test_shell_exports_user_config(self):
        """Both surfaces import user_config from the facade."""
        self.assertTrue(callable(shell.user_config))


class TestShellCommand(unittest.TestCase):

    """The interactive-shell surface."""

    def setUp(self):
        """Build the mixin without running shell __init__."""
        self.cmds = EnvironmentCommands.__new__(EnvironmentCommands)

    def test_do_user_config_calls_shell_function(self):
        """Bare `user-config` delegates to the shell function."""
        with mock.patch.object(commands_environment, "shell") as sh, \
                mock.patch("builtins.print") as pr:
            sh.user_config.return_value = _message()
            self.cmds.do_user_config("")
        sh.user_config.assert_called_once_with(list_only=False)
        self.assertTrue(pr.called)

    def test_do_user_config_list_flag(self):
        """`user-config --list` requests the read-only listing."""
        with mock.patch.object(commands_environment, "shell") as sh, \
                mock.patch("builtins.print"):
            sh.user_config.return_value = _message()
            self.cmds.do_user_config("--list")
        sh.user_config.assert_called_once_with(list_only=True)

    def test_do_user_config_short_list_flag(self):
        """`-l` is accepted as a shorthand for --list."""
        with mock.patch.object(commands_environment, "shell") as sh, \
                mock.patch("builtins.print"):
            sh.user_config.return_value = _message()
            self.cmds.do_user_config("-l")
        sh.user_config.assert_called_once_with(list_only=True)

    def test_do_user_config_rejects_unknown_argument(self):
        """An unknown argument prints usage and runs nothing."""
        with mock.patch.object(commands_environment, "shell") as sh, \
                mock.patch("builtins.print") as pr:
            self.cmds.do_user_config("--nope")
        sh.user_config.assert_not_called()
        self.assertTrue(pr.called)

    def test_do_config_still_edits_the_object(self):
        """The existing object-scoped `config` command is untouched."""
        with mock.patch.object(commands_environment, "shell") as sh, \
                mock.patch("builtins.print"):
            sh.config.return_value = _message()
            self.cmds.do_config("")
        sh.config.assert_called_once_with()
        sh.user_config.assert_not_called()


class TestCliCommand(unittest.TestCase):

    """The celebi-cli surface."""

    def test_command_is_registered_on_the_group(self):
        """`celebi-cli user-config` resolves to a command."""
        self.assertIn("user-config", cli_module.cli.commands)

    def test_cli_invokes_shell_function(self):
        """The click command calls through to the shell function."""
        with mock.patch.object(
            shell, "user_config", return_value=_message()
        ) as uc:
            result = CliRunner().invoke(
                cli_task_config.user_config_command, []
            )
        self.assertEqual(result.exit_code, 0)
        uc.assert_called_once_with(list_only=False)

    def test_cli_list_flag(self):
        """`--list` is forwarded to the shell function."""
        with mock.patch.object(
            shell, "user_config", return_value=_message()
        ) as uc:
            result = CliRunner().invoke(
                cli_task_config.user_config_command, ["--list"]
            )
        self.assertEqual(result.exit_code, 0)
        uc.assert_called_once_with(list_only=True)


if __name__ == "__main__":
    unittest.main()
