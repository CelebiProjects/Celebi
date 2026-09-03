"""Test the refresh-filelists CLI command surface."""
import unittest
from unittest import mock

from click.testing import CliRunner


class TestRefreshFilelistsCommand(unittest.TestCase):

    """Test Refresh Filelists Command."""

    def test_refresh_filelists_command_invokes_shell_function(self):
        """refresh-filelists forwards to the shell refresh_filelists."""
        from CelebiChrono.celebi_cli.commands.execution_management import (
            refresh_filelists_command)
        with mock.patch(
            "CelebiChrono.interface.shell.refresh_filelists"
        ) as fn:
            fn.return_value = mock.Mock(messages=[])
            result = CliRunner().invoke(refresh_filelists_command, [])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with()

    def test_refresh_filelists_command_is_registered(self):
        """refresh-filelists is a registered subcommand of the CLI."""
        from CelebiChrono.celebi_cli.cli import cli
        names = [cmd.name for cmd in cli.commands.values()]
        self.assertIn("refresh-filelists", names)
