"""CLI preview/confirmation boundaries without touching real EOS."""
from unittest.mock import Mock
from click.testing import CliRunner
import pytest
from CelebiChrono.celebi_cli.commands import eos_cleanup as command
from CelebiChrono.kernel.chern_communicator import ChernCommunicator
from CelebiChrono.interface.shell_modules import communication

P, SCAN, PLAN = (c * 32 for c in 'abc')


@pytest.fixture
def client(monkeypatch):
    client = Mock()
    monkeypatch.setattr(ChernCommunicator, 'instance', lambda: client)
    monkeypatch.setattr(command, 'refresh_local_live', Mock())
    monkeypatch.setattr(communication, '_current_project', lambda: ('/project', P))
    client.eos_usage_status.return_value = {'id': SCAN, 'status': 'done',
                                           'report': {'projects': [{'project': P}]}}
    state = {'id': PLAN, 'status': 'planned', 'manifest_sha256': 'hash',
             'manifest': {'root': '/eos/test', 'projects': [P], 'clear_projects': [],
                          'entries': [{'project': P, 'bytes': 1024}], 'protected': [],
                          'skipped_unattributed': 0}}
    client.plan_eos_cleanup.return_value = state
    client.eos_cleanup_status.return_value = state
    client.execute_eos_cleanup.return_value = {**state, 'status': 'submitted'}
    return client


def test_default_is_only_preview(client):
    result = CliRunner().invoke(command.eos_cleanup_command, ['--scan-id', SCAN])
    assert result.exit_code == 0, result.output
    assert 'Preview only' in result.output
    client.execute_eos_cleanup.assert_not_called()
    client.plan_eos_cleanup.assert_called_once_with(SCAN, [P], False, ())


def test_cancel_confirmation_never_submits(client):
    result = CliRunner().invoke(command.eos_cleanup_command,
        ['--scan-id', SCAN, '--execute'], input='n\n')
    assert result.exit_code == 0, result.output
    client.execute_eos_cleanup.assert_not_called()


def test_unknown_and_clear_require_explicit_flags(client):
    result = CliRunner().invoke(command.eos_cleanup_command,
        ['--scan-id', SCAN, '--all-projects', '--include-unknown', '--clear-project', P])
    assert result.exit_code == 0, result.output
    client.plan_eos_cleanup.assert_called_once_with(SCAN, [P], True, (P,))
    client.execute_eos_cleanup.assert_not_called()


def test_existing_plan_execute_once_and_query_does_not_execute(client):
    result = CliRunner().invoke(command.eos_cleanup_command,
        ['--plan-id', PLAN, '--execute', '--yes', '--no-wait'])
    assert result.exit_code == 0, result.output
    client.execute_eos_cleanup.assert_called_once_with(PLAN, 'hash')
    client.execute_eos_cleanup.reset_mock()
    result = CliRunner().invoke(command.eos_cleanup_command, ['--plan-id', PLAN])
    assert result.exit_code == 0
    client.execute_eos_cleanup.assert_not_called()


def test_conflicting_options_and_yes_without_execute_rejected(client):
    for args in [['--scan-id', SCAN, '--yes'],
                 ['--plan-id', PLAN, '--include-unknown'],
                 ['cern', '--scan-id', SCAN],
                 ['--scan-id', SCAN, '--clear-project', 'd' * 32]]:
        assert CliRunner().invoke(command.eos_cleanup_command, args).exit_code != 0
    client.execute_eos_cleanup.assert_not_called()


def test_tidyup_reana_routes_to_eos_not_ssh(monkeypatch):
    from CelebiChrono.celebi_cli.commands import maintenance
    cleanup = Mock(return_value=True)
    monkeypatch.setattr(maintenance, '_cleanup_eos', cleanup)
    shell = Mock()
    assert maintenance._cleanup_runner_cache(shell, {'name': 'cern', 'backend_type': 'reana'})
    cleanup.assert_called_once_with('cern')
    shell.purge_stale_cache.assert_not_called()
