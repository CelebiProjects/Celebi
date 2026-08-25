"""Tests for celebi-cli transfer command."""
from unittest import mock

from click.testing import CliRunner

from CelebiChrono.celebi_cli.commands import file_operations as file_cmd


def test_transfer_command_invokes_shell():
    with mock.patch("CelebiChrono.interface.shell.transfer") as shell_transfer:
        shell_transfer.return_value = mock.MagicMock()
        shell_transfer.return_value.messages = []
        result = CliRunner().invoke(file_cmd.transfer_command,
                                    ["yuki", "runner:pkufarm",
                                     "--pattern", "*.txt"])
        assert result.exit_code == 0, result.output
        shell_transfer.assert_called_once_with("yuki", "runner:pkufarm",
                                               pattern="*.txt", force=False)
