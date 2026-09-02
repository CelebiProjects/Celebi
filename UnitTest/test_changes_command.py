"""Tests for the `changes` command (diff current object vs latest impression)."""
import json
import os
import shutil
import sys
import tempfile

import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from CelebiChrono.utils import csys  # pylint: disable=wrong-import-position
from CelebiChrono.kernel.chern_cache import ChernCache  # pylint: disable=wrong-import-position
from CelebiChrono.kernel.valgorithm import VAlgorithm  # pylint: disable=wrong-import-position
from CelebiChrono.kernel.vtask import VTask  # pylint: disable=wrong-import-position


def _write_json(path, data):
    """Write json data to the file at path."""
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(data, stream)


def _make_object(path, object_type):
    """Create a plain directory object."""
    os.makedirs(os.path.join(path, ".celebi"), exist_ok=True)
    _write_json(os.path.join(path, ".celebi", "config.json"),
                {"object_type": object_type})


def _make_task_or_algo(path, object_type, predecessors=(), successors=(),
                       alias_to_path=None):
    """Create a task or algorithm object at path."""
    _make_object(path, object_type)
    with open(os.path.join(path, "celebi.yaml"), "w",
              encoding="utf-8") as stream:
        yaml.safe_dump({"alias": [],
                        "environment": "celebichrono/lhcb-omegac:v0.2",
                        "kubernetes_memory_limit": "256Mi"}, stream)
    with open(os.path.join(path, "README.md"), "w",
              encoding="utf-8") as stream:
        stream.write("")
    alias_to_path = alias_to_path or {}
    _write_json(os.path.join(path, ".celebi", "config.json"), {
        "object_type": object_type,
        "predecessors": list(predecessors),
        "successors": list(successors),
        "alias_to_path": alias_to_path,
        "path_to_alias": {p: a for a, p in alias_to_path.items()},
        "impression": "", "impressions": [],
        "output_md5s": {}, "output_md5": ""})


def _make_project_with_task():
    """Create a temp project with a task. Returns (root, task_path)."""
    root = os.path.realpath(tempfile.mkdtemp())
    _make_object(root, "project")
    with open(os.path.join(root, ".celebi", "project.json"),
              "w", encoding="utf-8") as stream:
        stream.write("")
    _make_object(os.path.join(root, "code"), "directory")
    task = os.path.join(root, "code", "Task1")
    _make_task_or_algo(task, "task")
    os.chdir(root)
    return root, task


def _make_project_with_task_and_algorithm():
    """Create a temp project with a task depending on an algorithm.

    Returns (root, task_path, algorithm_path).
    """
    root = os.path.realpath(tempfile.mkdtemp())
    _make_object(root, "project")
    with open(os.path.join(root, ".celebi", "project.json"),
              "w", encoding="utf-8") as stream:
        stream.write("")
    _make_object(os.path.join(root, "code"), "directory")
    algo = os.path.join(root, "code", "Gen")
    _make_task_or_algo(algo, "algorithm", successors=["Task1"])
    task = os.path.join(root, "code", "Task1")
    _make_task_or_algo(task, "task", predecessors=["code/Gen"],
                       alias_to_path={"gen_alias": "code/Gen"})
    os.chdir(root)
    return root, task, algo


def _text(message):
    """Plain-text rendering of a Message."""
    return str(message)


def test_changes_never_impressed_warns():
    """A task with no impression gets a warning instead of crashing."""
    root, task = _make_project_with_task()
    try:
        task_obj = VTask(task)
        text = _text(task_obj.changes())
        assert "no history impressed yet" in text
    finally:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        shutil.rmtree(root, ignore_errors=True)


def test_changes_detects_file_level_changes():
    """Added, removed and modified files are all reported against the impression."""
    root, task = _make_project_with_task()
    try:
        with open(os.path.join(task, "input.txt"), "w", encoding="utf-8") as stream:
            stream.write("original input\n")
        with open(os.path.join(task, "gone.txt"), "w", encoding="utf-8") as stream:
            stream.write("will be deleted\n")
        VTask(task).impress()

        # Modify the yaml, add a file, remove a file.
        with open(os.path.join(task, "celebi.yaml"), "a", encoding="utf-8") as stream:
            stream.write("# edited\n")
        with open(os.path.join(task, "extra.txt"), "w", encoding="utf-8") as stream:
            stream.write("brand new\n")
        os.remove(os.path.join(task, "gone.txt"))

        ChernCache.instance().__init__()  # pylint: disable=unnecessary-dunder-call
        task_obj = VTask(task)
        text = _text(task_obj.changes())

        assert "extra.txt" in text            # added file reported
        assert "gone.txt" in text             # removed file reported
        assert "Diff in file: celebi.yaml" in text
    finally:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        ChernCache.instance().__init__()  # pylint: disable=unnecessary-dunder-call
        shutil.rmtree(root, ignore_errors=True)


def test_changes_reports_no_changes():
    """A clean tree produces an explicit no-changes message, not silence."""
    root, task = _make_project_with_task()
    try:
        VTask(task).impress()
        ChernCache.instance().__init__()  # pylint: disable=unnecessary-dunder-call
        task_obj = VTask(task)
        text = _text(task_obj.changes())
        assert "No file-level changes detected." in text
        assert "Added files:" not in text
        assert "Removed files:" not in text
    finally:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        ChernCache.instance().__init__()  # pylint: disable=unnecessary-dunder-call
        shutil.rmtree(root, ignore_errors=True)


