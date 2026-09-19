"""Registration preserves task descriptors across every successful response."""
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest

from CelebiChrono.interface.shell_modules import object_creation
from CelebiChrono.utils.metadata import YamlFile


@pytest.mark.parametrize("status", ["immediate", "copying", "done"])
@pytest.mark.parametrize("existing, override, expected", [
    ("My dataset", "", "My dataset"),
    ("My dataset", "Explicit name", "Explicit name"),
    ("", "", "remote-directory"),
])
def test_registration_descriptor(tmp_path, status, existing, override, expected):
    yaml = YamlFile(str(tmp_path / "celebi.yaml"))
    yaml.write_variable("environment", "rawdata")
    yaml.write_variable("descriptor", existing)
    yaml.write_variable("uuid", "old-md5")
    current = MagicMock(path=str(tmp_path))
    current.object_type.return_value = "task"
    current.project_path.return_value = "/proj"
    current.project_uuid.return_value = "project-id"
    result = {"uuid": "new-md5", "impression_uuid": "impression-id",
              "descriptor": "remote-directory"}
    cc = MagicMock()
    cc.register_remote_data.return_value = (
        {"result": result} if status == "immediate" else {"job_id": "job-id"})
    cc.register_remote_data_status.return_value = {"status": status, "result": result}

    with patch.object(object_creation, "MANAGER") as manager, \
            patch.object(object_creation, "ChernCommunicator") as communicator, \
            patch.object(object_creation, "tqdm"):
        manager.current_object.return_value = current
        communicator.instance.return_value = cc
        object_creation.register_ssh_data("pkufarm212", "/cache/remote-directory", override)

    cc.register_remote_data.assert_called_once_with(
        "pkufarm212", "/cache/remote-directory", "project-id", override or existing or None)
    saved = YamlFile(str(tmp_path / "celebi.yaml"))
    assert saved.read_variable("descriptor", "") == expected
    assert saved.read_variable("uuid", "") == "new-md5"
    current.set_default_runner.assert_called_once_with("pkufarm212")


@pytest.fixture(autouse=True)
def mock_registration_snapshot():
    """Snapshot behavior is covered with real tasks in the identity tests."""
    from CelebiChrono.utils.message import Message
    with mock.patch.object(object_creation, "_refresh_registered_impression",
                           return_value=Message()):
        yield
