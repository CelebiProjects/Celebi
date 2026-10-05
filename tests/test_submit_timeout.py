"""Submission response timeouts propagate without changing other requests."""
from unittest.mock import MagicMock, patch

import pytest
import requests
from click.testing import CliRunner

from CelebiChrono.celebi_cli.cli import cli
from CelebiChrono.kernel.chern_communicator import ChernCommunicator
from CelebiChrono.kernel.chern_communicator import SubmissionError
from CelebiChrono.kernel.vobj_execution import ExecutionManagement
from CelebiChrono.interface.shell_modules import execution_management as shell


@pytest.mark.parametrize('timeout, expected', [(None, 10), (300, 300)])
def test_submit_timeout_reaches_http_request(timeout, expected):
    communicator = object.__new__(ChernCommunicator)
    communicator.timeout = 10
    communicator.project_uuid = 'project'
    communicator.serverurl = lambda: 'localhost:3315'
    obj = MagicMock(spec=ExecutionManagement)
    obj.path = "task"
    obj.is_algorithm.return_value = False
    obj.is_task_or_algorithm.return_value = True
    obj.is_task.return_value = True
    obj.get_vtask.return_value.default_runner.return_value = 'local'
    obj.sub_objects_recursively.return_value = []
    obj.get_impressions.return_value = ['impression']
    obj.submit.side_effect = lambda runner, **kw: ExecutionManagement.submit(obj, runner, **kw)
    args = ['submit'] + ([] if timeout is None else ['--timeout', str(timeout)])
    with patch.object(shell.MANAGER, 'current_object', return_value=obj), \
         patch.object(ChernCommunicator, 'instance', return_value=communicator), \
         patch.object(communicator, 'dite_status', return_value='connected'), \
         patch('CelebiChrono.kernel.chern_communicator.requests.get') as get, \
         patch('CelebiChrono.kernel.chern_communicator.requests.post') as post:
        get.return_value.text = 'machine'
        result = CliRunner().invoke(cli, args)
    assert result.exit_code == 0, result.output
    assert 'submitted' in result.output
    assert post.call_args.kwargs['timeout'] == expected
    if timeout is None:
        assert 'timeout' not in post.call_args.kwargs['data']
    else:
        assert post.call_args.kwargs['data']['timeout'] == timeout
    assert get.call_args.kwargs['timeout'] == 10
    assert communicator.timeout == 10


@pytest.mark.parametrize('value', ['0', '-1', 'abc', '1.5'])
def test_invalid_timeout_does_not_submit(value):
    with patch('CelebiChrono.interface.shell.submit') as submit:
        result = CliRunner().invoke(cli, ['submit', '--timeout', value])
    assert result.exit_code == 2
    submit.assert_not_called()


def test_batch_submit_timeout():
    obj = MagicMock(spec=ExecutionManagement)
    task = MagicMock()
    task.is_algorithm.return_value = False
    task.is_task.return_value = True
    task.default_runner.return_value = 'cluster'
    task.impression.return_value.uuid = 'impression'
    obj.get_vtask.return_value = task
    obj.submit_objects.side_effect = lambda objects, runner, **kw: (
        ExecutionManagement.submit_objects(obj, objects, runner, **kw)
    )
    with patch.object(shell.MANAGER, 'current_object', return_value=obj), \
         patch.object(shell.MANAGER, 'sub_object', return_value=task), \
         patch.object(ChernCommunicator, 'instance') as instance:
        instance.return_value.dite_status.return_value = 'connected'
        shell.submit_objects(['task'], 'cluster', timeout=300)
    assert instance.return_value.execute.call_args.kwargs['timeout'] == 300


def test_timeout_does_not_report_success_or_retry():
    with patch('CelebiChrono.interface.shell.submit', side_effect=requests.Timeout('timed out')) as submit:
        result = CliRunner().invoke(cli, ['submit', '--timeout', '300'])
    assert 'timed out' in result.output
    assert 'submitted' not in result.output
    submit.assert_called_once()