def test_changes_ignores_dotfiles():
    """Hidden files (e.g. .DS_Store) are not reported as added files."""
    root, task = _make_project_with_task()
    try:
        VTask(task).impress()
        with open(os.path.join(task, ".DS_Store"), "wb") as stream:
            stream.write(b"\x00\x01")
        ChernCache.instance().__init__()  # pylint: disable=unnecessary-dunder-call
        task_obj = VTask(task)
        text = _text(task_obj.changes())
        assert ".DS_Store" not in text
    finally:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        ChernCache.instance().__init__()  # pylint: disable=unnecessary-dunder-call
        shutil.rmtree(root, ignore_errors=True)


def test_get_files_in_directory_exclude_is_component_wise():
    """Excluding README.md must not also exclude README.md.bak."""
    root = os.path.realpath(tempfile.mkdtemp())
    try:
        with open(os.path.join(root, "README.md"), "w", encoding="utf-8") as stream:
            stream.write("")
        with open(os.path.join(root, "README.md.bak"), "w", encoding="utf-8") as stream:
            stream.write("")
        files = csys.get_files_in_directory(root, exclude=("README.md",))
        assert files == ["README.md.bak"]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_changes_reports_dependency_change_when_files_identical():
    """A re-impressed predecessor is reported even when own files are unchanged."""
    root, task, algo = _make_project_with_task_and_algorithm()
    try:
        with open(os.path.join(task, "input.txt"), "w", encoding="utf-8") as stream:
            stream.write("input\n")
        with open(os.path.join(algo, "gen.C"), "w", encoding="utf-8") as stream:
            stream.write("void gen() {}\n")
        VTask(task).impress()  # impresses the algorithm first

        # Edit and re-impress the algorithm: its impression uuid changes.
        with open(os.path.join(algo, "gen.C"), "w", encoding="utf-8") as stream:
            stream.write("void gen() { int x; }\n")
        ChernCache.instance().__init__()  # pylint: disable=unnecessary-dunder-call
        VAlgorithm(algo).impress()

        ChernCache.instance().__init__()  # pylint: disable=unnecessary-dunder-call
        task_obj = VTask(task)
        text = _text(task_obj.changes())

        assert "No file-level changes detected." not in text
        assert "not impressed" in text
        assert "code/Gen" in text
        # The alias points at the same predecessor: no redundant alias line.
        assert "Alias" not in text
    finally:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        ChernCache.instance().__init__()  # pylint: disable=unnecessary-dunder-call
        shutil.rmtree(root, ignore_errors=True)


def test_changes_reports_alias_change_for_non_predecessor():
    """An alias to an object that is not a predecessor is still reported."""
    root = os.path.realpath(tempfile.mkdtemp())
    try:
        _make_object(root, "project")
        with open(os.path.join(root, ".celebi", "project.json"),
                  "w", encoding="utf-8") as stream:
            stream.write("")
        _make_object(os.path.join(root, "code"), "directory")
        other = os.path.join(root, "code", "OtherAlgo")
        _make_task_or_algo(other, "algorithm")
        task = os.path.join(root, "code", "Task1")
        _make_task_or_algo(task, "task",
                           alias_to_path={"extra": "code/OtherAlgo"})
        os.chdir(root)

        with open(os.path.join(other, "gen.C"), "w", encoding="utf-8") as stream:
            stream.write("void gen() {}\n")
        VAlgorithm(other).impress()
        VTask(task).impress()

        # Edit and re-impress the aliased (non-predecessor) algorithm.
        with open(os.path.join(other, "gen.C"), "w", encoding="utf-8") as stream:
            stream.write("void gen() { int z; }\n")
        ChernCache.instance().__init__()  # pylint: disable=unnecessary-dunder-call
        VAlgorithm(other).impress()

        ChernCache.instance().__init__()  # pylint: disable=unnecessary-dunder-call
        task_obj = VTask(task)
        text = _text(task_obj.changes())

        assert "No file-level changes detected." not in text
        assert "Alias extra changed impression" in text
    finally:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        ChernCache.instance().__init__()  # pylint: disable=unnecessary-dunder-call
        shutil.rmtree(root, ignore_errors=True)


def test_changes_reports_unimpressed_predecessor():
    """An unimpressed predecessor is reported even when own files are unchanged."""
    root, task, algo = _make_project_with_task_and_algorithm()
    try:
        with open(os.path.join(algo, "gen.C"), "w", encoding="utf-8") as stream:
            stream.write("void gen() {}\n")
        VTask(task).impress()  # impresses the algorithm first

        # Edit the algorithm without impressing it.
        with open(os.path.join(algo, "gen.C"), "w", encoding="utf-8") as stream:
            stream.write("void gen() { int y; }\n")
        ChernCache.instance().__init__()  # pylint: disable=unnecessary-dunder-call

        task_obj = VTask(task)
        text = _text(task_obj.changes())

        assert "No file-level changes detected." not in text
        assert "is not impressed" in text
        assert "code/Gen" in text
    finally:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        ChernCache.instance().__init__()  # pylint: disable=unnecessary-dunder-call
        shutil.rmtree(root, ignore_errors=True)
