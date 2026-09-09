"""Registration polling tolerates temporary DITE connection failures."""
from unittest.mock import MagicMock, patch

import pytest
import requests

from CelebiChrono.interface.shell_modules import object_creation
from CelebiChrono.utils.message import Message


@pytest.fixture
def registration():
    current = MagicMock()
    current.object_type.return_value = "project"
    current.project_path.return_value = "/project"
    cc = MagicMock()
    cc.register_remote_data.return_value = {"job_id": "full-registration-job-id"}
    with patch.object(object_creation, "MANAGER") as manager, \
            patch.object(object_creation, "ChernCommunicator") as communicator, \
            patch.object(object_creation, "tqdm") as progress, \
            patch.object(object_creation.time, "sleep"), \
            patch.object(object_creation, "_fill_registered_data",
                         return_value=Message()) as fill:
        manager.current_object.return_value = current
        communicator.instance.return_value = cc
        yield cc, fill, progress.return_value


def timeout_error():
    """Use the exception wrapping performed by the communicator."""
    error = ConnectionError("Failed to connect to DITE server: read timed out")
    error.__cause__ = requests.exceptions.ReadTimeout("read timed out")
    return error


@pytest.mark.parametrize("status", ["done", "copying"])
def test_recovers_and_resets_failure_count(registration, status):
    cc, fill, progress = registration
    cc.register_remote_data_status.side_effect = (
        [timeout_error() for _ in range(9)]
        + [{"status": "hashing"}]
        + [timeout_error() for _ in range(9)]
        + [{"status": status, "result": {
            "uuid": "data-md5", "impression_uuid": "impression", "descriptor": "data"}}]
    )

    message = object_creation.register_ssh_data("cluster", "/data")

    assert message.success
    fill.assert_called_once()
    cc.register_remote_data.assert_called_once()
    assert all(call.args == ("full-registration-job-id",)
               for call in cc.register_remote_data_status.call_args_list)
    progress.close.assert_called_once()


def test_persistent_failure_preserves_job_id_without_filling_task(registration):
    cc, fill, progress = registration
    cc.register_remote_data_status.side_effect = timeout_error()

    message = object_creation.register_ssh_data("cluster", "/data")

    assert not message.success
    assert "full-registration-job-id" in str(message)
    assert "may still be running" in str(message)
    assert cc.register_remote_data_status.call_count == 10
    cc.register_remote_data.assert_called_once()
    fill.assert_not_called()
    progress.close.assert_called_once()


def test_server_failure_after_connection_recovery_is_reported(registration):
    cc, fill, progress = registration
    cc.register_remote_data_status.side_effect = [
        timeout_error(), {"status": "failed", "error": "remote directory missing"}]

    message = object_creation.register_ssh_data("cluster", "/data")

    assert not message.success
    assert "remote directory missing" in str(message)
    fill.assert_not_called()
    progress.close.assert_called_once()
