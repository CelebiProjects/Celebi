"""Tests for the celebi-cli workaround-vre command."""
from unittest import mock

from click.testing import CliRunner

from CelebiChrono.celebi_cli.commands import file_operations as file_cmd


def test_workaround_vre_command_invokes_shell_with_default_pattern():
    with mock.patch(
        "CelebiChrono.interface.shell.workaround_vre"
    ) as shell_workaround_vre:
        result = CliRunner().invoke(file_cmd.workaround_vre_command, [])

    assert result.exit_code == 0, result.output
    shell_workaround_vre.assert_called_once_with("*")


def test_workaround_vre_command_forwards_pattern():
    with mock.patch(
        "CelebiChrono.interface.shell.workaround_vre"
    ) as shell_workaround_vre:
        result = CliRunner().invoke(
            file_cmd.workaround_vre_command, ["plots/*.png"])

    assert result.exit_code == 0, result.output
    shell_workaround_vre.assert_called_once_with("plots/*.png")


def test_shell_workaround_vre_forwards_to_current_object():
    from CelebiChrono.interface.shell_modules import file_operations

    current_object = mock.Mock()
    with mock.patch.object(file_operations.MANAGER, "current_object",
                           return_value=current_object):
        file_operations.workaround_vre("*.root")

    current_object.workaround_vre.assert_called_once_with("*.root")


def test_workaround_vre_command_is_registered_instead_of_export():
    from CelebiChrono.celebi_cli.cli import cli

    assert "workaround-vre" in cli.commands
    assert "export" not in cli.commands
