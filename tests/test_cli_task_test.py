"""CLI task tests dispatch to the selected execution backend."""
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from CelebiChrono.celebi_cli.cli import cli
from CelebiChrono.interface.shell_modules import execution_management as shell


@pytest.mark.parametrize('args', [['test'], ['test', 'docker']])
def test_docker_default_and_explicit(args):
    task = MagicMock()
    task.docker_test.return_value = 'Docker completed'
    with patch.object(shell.MANAGER, 'current_object', return_value=task):
        result = CliRunner().invoke(cli, args)
    assert result.exit_code == 0, result.output
    assert 'Docker completed' in result.output
    task.docker_test.assert_called_once_with()
    task.ssh_test.assert_not_called()


def test_ssh_runner_reaches_task():
    task = MagicMock()
    task.ssh_test.return_value = 'Remote test completed'
    with patch.object(shell.MANAGER, 'current_object', return_value=task):
        result = CliRunner().invoke(cli, ['test', 'ssh', 'pkufarm212'])
    assert result.exit_code == 0, result.output
    assert 'Remote test completed' in result.output
    task.ssh_test.assert_called_once_with('pkufarm212')
    task.docker_test.assert_not_called()


@pytest.mark.parametrize('args', [
    ['test', 'ssh'], ['test', 'docker', 'pkufarm212'],
    ['test', 'unknown'], ['test', 'ssh', 'pkufarm212', 'extra'],
])
def test_invalid_arguments_do_not_execute(args):
    with patch.object(shell.MANAGER, 'current_object') as current:
        result = CliRunner().invoke(cli, args)
    assert result.exit_code == 2, result.output
    current.assert_not_called()


def test_ssh_error_is_reported():
    task = MagicMock()
    task.ssh_test.side_effect = RuntimeError('connection failed')
    with patch.object(shell.MANAGER, 'current_object', return_value=task):
        result = CliRunner().invoke(cli, ['test', 'ssh', 'pkufarm212'])
    assert result.exit_code == 1, result.output
    assert 'connection failed' in result.output


def test_help_describes_ssh():
    result = CliRunner().invoke(cli, ['test', '--help'])
    assert result.exit_code == 0
    assert 'pkufarm212' in result.output
