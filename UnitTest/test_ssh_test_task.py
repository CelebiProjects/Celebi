"""Tests for JobManager.ssh_test and VObject.ssh_test."""
import os
import tarfile
from datetime import datetime
from unittest import mock

import CelebiChrono.kernel.vtask as vtsk
from CelebiChrono.kernel import vtask_ssh_test
from CelebiChrono.kernel.vobject import VObject
from CelebiChrono.utils.message import Message

SSH_CONFIG = {"host": "cluster.example.com", "user": "alice", "port": 2222,
              "key": "KEY", "key_path": "/srv/keys/r1",
              "remote_workdir": "/data/yuki",
              "conda_env": "env_root_6.38.04"}


class FakeSshRunner:
    """Records constructor args and calls; scripted exec responses."""

    instances = []
    exit_code = 0
    # Responses consumed per exec_stream call: (code, [lines]). When empty,
    # exec_stream returns exit_code without delivering lines.
    script = [
        (0, ["/home/zhaomr/workdir/miniconda3"]),  # conda info --base probe
        (0, ["/home/zhaomr/workdir/miniconda3/envs/env_root_6.38.04/bin/python"]),
    ]

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.connected = False
        self.closed = False
        self.put_tar_args = None
        self.exec_args = []
        FakeSshRunner.instances.append(self)

    def connect(self):
        """Mark connected."""
        self.connected = True
        return self

    def put_tar(self, local_tar, remote_dir):
        """Record the upload."""
        self.put_tar_args = (local_tar, remote_dir)

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

    def conda_base_dir(self):
        """Scripted: consume the next exec response as conda info --base."""
        lines = []
        code = self.exec_stream("conda info --base", on_line=lines.append)
        if code:
            return ""
        return lines[0].strip() if lines else ""

    def close(self):
        """Mark closed."""
        self.closed = True


def _reset_fakes():
    """Reset the fake runner state between tests."""
    FakeSshRunner.instances = []
    FakeSshRunner.exit_code = 0
    FakeSshRunner.script = [
        (0, ["/home/zhaomr/workdir/miniconda3"]),
        (0, ["/home/zhaomr/workdir/miniconda3/envs/env_root_6.38.04/bin/python"]),
    ]


def _task():
    """A JobManager instance bypassing VTask construction."""
    return vtsk.VTask.__new__(vtsk.VTask)


def _cherncc(connected=True, ssh_config=None):
    """A ChernCommunicator stub."""
    cc = mock.MagicMock()
    cc.dite_status.return_value = "connected" if connected else "not connected"
    cc.runner_ssh_config.return_value = ssh_config
    return cc


def _task_with_workdirs(tmp_path):
    """A task stub whose pre_docker_test points at real temp dirs."""
    task = _task()
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    (base_dir / "stageout").mkdir()
    (base_dir / "data.txt").write_text("data")
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "run.py").write_text("print('hi')")
    mount_config = {
        "base_dir": str(base_dir),
        "mounts": [{"source": str(code_dir),
                    "target": "/workspace/code",
                    "readonly": False}],
    }
    task.pre_docker_test = mock.MagicMock(return_value=(True, mount_config))
    task._create_workaround_dir = mock.MagicMock(
        return_value=str(tmp_path / "stage"))
    task.inputs = mock.MagicMock(return_value=[])
    algorithm = mock.MagicMock()
    algorithm.commands.return_value = ["echo ${evt}"]
    task.algorithm = mock.MagicMock(return_value=algorithm)
    task.parameters = mock.MagicMock(return_value=(["evt"], {"evt": "20000"}))
    task.environment = mock.MagicMock(return_value="env_root_6.38.04")
    return task


def _run(task, connected=True, ssh_config=SSH_CONFIG):
    """Call ssh_test with the fake communicator and runner patched in."""
    with mock.patch.object(vtask_ssh_test, "SshRunner", FakeSshRunner), \
            mock.patch.object(vtask_ssh_test.ChernCommunicator,
                              "instance",
                              return_value=_cherncc(
                                  connected=connected,
                                  ssh_config=ssh_config)):
        return task.ssh_test("farm")


