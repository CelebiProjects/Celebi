"""CLI orchestration: no implicit resubmission, machine-readable reporting."""
from unittest.mock import Mock
from click.testing import CliRunner
import pytest
from CelebiChrono.celebi_cli.commands.eos_usage import eos_usage_command
from CelebiChrono.kernel.chern_communicator import ChernCommunicator
from CelebiChrono.interface.shell_modules import communication


@pytest.fixture
def communicator(monkeypatch):
    client = Mock()
    monkeypatch.setattr(ChernCommunicator, 'instance', lambda: client)
    monkeypatch.setattr(communication, '_current_project', lambda: (None, ''))
    return client


def test_all_projects_starts_one_scan(communicator):
    communicator.start_eos_usage.return_value = {'id': 'a' * 32, 'status': 'submitted'}
    result = CliRunner().invoke(eos_usage_command, ['cern', '--all-projects', '--no-wait'])
    assert result.exit_code == 0, result.output
    communicator.start_eos_usage.assert_called_once()
    assert communicator.start_eos_usage.call_args.args[2] is None
    assert 'Resume:' in result.output


def test_existing_scan_never_submits(communicator):
    communicator.eos_usage_status.return_value = {'id': 'a' * 32, 'status': 'done'}
    result = CliRunner().invoke(eos_usage_command, ['--scan-id', 'a' * 32, '--json'])
    assert result.exit_code == 0, result.output
    assert '"status": "done"' in result.output
    communicator.start_eos_usage.assert_not_called()


def test_requires_scope_and_exclusive_options(communicator):
    for args in [[], ['cern'], ['cern', '--scan-id', 'a' * 32]]:
        result = CliRunner().invoke(eos_usage_command, args)
        assert result.exit_code != 0
    communicator.start_eos_usage.assert_not_called()


def test_timeout_retains_scan(monkeypatch, communicator):
    communicator.eos_usage_status.return_value = {'id': 'a' * 32, 'status': 'running'}
    times = iter([0, 2])
    monkeypatch.setattr('CelebiChrono.celebi_cli.commands.eos_usage.time.monotonic', lambda: next(times))
    result = CliRunner().invoke(eos_usage_command, ['--scan-id', 'a' * 32, '--timeout', '1'])
    assert result.exit_code == 0 and 'Still pending' in result.output
    communicator.start_eos_usage.assert_not_called()
