"""Repeated task configuration remains one ordinary Celebi task."""
import json
import pytest
from unittest import mock

from click.testing import CliRunner
from CelebiChrono.celebi_cli.cli import cli

from CelebiChrono.kernel.vtask import VTask
from CelebiChrono.utils import metadata
from CelebiChrono.utils.subtasks import subtask_count


@pytest.mark.parametrize("value", [0, -1, True, False, 1.5, "3", None, [], {}])
def test_reject_invalid_repeat_count(value):
    with pytest.raises(ValueError, match="positive integer"):
        subtask_count({"subtasks": value})


def test_index_is_reserved_only_for_repeated_tasks():
    assert subtask_count({"parameters": {"index": 4}}) is None
    assert subtask_count({"subtasks": 1}) == 1
    with pytest.raises(ValueError, match="index is reserved"):
        subtask_count({"subtasks": 2, "parameters": {"index": 4}})


@pytest.mark.parametrize("environment", ["rawdata", "datalist", "lhcb_ap_datalist"])
def test_data_objects_cannot_repeat(environment):
    with pytest.raises(ValueError, match="executable tasks"):
        subtask_count({"subtasks": 2, "environment": environment})


def test_task_reads_subtasks_without_creating_child_objects(tmp_path):
    config = metadata.YamlFile(str(tmp_path / "celebi.yaml"))
    task = VTask(str(tmp_path))
    assert task.subtasks() is None
    config.write_variable("subtasks", 3)
    assert task.subtasks() == 3
    assert task.sub_objects() == []
    with pytest.raises(ValueError, match="index is reserved"):
        task.add_parameter("index", "2")
    config.write_variable("subtasks", None)
    assert task.validated() is False


def test_log_selects_subtask():
    with mock.patch("CelebiChrono.interface.shell.error_log", return_value="hello") as log:
        result = CliRunner().invoke(cli, ["log", "2", "--subtask", "7"])
    assert result.exit_code == 0
    assert result.output == "hello"
    log.assert_called_once_with(2, subtask=7)


def test_repeat_count_is_frozen_in_one_impression(tmp_path, monkeypatch):
    from CelebiChrono.kernel.immutable_impress import impress_immutable

    (tmp_path / ".celebi").mkdir()
    (tmp_path / ".celebi/config.json").write_text(json.dumps({
        "object_type": "project", "project_uuid": "p" * 32,
    }))
    (tmp_path / ".celebi/project.json").write_text("{}")
    task = tmp_path / "simulation"
    (task / ".celebi").mkdir(parents=True)
    (task / ".celebi/config.json").write_text(json.dumps({"object_type": "task"}))
    config = metadata.YamlFile(str(task / "celebi.yaml"))
    config.write_variable("subtasks", 100)
    monkeypatch.chdir(tmp_path)
    first = impress_immutable(tmp_path)
    assert set(first["objects"]) == {"simulation"}
    assert first["created"] == 1
    assert impress_immutable(tmp_path)["reused"] == 1
    config.write_variable("subtasks", 101)
    second = impress_immutable(tmp_path)
    assert second["created"] == 1
    assert first["objects"]["simulation"] != second["objects"]["simulation"]


def test_log_subtask_option_reaches_http_query():
    from CelebiChrono.kernel.chern_communicator import ChernCommunicator

    communicator = ChernCommunicator.__new__(ChernCommunicator)
    communicator.project_uuid = "project"
    communicator.timeout = 5
    communicator.serverurl = lambda: "localhost:3315"
    with mock.patch.object(communicator, "_request") as request:
        communicator.error_log(mock.Mock(uuid="impression"), 2, offset=10, subtask=7)
    assert request.call_args.kwargs["params"] == {"offset": 10, "subtask": 7}
