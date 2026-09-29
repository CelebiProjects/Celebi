"""Regression tests for removing Celebi objects."""

import shutil
from pathlib import Path

from CelebiChrono.kernel.chern_cache import ChernCache
from CelebiChrono.kernel.vobject import VObject
from CelebiChrono.utils.metadata import YamlFile


def test_rm_producer_removes_aliases_from_surviving_successors(tmp_path, monkeypatch):
    """Deleting a producer must not leave zombie aliases on its consumers."""
    fixture = Path(__file__).parents[1] / "UnitTest/data/demo_complex"
    project = tmp_path / "demo_complex"
    shutil.copytree(fixture, project)
    monkeypatch.chdir(project)

    cache = ChernCache.instance()
    monkeypatch.setattr(cache, "project_path", str(project))
    monkeypatch.setattr(cache, "project_modification_time", (None, -1))
    monkeypatch.setattr(cache, "generic_cache", {})

    producer = VObject(str(project / "tasks/taskGen"), str(project))
    consumers = [
        VObject(str(project / "tasks/taskAna1"), str(project)),
        VObject(str(project / "tasks/taskAna2"), str(project)),
    ]

    for consumer in consumers:
        assert consumer.has_predecessor(producer)
        assert consumer.alias_to_path("gen") == "tasks/taskGen"

    producer.rm()

    assert not (project / "tasks/taskGen").exists()
    for consumer in consumers:
        assert not consumer.has_predecessor(producer)
        assert not consumer.alias_to_path("gen")
        assert not consumer.path_to_alias("tasks/taskGen")
        aliases = YamlFile(str(Path(consumer.path) / "celebi.yaml")).read_variable(
            "alias", []
        )
        assert "gen" not in aliases