def test_ssh_test_runs_commands_on_runner(tmp_path):
    """ssh_test connects with the DITE config and streams the commands."""
    _reset_fakes()
    task = _task_with_workdirs(tmp_path)
    message = _run(task)
    assert "exited with code 0" in str(message)
    assert len(FakeSshRunner.instances) == 1
    runner = FakeSshRunner.instances[0]
    assert runner.connected
    assert runner.closed
    assert runner.kwargs["host"] == "cluster.example.com"
    assert runner.kwargs["user"] == "alice"
    assert runner.kwargs["port"] == 2222
    assert runner.kwargs["key_content"] == "KEY"


def test_ssh_test_uses_timestamped_remote_dir(tmp_path):
    """The remote test dir is named by date-time, not a random uuid."""
    _reset_fakes()
    fixed = datetime(2026, 8, 28, 18, 5, 30)
    task = _task_with_workdirs(tmp_path)
    with mock.patch.object(vtask_ssh_test, "datetime") as dt:
        dt.now.return_value = fixed
        message = _run(task)
    assert "exited with code 0" in str(message)
    remote_dir = FakeSshRunner.instances[0].put_tar_args[1]
    assert remote_dir == "/data/yuki/tests/20260828-180530"


def test_ssh_test_uploads_staged_tree_and_substitutes_parameters(tmp_path):
    """The tar holds the base + mounts; commands have parameters filled."""
    _reset_fakes()
    task = _task_with_workdirs(tmp_path)
    message = _run(task)
    assert "exited with code 0" in str(message)
    runner = FakeSshRunner.instances[0]
    local_tar, remote_dir = runner.put_tar_args
    assert remote_dir.startswith("/data/yuki/tests/")
    assert os.path.exists(local_tar)
    with tarfile.open(local_tar, "r:gz") as tar:
        names = tar.getnames()
    assert "data.txt" in names
    assert "code/run.py" in names
    command, cwd = runner.exec_args[-1]
    assert "mkdir -p stageout && echo 20000" in command
    assert cwd == remote_dir


def test_ssh_test_activates_resolved_conda_environment(tmp_path):
    """A resolved conda_env wraps the command via `conda run`."""
    _reset_fakes()
    task = _task_with_workdirs(tmp_path)
    config_with_env = dict(SSH_CONFIG, conda_env="env_root_6.38.04")
    message = _run(task, ssh_config=config_with_env)
    assert "exited with code 0" in str(message)
    runner = FakeSshRunner.instances[0]
    command, _cwd = runner.exec_args[-1]
    assert "conda run --no-capture-output -n env_root_6.38.04 -- bash -c" in command
    assert "mkdir -p stageout && echo 20000" in command


def test_ssh_test_sanitizes_remote_environment(tmp_path):
    """The run command resets PYTHONPATH/LD_LIBRARY_PATH and curates PATH."""
    _reset_fakes()
    FakeSshRunner.script = [
        (0, ["/home/zhaomr/workdir/miniconda3"]),
        (0, ["/home/zhaomr/workdir/miniconda3/envs/env_root_6.38.04/bin/python"]),
        (0, []),
    ]
    task = _task_with_workdirs(tmp_path)
    message = _run(task)
    assert "exited with code 0" in str(message)
    runner = FakeSshRunner.instances[0]
    # first call probes the conda base dir
    assert "conda info --base" in runner.exec_args[0][0]
    command, _cwd = runner.exec_args[-1]
    assert command.startswith("unset PYTHONPATH LD_LIBRARY_PATH; ")
    assert ("export PATH=\"/home/zhaomr/workdir/miniconda3/bin"
            ":$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin\"; "
            ) in command
    assert "mkdir -p stageout && echo 20000" in command


