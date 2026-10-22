"""Submission response timeouts propagate without changing other requests."""
from unittest.mock import MagicMock, patch

import pytest
import requests
from click.testing import CliRunner

from CelebiChrono.celebi_cli.cli import cli
from CelebiChrono.kernel.chern_communicator import ChernCommunicator
from CelebiChrono.kernel.chern_communicator import SubmissionError
from CelebiChrono.kernel.vobj_execution import ExecutionManagement
from CelebiChrono.kernel.vobj_execution import _submission_level, _submission_message
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
    assert not result.exit_code, result.output
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


def test_cli_submit_uses_runner_option():
    """The CLI and interactive shell use the same --runner spelling."""
    with patch('CelebiChrono.interface.shell.submit') as submit:
        result = CliRunner().invoke(
            cli, ['submit', '--runner', 'ihep'])
    assert not result.exit_code, result.output
    submit.assert_called_once_with(
        'ihep', timeout=None, with_unknown=False)


def test_cli_submit_rejects_positional_runner():
    """The former positional runner syntax is no longer ambiguous."""
    with patch('CelebiChrono.interface.shell.submit') as submit:
        result = CliRunner().invoke(cli, ['submit', 'ihep'])
    assert result.exit_code == 2
    assert 'unexpected extra argument' in result.output.lower()
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


def test_batch_submit_deduplicates_identical_impressions(tmp_path):
    """A repeated content-addressed task is sent to Yuki only once."""
    obj = MagicMock(spec=ExecutionManagement)
    task = MagicMock()
    task.is_algorithm.return_value = False
    task.is_task.return_value = True
    task.default_runner.return_value = 'cluster'
    task.impression.return_value.uuid = 'same-impression'
    obj.get_vtask.return_value = task
    obj.project_path.return_value = str(tmp_path)
    obj.sub_objects_recursively.return_value = []

    with patch.object(ChernCommunicator, 'instance') as instance:
        instance.return_value.dite_status.return_value = 'connected'
        ExecutionManagement.submit_objects(
            obj, [task, task], 'cluster')

    impressions, cache_on_runner, _runner = \
        instance.return_value.execute.call_args.args[:3]
    assert impressions == ['same-impression']
    assert cache_on_runner == {'same-impression': task.cache_on_runner()}


def test_cli_submit_forwards_with_unknown():
    """The CLI opt-in reaches Yuki without changing ordinary submissions."""
    obj = MagicMock(spec=ExecutionManagement)
    obj.path = "task"
    obj.is_algorithm.return_value = False
    obj.is_task_or_algorithm.return_value = True
    obj.is_task.return_value = True
    obj.get_vtask.return_value.default_runner.return_value = 'local'
    obj.sub_objects_recursively.return_value = []
    obj.get_impressions.return_value = ['impression']
    obj.submit.side_effect = lambda runner, **kw: ExecutionManagement.submit(
        obj, runner, **kw)
    with patch.object(shell.MANAGER, 'current_object', return_value=obj), \
         patch.object(ChernCommunicator, 'instance') as instance:
        instance.return_value.dite_status.return_value = 'connected'
        instance.return_value.execute.return_value = {
            'status': 'deduplicated', 'submission_reason': 'unknown',
            'workflow_id': 'wf-unknown', 'workflow_status': 'unknown'}
        result = CliRunner().invoke(cli, ['submit', '--with-unknown'])
    assert result.exit_code == 0, result.output
    assert 'still unknown' in result.output
    assert instance.return_value.execute.call_args.kwargs['with_unknown'] is True


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


def test_execute_sends_with_unknown_opt_in():
    """The communicator sends the opt-in only when explicitly requested."""
    communicator = object.__new__(ChernCommunicator)
    communicator.timeout = 10
    communicator.transfer_timeout = 600
    communicator.project_uuid = 'project'
    communicator.serverurl = lambda: 'localhost:3315'
    machine = _response(200, text='runner-id')
    deduplicated = _response(200, {
        'submission_id': 'sub-1', 'status': 'deduplicated',
        'submission_reason': 'unknown', 'workflow_id': 'wf-unknown',
    })

    with patch('CelebiChrono.kernel.chern_communicator.requests.get',
               return_value=machine), \
         patch('CelebiChrono.kernel.chern_communicator.requests.post',
               return_value=deduplicated) as post:
        communicator.execute(
            ['imp'], {'imp': False}, 'cluster', with_unknown=True)

    assert post.call_args.kwargs['data']['with_unknown'] == 'true'


@pytest.mark.parametrize('submission, expected', [
    ({'status': 'deduplicated', 'submission_reason': 'active',
      'workflow_id': 'wf-running', 'workflow_status': 'unknown'},
     'Workflow wf-running is already active (unknown)'),
    ({'status': 'deduplicated', 'submission_reason': 'completed',
      'workflow_id': 'wf-finished', 'workflow_status': 'finished'},
     'Workflow wf-finished is already complete (finished)'),
    ({'status': 'scheduled', 'submission_reason': 'replacement',
      'workflow_id': 'wf-new',
      'previous_workflows': {
          'imp': {'workflow_id': 'wf-old', 'job_status': 'failed'}}},
     'Previous workflow wf-old (failed) was replaced by workflow wf-new'),
    ({'status': 'scheduled', 'workflow_id': 'wf-new'},
     'Created workflow wf-new'),
    ({'status': 'deduplicated', 'submission_reason': 'unknown',
      'workflow_id': 'wf-unknown', 'workflow_status': 'unknown'},
     'Workflow wf-unknown is still unknown after a status refresh'),
    ({'status': 'deduplicated', 'submission_reason': 'refresh_failed',
      'workflow_id': 'wf-unknown', 'workflow_status': 'unknown',
      'refresh_error': 'SSH unavailable'},
     'Could not refresh unknown workflow wf-unknown'),
])
def test_submit_result_message_distinguishes_workflow_action(submission, expected):
    """The submit response tells users whether work was created or reused."""
    assert expected in _submission_message(['imp'], 'cluster', submission)


def test_inconclusive_unknown_refresh_is_a_warning():
    """No-submit outcomes must not look like successful submission notices."""
    assert _submission_level({'submission_reason': 'unknown'}) == 'warning'
    assert _submission_level({'submission_reason': 'refresh_failed'}) == 'warning'
    assert _submission_level({'submission_reason': 'replacement'}) == 'info'
