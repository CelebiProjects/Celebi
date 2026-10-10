"""Test the explicit failed-stageout collection CLI surface."""
from unittest import mock

from click.testing import CliRunner


def test_collect_allow_failed_is_forwarded():
    """collect --allow-failed all reaches the shell as an explicit opt-in."""
    from CelebiChrono.celebi_cli.commands.execution_management import (
        collect_command,
    )
    with mock.patch("CelebiChrono.interface.shell.collect") as collect:
        collect.return_value = mock.Mock(messages=[])
        result = CliRunner().invoke(
            collect_command, ["--allow-failed", "all"])

    assert result.exit_code == 0, result.output
    collect.assert_called_once_with("all", allow_failed=True)