def test_ssh_test_fails_when_env_lacks_python(tmp_path):
    """A conda env without python aborts the run with a clear message."""
    _reset_fakes()
    FakeSshRunner.script = [
        (0, ["/home/zhaomr/workdir/miniconda3"]),
        (1, []),  # test -x on the env's python fails
    ]
    task = _task_with_workdirs(tmp_path)
    message = _run(task, ssh_config=dict(SSH_CONFIG, conda_env="env_root_6.38.04"))
    assert "not usable" in str(message)
    assert "no python found at" in str(message)
    assert "envs/env_root_6.38.04/bin/python" in str(message)
    assert not message.success
    runner = FakeSshRunner.instances[0]
    # only the probe and the verification ran — no command execution
    assert len(runner.exec_args) == 2
    assert runner.exec_args[1][0].startswith("test -x ")


def test_ssh_test_verify_failure_aborts_run(tmp_path):
    """A failing env probe (nonzero exit) aborts the run."""
    _reset_fakes()
    FakeSshRunner.script = [
        (0, ["/home/zhaomr/workdir/miniconda3"]),
        (1, ["CondaEnvironmentNotFoundError"]),
    ]
    task = _task_with_workdirs(tmp_path)
    message = _run(task, ssh_config=dict(SSH_CONFIG, conda_env="env_root_6.38.04"))
    assert "not usable" in str(message)
    assert not message.success
    assert len(FakeSshRunner.instances[0].exec_args) == 2


def test_ssh_test_reports_error_on_nonzero_exit(tmp_path):
    """A failing remote run yields an error message."""
    _reset_fakes()
    FakeSshRunner.exit_code = 7
    task = _task_with_workdirs(tmp_path)
    message = _run(task)
    assert "exited with code 7" in str(message)
    assert not message.success


def test_ssh_test_warns_when_dite_disconnected(tmp_path):
    """No run happens without a DITE connection."""
    _reset_fakes()
    task = _task_with_workdirs(tmp_path)
    message = _run(task, connected=False)
    assert "DITE is not connected" in str(message)
    assert FakeSshRunner.instances == []


def test_ssh_test_warns_when_runner_unknown(tmp_path):
    """An unknown runner name yields a warning."""
    _reset_fakes()
    task = _task_with_workdirs(tmp_path)
    message = _run(task, ssh_config=None)
    assert "farm" in str(message)


def test_ssh_test_warns_when_preparation_fails(tmp_path):
    """A failed pre_docker_test yields a warning."""
    _reset_fakes()
    task = _task()
    task.environment = mock.MagicMock(return_value="env_root_6.38.04")
    task.inputs = mock.MagicMock(return_value=[])
    algorithm = mock.MagicMock()
    algorithm.commands.return_value = ["echo hi"]
    task.algorithm = mock.MagicMock(return_value=algorithm)
    task.parameters = mock.MagicMock(return_value=([], {}))
    task.pre_docker_test = mock.MagicMock(return_value=(False, "boom"))
    message = _run(task)
    assert "boom" in str(message)


def test_vobject_ssh_test_refuses_non_task():
    """Non-task objects get a warning without delegating."""
    obj = VObject.__new__(VObject)
    obj.is_task = mock.MagicMock(return_value=False)
    message = obj.ssh_test("farm")
    assert "only be run on a task" in str(message)


def test_vobject_ssh_test_delegates_to_task():
    """Task objects delegate to the JobManager implementation."""
    obj = VObject.__new__(VObject)
    obj.is_task = mock.MagicMock(return_value=True)
    delegated = Message()
    delegated.add("delegated ok", "info")
    fake_task = mock.MagicMock()
    fake_task.ssh_test.return_value = delegated
    obj.get_vtask = mock.MagicMock(return_value=fake_task)
    obj.path = "fake/task/path"
    message = obj.ssh_test("farm")
    fake_task.ssh_test.assert_called_once_with("farm")
    assert "delegated ok" in str(message)


def test_prepare_data_dir_is_silent(tmp_path, capsys):
    """_prepare_data_dir must not print the tree listing to the console."""
    from CelebiChrono.kernel import vtask_job
    task = _task()
    task.path = str(tmp_path / "task")
    with mock.patch.object(vtask_job.csys, "tree_excluded", return_value=[]):
        task._prepare_data_dir(str(tmp_path / "workdir"))
    assert capsys.readouterr().out == ""


