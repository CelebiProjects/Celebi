"""Tests for compute_live_sets (Celebi project-graph liveness).

Fixtures use the real object layout: shared config
<obj>/.celebi/config.json holds object_type; the local config
<obj>/.celebi/config.local.json holds the impression pointer and the
impressions history (see vobj_core.py Core.__init__, vtask.py
create_task, valgorithm.py create_algorithm).
"""
import json
import os

from CelebiChrono.kernel import liveness as celeb_liveness


def _mk_config(path, variables):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(variables, f)


def _mk_object(project, name, object_type, pointer, history):
    obj_dir = os.path.join(project, name)
    _mk_config(os.path.join(obj_dir, ".celebi", "config.json"),
               {"object_type": object_type})
    _mk_config(os.path.join(obj_dir, ".celebi", "config.local.json"),
               {"impression": pointer,
                "impressions": [{"uuid": u} for u in history]})


def _mk_impression(project, uuid, dependencies=None, aliases=None):
    _mk_config(os.path.join(project, ".celebi", "impressions",
                            uuid, "config.json"),
               {"dependencies": dependencies or [],
                "alias_to_impression": aliases or {}})


def _uuid(seed):
    return (seed * 8).zfill(32)[:32]


def test_compute_live_sets_current_plus_inputs(tmp_path):
    """Live = current pointers plus transitive inputs; history is superseded."""
    project = str(tmp_path / "proj")
    t1 = _uuid("a")
    t2 = _uuid("b")
    old = _uuid("c")
    data = _uuid("d")
    _mk_object(project, "task1", "task", t1, [old])
    _mk_object(project, "algo1", "algorithm", t2, [])
    _mk_impression(project, t1, dependencies=[data])
    _mk_impression(project, t2)
    _mk_impression(project, data)
    _mk_impression(project, old)

    live, superseded = celeb_liveness.compute_live_sets(project)

    assert set(live) == {t1, t2, data}
    assert superseded == [old]


def test_compute_live_sets_ignores_non_objects(tmp_path):
    """Directories without a task/algorithm config contribute nothing."""
    project = str(tmp_path / "proj")
    os.makedirs(os.path.join(project, "readme_dir"))
    _mk_config(os.path.join(project, "readme_dir", ".celebi",
                            "config.json"),
               {"object_type": "directory"})

    live, superseded = celeb_liveness.compute_live_sets(project)

    assert live == []
    assert superseded == []


def test_compute_live_sets_empty_project(tmp_path):
    """An empty project yields empty sets."""
    project = str(tmp_path / "proj")
    os.makedirs(project)
    live, superseded = celeb_liveness.compute_live_sets(project)
    assert live == []
    assert superseded == []


def test_compute_live_sets_aliases_transitive_deps_dangling_skipped(
        tmp_path):
    """Aliases and transitive dependencies join live; a dangling dep uuid
    (no impression config) is silently skipped, never a crash."""
    project = str(tmp_path / "proj")
    t1 = _uuid("a")
    data = _uuid("b")
    deeper = _uuid("c")
    dangling = _uuid("d")
    _mk_object(project, "task1", "task", t1, [])
    _mk_impression(project, t1, aliases={"input": data})
    _mk_impression(project, data, dependencies=[deeper, dangling])
    _mk_impression(project, deeper)
    # dangling has no impression config on purpose.

    live, superseded = celeb_liveness.compute_live_sets(project)

    assert live == sorted([t1, data, deeper])
    assert dangling not in live
    assert superseded == []
