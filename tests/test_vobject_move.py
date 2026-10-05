"""Moving working objects does not require or create impressions."""

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from CelebiChrono.interface.shell_modules.file_operations import mv
from CelebiChrono.kernel.chern_cache import ChernCache
from CelebiChrono.kernel.vobject import VObject


@pytest.mark.parametrize("source", ["tasks/taskGen", "tasks"])
@pytest.mark.parametrize("has_history", [False, True])
def test_move_preserves_working_files_history_and_dependencies(
    tmp_path, monkeypatch, source, has_history
):
    fixture = Path(__file__).parents[1] / "UnitTest/data/demo_complex"
    project = tmp_path / "project"
    shutil.copytree(fixture, project)
    monkeypatch.chdir(project)
    cache = ChernCache.instance()
    monkeypatch.setattr(cache, "project_path", str(project))
    monkeypatch.setattr(cache, "project_modification_time", (None, -1))
    monkeypatch.setattr(cache, "generic_cache", {})

    producer = VObject(str(project / "tasks/taskGen"), str(project))
    if not has_history:
        for obj in VObject(str(project), str(project)).sub_objects_recursively():
            if obj.is_task_or_algorithm():
                obj.clean_impressions()
    old_impression = producer.config_file.read_variable("impression", "")
    old_history = producer.config_file.read_variable("impressions", [])
    working_file = project / "tasks/taskGen/unfinished.txt"
    working_file.write_text("unsnapshotted changes\n", encoding="utf-8")

    with patch.object(VObject, "impress", side_effect=AssertionError("must not impress")):
        result = mv(source, "moved")

    assert not result.messages
    assert not (project / source).exists()
    producer_path = "moved" if source == "tasks/taskGen" else "moved/taskGen"
    moved = VObject(str(project / producer_path), str(project))
    assert (Path(moved.path) / "unfinished.txt").read_text() == "unsnapshotted changes\n"
    assert moved.config_file.read_variable("impression", "") == old_impression
    assert moved.config_file.read_variable("impressions", []) == old_history
    assert [obj.invariant_path() for obj in moved.predecessors()] == ["code/gen"]
    algorithm = VObject(str(project / "code/gen"), str(project))
    assert [obj.invariant_path() for obj in algorithm.successors()] == [producer_path]
    consumer_root = "tasks" if source == "tasks/taskGen" else "moved"
    expected_consumers = {f"{consumer_root}/taskAna1", f"{consumer_root}/taskAna2"}
    assert {obj.invariant_path() for obj in moved.successors()} == expected_consumers
    for path in expected_consumers:
        consumer = VObject(str(project / path), str(project))
        assert consumer.has_predecessor(moved)
        assert consumer.alias_to_path("gen") == producer_path