def test_prepare_mounting_preceding_jobs_records_impression(tmp_path):
    """Mount entries carry the preceding job's impression uuid."""
    from CelebiChrono.kernel import vtask_job
    task = _task()
    pre_tmp = tmp_path / "pre_tmp"
    pre_tmp.mkdir()
    task._workaround_dir = mock.MagicMock(return_value=str(pre_tmp))
    pre = mock.MagicMock()
    pre.impression.return_value.uuid = "imp-bkg-1"
    pre.invariant_path.return_value = "MVA/sample2024/tmva_bkg"
    pre.environment.return_value = "rawdata"
    task.inputs = mock.MagicMock(return_value=[pre])
    task.path_to_alias = mock.MagicMock(return_value="bkg")
    mount_config = {"mounts": []}
    with mock.patch("builtins.print"):
        task._prepare_mounting_preceding_jobs(mock.MagicMock(), None, mount_config)
    assert mount_config["mounts"][0]["impression"] == "imp-bkg-1"
    assert mount_config["mounts"][0]["target"] == "/workspace/bkg"


def test_ssh_test_symlinks_cached_inputs_instead_of_tarring(tmp_path):
    """Inputs already on the runner are symlinked, not uploaded in the tar."""
    _reset_fakes()
    task = _task_with_workdirs(tmp_path)
    task.project_uuid = mock.MagicMock(return_value="proj-123")
    pre = mock.MagicMock()
    pre.impression.return_value.uuid = "imp-bkg-1"
    task.inputs = mock.MagicMock(return_value=[pre])
    # add an impression-carrying mount (a preceding job output)
    mount = {"source": str(tmp_path / "code"),
             "target": "/workspace/bkg", "impression": "imp-bkg-1"}
    task.pre_docker_test.return_value = (
        True, {"base_dir": str(tmp_path / "base"),
               "mounts": [mount]})
    FakeSshRunner.script = [
        (0, []),                                     # cached check: present
        (0, []),                                     # symlink exec
        (0, ["/home/zhaomr/workdir/miniconda3"]),     # conda probe
        (0, []),                                     # env verify
        (0, []),                                     # run
    ]
    message = _run(task)
    assert "exited with code 0" in str(message)
    runner = FakeSshRunner.instances[0]
    local_tar, _remote_dir = runner.put_tar_args
    with tarfile.open(local_tar, "r:gz") as tar:
        names = tar.getnames()
    assert "run.py" not in names  # cached mount not uploaded
    check = runner.exec_args[0][0]
    assert check.startswith("test -d ")
    assert "impressions/proj-123/imp-bkg-1" in check
    symlink_cmd = runner.exec_args[1][0]
    assert "ln -s" in symlink_cmd
    assert "impressions/proj-123/imp-bkg-1" in symlink_cmd
    assert symlink_cmd.split("ln -s ")[1].split(" ")[0].endswith(
        "impressions/proj-123/imp-bkg-1")
    assert "bkg/stageout" in symlink_cmd


def test_ssh_test_tars_inputs_not_on_runner(tmp_path):
    """Inputs missing from the runner cache are uploaded in the tar."""
    _reset_fakes()
    task = _task_with_workdirs(tmp_path)
    task.project_uuid = mock.MagicMock(return_value="proj-123")
    pre = mock.MagicMock()
    pre.impression.return_value.uuid = "imp-bkg-1"
    task.inputs = mock.MagicMock(return_value=[pre])
    mount = {"source": str(tmp_path / "code"),
             "target": "/workspace/bkg", "impression": "imp-bkg-1"}
    task.pre_docker_test.return_value = (
        True, {"base_dir": str(tmp_path / "base"),
               "mounts": [mount]})
    FakeSshRunner.script = [
        (1, []),                                     # cached check: missing
        (0, ["/home/zhaomr/workdir/miniconda3"]),     # conda probe
        (0, []),                                     # env verify
        (0, []),                                     # run
    ]
    message = _run(task)
    assert "exited with code 0" in str(message)
    runner = FakeSshRunner.instances[0]
    local_tar, _remote_dir = runner.put_tar_args
    with tarfile.open(local_tar, "r:gz") as tar:
        names = tar.getnames()
    assert "bkg/run.py" in names  # not cached -> uploaded under the alias
    for _cmd, _cwd in runner.exec_args:
        assert "ln -s" not in _cmd


