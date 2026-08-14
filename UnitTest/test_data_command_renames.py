"""Tests that the renamed data commands exist and old names are gone."""
import unittest
from unittest import mock

from click.testing import CliRunner


class TestDataCommandRenames(unittest.TestCase):

    def test_upload_data_command_exists(self):
        from CelebiChrono.celebi_cli.commands.file_operations import (
            upload_data_command)
        with mock.patch("CelebiChrono.interface.shell.upload_data") as fn:
            result = CliRunner().invoke(upload_data_command, ["/data/dir"])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("/data/dir")

    def test_attach_data_command_exists(self):
        from CelebiChrono.celebi_cli.commands.object_creation import (
            attach_data_command)
        with mock.patch("CelebiChrono.interface.shell.attach_data") as fn:
            result = CliRunner().invoke(attach_data_command, ["imp-uuid"])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("imp-uuid", "")

    def test_old_cli_names_removed(self):
        from CelebiChrono.celebi_cli.cli import cli
        result = CliRunner().invoke(cli, ["send", "/x"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("No such command", result.output)
        result = CliRunner().invoke(cli, ["use-data", "uuid"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("No such command", result.output)

    def test_chern_shell_renames(self):
        from CelebiChrono.interface.chern_shell.commands_advanced import (
            AdvancedCommands)
        from CelebiChrono.interface.chern_shell.commands_task import (
            TaskCommands)
        from CelebiChrono.interface.chern_shell import commands_advanced
        from CelebiChrono.interface.chern_shell import commands_task
        adv = AdvancedCommands.__new__(AdvancedCommands)
        task_cmds = TaskCommands.__new__(TaskCommands)
        with mock.patch.object(commands_advanced, "shell") as shell:
            shell.upload_data.return_value = mock.MagicMock(messages=[])
            adv.do_upload_data("/data/dir")
            shell.upload_data.assert_called_once_with("/data/dir")
        with mock.patch.object(commands_task, "shell") as shell:
            shell.attach_data.return_value = mock.MagicMock(messages=[])
            task_cmds.do_attach_data("imp-uuid")
            shell.attach_data.assert_called_once_with("imp-uuid", "")
