"""Tests for SshTestMixin.check_results and VObject.check_results."""
from datetime import datetime
from unittest import mock

import CelebiChrono.kernel.vtask as vtsk
from CelebiChrono.kernel import vtask_ssh_test
from CelebiChrono.kernel.vobject import VObject
from CelebiChrono.utils.message import Message

SSH_CONFIG = {"host": "cluster.example.com", "user": "alice", "port": 2222,
              "key": "KEY", "key_path": "/srv/keys/r1",
              "remote_workdir": "/data/yuki"}


class FakeSshRunner:
    """Records constructor args and calls; scripted exec responses."""

    instances = []
    exit_code = 0
    # Responses consumed per exec_stream call: (code, [lines]). When empty,
    # exec_stream returns exit_code without delivering lines.
    script = [(0, [])]

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.connected = False
        self.closed = False
        self.exec_args = []
        FakeSshRunner.instances.append(self)

    def connect(self):
        """Mark connected."""
        self.connected = True
        return self

    def exec_stream(self, command, cwd=None, on_line=None):
        """Record the run and return the scripted code."""
        self.exec_args.append((command, cwd))
        if FakeSshRunner.script:
            code, lines = FakeSshRunner.script.pop(0)
            for line in lines:
                if on_line:
                    on_line(line)
            return code
        return FakeSshRunner.exit_code

    def close(self):
        """Mark closed."""
        self.closed = True


def _reset_fakes():
    """Reset the fake runner state between tests."""
    FakeSshRunner.instances = []
    FakeSshRunner.exit_code = 0
    FakeSshRunner.script = [(0, [])]


def _task():
    """A SshTestMixin instance bypassing VTask construction."""
    return vtsk.VTask.__new__(vtsk.VTask)


def _cherncc(connected=True, ssh_config=None):
    """A ChernCommunicator stub."""
    cc = mock.MagicMock()
    cc.dite_status.return_value = "connected" if connected else "not connected"
    cc.runner_ssh_config.return_value = ssh_config
    return cc


def _impression_task():
    """A task stub carrying a project uuid and an impressed impression."""
    task = _task()
    task.project_uuid = mock.MagicMock(return_value="proj-123")
    imp = mock.MagicMock()
    imp.uuid = "imp-abc-123"
    task.impression = mock.MagicMock(return_value=imp)
    task.environment = mock.MagicMock(return_value="env_root_6.38.04")
    return task


def _run(task, connected=True, ssh_config=SSH_CONFIG):
    """Call check_results with the fake communicator and runner patched in."""
    with mock.patch.object(vtask_ssh_test, "SshRunner", FakeSshRunner), \
            mock.patch.object(vtask_ssh_test.ChernCommunicator,
                              "instance",
                              return_value=_cherncc(
                                  connected=connected,
                                  ssh_config=ssh_config)):
        return task.check_results("farm")


def test_check_results_links_cached_files_into_timestamped_dir():
    """Each cache entry is symlinked into a fresh timestamped check dir."""
    _reset_fakes()
    FakeSshRunner.script = [(0, [])]
    fixed = datetime(2026, 8, 28, 18, 5, 30)
    task = _impression_task()
    with mock.patch.object(vtask_ssh_test, "datetime") as dt:
        dt.now.return_value = fixed
        message = _run(task)
    assert message.success
    assert ("cluster.example.com:/data/yuki/tests/check/20260828-180530"
            in str(message))
    rendered = message.colored()
    assert ("Results mounted at cluster.example.com:/data/yuki/tests/check/"
            "20260828-180530\n" in rendered)
    assert "Each entry is a symlink into the runner cache.\n" in rendered
    runner = FakeSshRunner.instances[0]
    assert runner.connected
    assert runner.closed
    assert runner.kwargs["host"] == "cluster.example.com"
    # cached check and linking travel in one remote command
    assert len(runner.exec_args) == 1
    command = runner.exec_args[0][0]
    assert command.startswith("test -d ")
    assert "impressions/proj-123/imp-abc-123" in command
    assert "|| exit 3" in command
    assert "mkdir -p /data/yuki/tests/check/20260828-180530" in command
    assert "for f in /data/yuki/impressions/proj-123/imp-abc-123/*" in command
    assert '[ -e "$f" ] || [ -L "$f" ] || continue' in command
    assert 'ln -s "$f" /data/yuki/tests/check/20260828-180530/' in command


def test_check_results_errors_when_no_impression():
    """No impression on the task aborts before any connection."""
    _reset_fakes()
    task = _task()
    task.impression = mock.MagicMock(return_value=None)
    message = _run(task)
    assert not message.success
    assert "no impression" in str(message)
    assert FakeSshRunner.instances == []


def test_check_results_errors_when_not_cached_on_runner():
    """A missing runner cache entry (exit 3) suggests cache-results."""
    _reset_fakes()
    FakeSshRunner.script = [(3, [])]
    task = _impression_task()
    message = _run(task)
    assert not message.success
    assert "cache-results" in str(message)
    runner = FakeSshRunner.instances[0]
    assert runner.closed
    assert len(runner.exec_args) == 1


def test_check_results_warns_when_dite_disconnected():
    """No connection attempt without a DITE connection."""
    _reset_fakes()
    task = _impression_task()
    message = _run(task, connected=False)
    assert "DITE is not connected" in str(message)
    assert FakeSshRunner.instances == []


def test_check_results_warns_when_runner_unknown():
    """An unknown runner name yields a warning without connecting."""
    _reset_fakes()
    task = _impression_task()
    message = _run(task, ssh_config=None)
    assert "farm" in str(message)
    assert FakeSshRunner.instances == []


def test_check_results_reports_error_on_nonzero_exit():
    """A failing link command yields an error message."""
    _reset_fakes()
    FakeSshRunner.script = [(7, [])]
    task = _impression_task()
    message = _run(task)
    assert not message.success
    assert "exited with code 7" in str(message)
    assert len(FakeSshRunner.instances[0].exec_args) == 1


def test_vobject_check_results_refuses_non_task():
    """Non-task objects get a warning without delegating."""
    obj = VObject.__new__(VObject)
    obj.is_task = mock.MagicMock(return_value=False)
    message = obj.check_results("farm")
    assert "only be run on a task" in str(message)


def test_vobject_check_results_delegates_to_task():
    """Task objects delegate to the SshTestMixin implementation."""
    obj = VObject.__new__(VObject)
    obj.is_task = mock.MagicMock(return_value=True)
    delegated = Message()
    delegated.add("delegated ok", "info")
    fake_task = mock.MagicMock()
    fake_task.check_results.return_value = delegated
    obj.get_vtask = mock.MagicMock(return_value=fake_task)
    obj.path = "fake/task/path"
    message = obj.check_results("farm")
    fake_task.check_results.assert_called_once_with("farm")
    assert "delegated ok" in str(message)