def test_prepare_mounting_skips_download_for_cached_impressions(tmp_path):
    """Cached impressions are not downloaded; their mounts are still added."""
    from CelebiChrono.kernel import vtask_job
    task = _task()
    task._workaround_dir = mock.MagicMock(
        return_value=str(tmp_path / "nonexistent_pre_tmp"))
    pre = mock.MagicMock()
    pre.impression.return_value.uuid = "imp-bkg-1"
    pre.invariant_path.return_value = "MVA/sample2024/tmva_bkg"
    pre.environment.return_value = "rawdata"
    task.inputs = mock.MagicMock(return_value=[pre])
    task.path_to_alias = mock.MagicMock(return_value="bkg")
    cherncc = mock.MagicMock()
    cherncc.output_files.return_value = ["a.root"]
    mount_config = {"mounts": []}
    with mock.patch("builtins.print"):
        task._prepare_mounting_preceding_jobs(
            cherncc, None, mount_config,
            skip_impressions={"imp-bkg-1"})
    cherncc.output_files.assert_not_called()
    cherncc.export.assert_not_called()
    assert mount_config["mounts"][0]["impression"] == "imp-bkg-1"


def test_ssh_test_skips_download_for_cached_inputs(tmp_path):
    """ssh_test passes the cached impressions into pre_docker_test."""
    _reset_fakes()
    task = _task_with_workdirs(tmp_path)
    task.project_uuid = mock.MagicMock(return_value="proj-123")
    pre = mock.MagicMock()
    pre.impression.return_value.uuid = "imp-bkg-1"
    task.inputs = mock.MagicMock(return_value=[pre])
    mount = {"source": str(tmp_path / "code"),
             "target": "/workspace/bkg", "impression": "imp-bkg-1"}
    task.pre_docker_test.return_value = (
        True, {"base_dir": str(tmp_path / "base"),
               "mounts": [mount]})
    FakeSshRunner.script = [
        (0, []),                                     # cached check: present
        (0, []),                                     # symlink exec
        (0, ["/home/zhaomr/workdir/miniconda3"]),     # conda probe
        (0, []),                                     # env verify
        (0, []),                                     # run
    ]
    message = _run(task)
    assert "exited with code 0" in str(message)
    task.pre_docker_test.assert_called_once_with(
        skip_impressions={"imp-bkg-1"})
    runner = FakeSshRunner.instances[0]
    assert "ln -s" in runner.exec_args[1][0]


def test_ssh_test_downloads_inputs_not_on_runner(tmp_path):
    """Inputs missing from the runner cache are downloaded as before."""
    _reset_fakes()
    task = _task_with_workdirs(tmp_path)
    task.project_uuid = mock.MagicMock(return_value="proj-123")
    pre = mock.MagicMock()
    pre.impression.return_value.uuid = "imp-bkg-1"
    task.inputs = mock.MagicMock(return_value=[pre])
    mount = {"source": str(tmp_path / "code"),
             "target": "/workspace/bkg", "impression": "imp-bkg-1"}
    task.pre_docker_test.return_value = (
        True, {"base_dir": str(tmp_path / "base"),
               "mounts": [mount]})
    FakeSshRunner.script = [
        (1, []),                                     # cached check: missing
        (0, ["/home/zhaomr/workdir/miniconda3"]),     # conda probe
        (0, []),                                     # env verify
        (0, []),                                     # run
    ]
    message = _run(task)
    assert "exited with code 0" in str(message)
    task.pre_docker_test.assert_called_once_with(skip_impressions=set())
    local_tar, _ = FakeSshRunner.instances[0].put_tar_args
    with tarfile.open(local_tar, "r:gz") as tar:
        assert "bkg/run.py" in tar.getnames()
