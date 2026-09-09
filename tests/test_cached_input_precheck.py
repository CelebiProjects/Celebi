"""Runner-cached inputs must still pass the upstream readiness check."""
from unittest import mock

import pytest

from CelebiChrono.kernel.vtask_job import JobManager


@pytest.mark.parametrize("status", ["unsubmitted", "running", "failed"])
@pytest.mark.parametrize("cached", [True, False])
def test_incomplete_input_is_rejected_even_when_cached(status, cached):
    pre = mock.Mock()
    pre.is_impressed_fast.return_value = True
    pre.impression.return_value.uuid = "input-uuid"
    pre.run_status.return_value = status
    task = mock.Mock()
    task.inputs.return_value = [pre]
    communicator = mock.Mock()

    ok, message = JobManager._check_preceding_jobs(
        task, communicator, {"input-uuid"} if cached else set())

    assert not ok
    assert "is not finished" in message
    pre.run_status.assert_called_once_with()
    communicator.collect_outputs.assert_not_called()


def test_cached_input_still_requires_current_impression():
    pre = mock.Mock()
    pre.is_impressed_fast.return_value = False
    pre.impression.return_value.uuid = "input-uuid"
    task = mock.Mock()
    task.inputs.return_value = [pre]
    communicator = mock.Mock()

    ok, message = JobManager._check_preceding_jobs(
        task, communicator, {"input-uuid"})

    assert not ok
    assert "is not impressed" in message
    pre.run_status.assert_not_called()
    communicator.collect_outputs.assert_not_called()