def _response(status_code, payload=None, text=''):
    response = MagicMock(status_code=status_code, text=text)
    response.json.return_value = payload
    return response


def test_execute_waits_for_scheduled_submission():
    communicator = object.__new__(ChernCommunicator)
    communicator.timeout = 10
    communicator.transfer_timeout = 600
    communicator.project_uuid = 'project'
    communicator.serverurl = lambda: 'localhost:3315'
    machine = _response(200, text='runner-id')
    accepted = _response(202, {'submission_id': 'sub-1', 'status': 'accepted'})
    building = _response(200, {'submission_id': 'sub-1', 'status': 'building'})
    scheduled = _response(200, {
        'submission_id': 'sub-1', 'status': 'scheduled', 'workflow_id': 'wf-1'})

    with patch('CelebiChrono.kernel.chern_communicator.requests.get',
               side_effect=[machine, building, scheduled]), \
         patch('CelebiChrono.kernel.chern_communicator.requests.post',
               return_value=accepted), \
         patch('CelebiChrono.kernel.chern_communicator.time.sleep'):
        result = communicator.execute(['imp'], {'imp': False}, 'cluster')

    assert result['status'] == 'scheduled'
    assert result['workflow_id'] == 'wf-1'


def test_execute_raises_on_blocked_submission():
    communicator = object.__new__(ChernCommunicator)
    communicator.timeout = 10
    communicator.transfer_timeout = 600
    communicator.project_uuid = 'project'
    communicator.serverurl = lambda: 'localhost:3315'
    machine = _response(200, text='runner-id')
    accepted = _response(202, {'submission_id': 'sub-1', 'status': 'accepted'})
    blocked = _response(200, {
        'submission_id': 'sub-1', 'status': 'blocked',
        'error': 'Jobs already belong to active workflows',
        'conflicts': {'upstream': 'wf-existing'},
    })

    with patch('CelebiChrono.kernel.chern_communicator.requests.get',
               side_effect=[machine, blocked]), \
         patch('CelebiChrono.kernel.chern_communicator.requests.post',
               return_value=accepted), \
         pytest.raises(SubmissionError, match='wf-existing'):
        communicator.execute(['imp'], {'imp': False}, 'cluster')


def test_execute_raises_when_dispatch_is_rejected():
    communicator = object.__new__(ChernCommunicator)
    communicator.timeout = 10
    communicator.transfer_timeout = 600
    communicator.project_uuid = 'project'
    communicator.serverurl = lambda: 'localhost:3315'
    machine = _response(200, text='runner-id')
    rejected = _response(503, {
        'submission_id': 'sub-1', 'status': 'failed',
        'error': 'Failed to dispatch submission: broker unavailable',
    })

    with patch('CelebiChrono.kernel.chern_communicator.requests.get',
               return_value=machine), \
         patch('CelebiChrono.kernel.chern_communicator.requests.post',
               return_value=rejected), \
         pytest.raises(SubmissionError, match='broker unavailable'):
        communicator.execute(['imp'], {'imp': False}, 'cluster')


def test_execute_accepts_synchronous_deduplication():
    """A duplicate active workflow is a successful terminal submission result."""
    communicator = object.__new__(ChernCommunicator)
    communicator.timeout = 10
    communicator.transfer_timeout = 600
    communicator.project_uuid = 'project'
    communicator.serverurl = lambda: 'localhost:3315'
    machine = _response(200, text='runner-id')
    deduplicated = _response(200, {
        'submission_id': 'sub-1', 'status': 'deduplicated',
        'workflow_id': 'wf-existing', 'deduplicated': True,
    })

    with patch('CelebiChrono.kernel.chern_communicator.requests.get',
               return_value=machine), \
         patch('CelebiChrono.kernel.chern_communicator.requests.post',
               return_value=deduplicated):
        result = communicator.execute(['imp'], {'imp': False}, 'cluster')

    assert result['status'] == 'deduplicated'
    assert result['workflow_id'] == 'wf-existing'
