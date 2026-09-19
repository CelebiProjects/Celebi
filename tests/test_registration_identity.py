"""Registration synchronizes real local impressions with the server identity."""
from unittest.mock import MagicMock, patch

import pytest

from CelebiChrono.interface.shell_modules import object_creation
from CelebiChrono.kernel.chern_cache import ChernCache
from CelebiChrono.kernel.vobject import VObject
from CelebiChrono.kernel.vtask import create_rawdata_task
from CelebiChrono.kernel.vimpression import VImpression
from CelebiChrono.utils.metadata import ConfigFile, YamlFile


@pytest.mark.parametrize("status", ["immediate", "copying", "done"])
@pytest.mark.parametrize("in_task", [True, False])
def test_registration_refreshes_snapshot(tmp_path, monkeypatch, status, in_task):
    project = tmp_path / "project"
    config = ConfigFile(str(project / ".celebi/config.json"))
    config.write_variable("object_type", "project")
    config.write_variable("project_uuid", "project-id")
    (project / ".celebi/project.json").write_text("{}")
    monkeypatch.chdir(project)
    cache = ChernCache.instance()
    monkeypatch.setattr(cache, "project_path", "")
    monkeypatch.setattr(cache, "impression_consult_table", {})
    monkeypatch.setattr(cache, "project_modification_time", (None, -1))
    task_path = project / "Geo_root"
    create_rawdata_task(str(task_path), "Geo_root", "old-md5")
    task = VObject(str(task_path), str(project))
    task.impress()
    old_uuid = task.impression().uuid
    # Server's canonical rawdata snapshot after registering new data.
    canonical = tmp_path / "canonical"
    yaml = YamlFile(str(canonical / "celebi.yaml"))
    yaml.write_variable("environment", "rawdata")
    yaml.write_variable("uuid", "new-md5")
    yaml.write_variable("descriptor", "Geo_root")
    expected = VImpression.__new__(VImpression).generate_imp_uuid(
        "project-id", str(canonical), [])
    result = {"uuid": "new-md5", "impression_uuid": expected, "descriptor": "Geo_root"}
    cc = MagicMock()
    cc.register_remote_data.return_value = (
        {"result": result} if status == "immediate" else {"job_id": "job"})
    cc.register_remote_data_status.return_value = {"status": status, "result": result}
    current = task if in_task else VObject(str(project), str(project))
    with patch.object(object_creation, "MANAGER") as manager, \
            patch.object(object_creation, "ChernCommunicator") as communicator, \
            patch.object(object_creation, "tqdm"):
        manager.current_object.return_value = current
        communicator.instance.return_value = cc
        message = object_creation.register_ssh_data("cluster", "/cache/Geo_root")
    assert message.success, str(message)
    assert task.impression().uuid == expected
    assert expected != old_uuid
    assert task.is_impressed()
    assert YamlFile(str(task_path / "celebi.yaml")).read_variable("descriptor") == "Geo_root"


def test_snapshot_mismatch_is_reported(tmp_path):
    task = MagicMock()
    task.config_file.read_variable.return_value = "local-impression"
    with patch.object(object_creation, "VObject", return_value=task):
        message = object_creation._refresh_registered_impression(
            str(tmp_path), str(tmp_path), "server-impression")
    task.impress.assert_called_once()
    assert not message.success
    assert "local-impression" in str(message)
    assert "server-impression" in str(message)
