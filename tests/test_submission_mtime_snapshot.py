"""Project mtime snapshots used while preparing large submissions."""
import os
from unittest.mock import MagicMock, patch

from CelebiChrono.kernel.chern_cache import ChernCache
from CelebiChrono.kernel.chern_communicator import ChernCommunicator
from CelebiChrono.kernel.vobj_execution import ExecutionManagement
from CelebiChrono.utils import csys


def test_dir_mtime_ignores_existing_local_runtime_config(tmp_path):
    project = tmp_path / "project"
    local_config = project / "task/.celebi/config.local.json"
    local_config.parent.mkdir(parents=True)
    local_config.write_text('{"impression": "old"}', encoding="utf-8")
    source = project / "task/analysis.py"
    source.write_text("value = 1\n", encoding="utf-8")

    initial_mtime = csys.dir_mtime(str(project))
    future = initial_mtime + 100
    local_config.write_text('{"impression": "new"}', encoding="utf-8")
    os.utime(local_config, (future, future))

    assert csys.dir_mtime(str(project)) == initial_mtime


def test_dir_mtime_ignores_creation_of_local_runtime_config(tmp_path):
    """First-time runtime metadata must not invalidate a frozen snapshot."""
    project = tmp_path / "project"
    celebi_dir = project / "task/.celebi"
    celebi_dir.mkdir(parents=True)
    shared_config = celebi_dir / "config.json"
    shared_config.write_text('{"object_type": "task"}', encoding="utf-8")

    initial_mtime = csys.dir_mtime(str(project))
    local_config = celebi_dir / "config.local.json"
    local_config.write_text('{"impression": "new"}', encoding="utf-8")
    future = initial_mtime + 100
    os.utime(celebi_dir, (future, future))
    os.utime(local_config, (future, future))

    assert csys.dir_mtime(str(project)) == initial_mtime


def test_dir_mtime_tracks_shared_project_content(tmp_path):
    project = tmp_path / "project"
    shared_config = project / "task/.celebi/config.json"
    shared_config.parent.mkdir(parents=True)
    shared_config.write_text('{"object_type": "task"}', encoding="utf-8")

    initial_mtime = csys.dir_mtime(str(project))
    future = initial_mtime + 100
    shared_config.write_text(
        '{"object_type": "task", "predecessors": ["input"]}',
        encoding="utf-8",
    )
    os.utime(shared_config, (future, future))

    assert csys.dir_mtime(str(project)) == future


def test_submission_snapshot_freezes_and_then_invalidates_cache(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "analysis.py").write_text("value = 1\n", encoding="utf-8")
    cache = ChernCache()

    with cache.freeze_project_modification_time(str(project)) as initial_mtime:
        assert initial_mtime == csys.dir_mtime(str(project))
        assert cache.project_modification_time == (initial_mtime, float("inf"))

    assert cache.project_modification_time == (None, -1)


def test_submit_stops_before_execute_when_project_changes(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    source = project / "analysis.py"
    source.write_text("value = 1\n", encoding="utf-8")
    initial_mtime = csys.dir_mtime(str(project))

    obj = MagicMock(spec=ExecutionManagement)
    obj.path = str(project / "task")
    obj.project_path.return_value = str(project)
    obj.is_algorithm.return_value = False
    obj.is_task_or_algorithm.return_value = True
    obj.is_task.return_value = True
    obj.get_vtask.return_value.default_runner.return_value = "local"
    obj.sub_objects_recursively.return_value = []
    obj.get_impressions.return_value = ["impression"]

    def change_project(_consult_id):
        source.write_text("value = 2\n", encoding="utf-8")
        future = initial_mtime + 100
        os.utime(source, (future, future))

    obj.deposit.side_effect = change_project
    communicator = MagicMock()
    communicator.dite_status.return_value = "connected"

    with patch.object(ChernCommunicator, "instance", return_value=communicator):
        message = ExecutionManagement.submit(obj, "local")

    assert "Project files changed" in str(message)
    communicator.execute.assert_not_called()
