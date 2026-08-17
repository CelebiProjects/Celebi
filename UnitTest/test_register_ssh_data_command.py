"""Tests for register-ssh-data shell function and CLI command."""
import os
import shutil
import tempfile
import unittest
from unittest import mock

from CelebiChrono.interface.shell_modules import object_creation
from CelebiChrono.celebi_cli.commands.object_creation import register_ssh_data_command
from CelebiChrono.utils.metadata import YamlFile


class TestRegisterSshData(unittest.TestCase):

    """Test Register SSH Data."""
    def _make_current(self, obj_type="project", path="/proj", env=None):
        """Make current."""
        current = mock.MagicMock()
        current.object_type.return_value = obj_type
        current.path = path
        current.project_path.return_value = "/proj"
        current.project_uuid.return_value = "proj-uuid"
        if env is not None:
            # rawdata-task check reads celebi.yaml on disk
            current.is_task = obj_type == "task"
        return current

    def _make_rawdata_task_current(self, tmpdir):
        """A current-object task whose celebi.yaml says environment: rawdata."""
        current = mock.MagicMock()
        current.object_type.return_value = "task"
        current.path = tmpdir
        current.project_path.return_value = "/proj"
        current.project_uuid.return_value = "proj-uuid"
        current.invariant_path.return_value = "/proj/rawtask"
        return current

    def test_polls_until_done_and_creates_pointer_task(self):
        """Test polls until done and creates pointer task."""
        current = self._make_current("directory", path="/proj/dir")
        states = iter([
            {"status": "hashing"},
            {"status": "copying"},
            {"status": "done",
             "result": {"uuid": "md5abc", "impression_uuid": "imp-1",
                        "descriptor": "d"}},
        ])
        cc = mock.MagicMock()
        cc.register_remote_data.return_value = {"job_id": "job-1"}
        cc.register_remote_data_status.side_effect = lambda j: next(states)

        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls, \
                mock.patch.object(object_creation.time, "sleep"), \
                mock.patch.object(object_creation, "tqdm",
                                  return_value=mock.MagicMock()), \
                mock.patch.object(object_creation, "_fill_or_create_pointer_task",
                                  return_value=mock.MagicMock(messages=[])) as fill:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            message = object_creation.register_ssh_data("cluster", "/src/data", "d")

        fill.assert_called_once_with(
            "/proj", current, "d", "md5abc", "", "register-ssh-data",
            default_runner="cluster")
        registered = [m for m in message.messages if "Registered" in str(m)]
        self.assertTrue(registered)
        self.assertTrue(registered[0][0].endswith("\n"))

    def test_exits_when_copying_with_result(self):
        """Copying-with-result is the exit point: fill the pointer, stop."""
        current = self._make_current("directory", path="/proj/dir")
        states = iter([
            {"status": "hashing"},
            {"status": "copying",
             "result": {"uuid": "md5abc", "impression_uuid": "imp-1",
                        "descriptor": "d"}},
        ])
        cc = mock.MagicMock()
        cc.register_remote_data.return_value = {"job_id": "job-1"}
        cc.register_remote_data_status.side_effect = lambda j: next(states)
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls, \
                mock.patch.object(object_creation.time, "sleep"), \
                mock.patch.object(object_creation, "tqdm",
                                  return_value=mock.MagicMock()), \
                mock.patch.object(object_creation, "_fill_or_create_pointer_task",
                                  return_value=mock.MagicMock(messages=[])) as fill:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            message = object_creation.register_ssh_data("cluster", "/src/data", "d")

        # exits at the copying poll — no further polling
        self.assertEqual(cc.register_remote_data_status.call_count, 2)
        fill.assert_called_once_with(
            "/proj", current, "d", "md5abc", "", "register-ssh-data",
            default_runner="cluster")
        self.assertTrue(any("Registered" in str(m) for m in message.messages))
        self.assertTrue(
            any("background" in str(m) for m in message.messages))

    def test_failed_job_reports_error(self):
        """Test failed job reports error."""
        current = self._make_current("project")
        states = iter([{"status": "failed", "error": "remote md5 failed: boom"}])
        cc = mock.MagicMock()
        cc.register_remote_data.return_value = {"job_id": "job-1"}
        cc.register_remote_data_status.side_effect = lambda j: next(states)
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls, \
                mock.patch.object(object_creation.time, "sleep"), \
                mock.patch.object(object_creation, "tqdm",
                                  return_value=mock.MagicMock()), \
                mock.patch.object(object_creation, "_fill_or_create_pointer_task") as fill:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            message = object_creation.register_ssh_data("cluster", "/src/data")
        fill.assert_not_called()
        self.assertTrue(any("boom" in str(m) for m in message.messages))

    def test_unknown_status_bails_after_10_consecutive(self):
        """A vanished job (404 -> 'unknown') must not be polled forever."""
        current = self._make_current("project")
        cc = mock.MagicMock()
        cc.register_remote_data.return_value = {"job_id": "job-1"}
        cc.register_remote_data_status.return_value = {
            "status": "unknown", "error": "job not found"}
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls, \
                mock.patch.object(object_creation.time, "sleep") as sleep, \
                mock.patch.object(object_creation, "tqdm",
                                  return_value=mock.MagicMock()):
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            message = object_creation.register_ssh_data("cluster", "/src/data")

        # 10 polls, then an error instead of an unbounded loop
        self.assertEqual(cc.register_remote_data_status.call_count, 10)
        self.assertEqual(sleep.call_count, 9)
        sleep.assert_called_with(3)
        self.assertTrue(
            any("unknown" in str(m) and "aborting" in str(m)
                for m in message.messages))

    def test_server_error_returned(self):
        """Test server error returned."""
        current = self._make_current("project")
        cc = mock.MagicMock()
        cc.register_remote_data.return_value = {"error": "requires an ssh runner"}
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            message = object_creation.register_ssh_data("local", "/p")
        self.assertTrue(any("ssh runner" in str(m) for m in message.messages))

    def test_idempotent_result_no_polling_creates_pointer_task(self):
        """A 'result' response (already registered) is used directly."""
        current = self._make_current("directory", path="/proj/dir")
        cc = mock.MagicMock()
        cc.register_remote_data.return_value = {
            "result": {"uuid": "md5abc", "impression_uuid": "imp-1",
                       "descriptor": "d"}}
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls, \
                mock.patch.object(object_creation, "_fill_or_create_pointer_task",
                                  return_value=mock.MagicMock(messages=[])) as fill:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            message = object_creation.register_ssh_data("cluster", "/src/data", "d")

        cc.register_remote_data_status.assert_not_called()
        fill.assert_called_once_with(
            "/proj", current, "d", "md5abc", "", "register-ssh-data",
            default_runner="cluster")
        self.assertTrue(any("Registered" in str(m) for m in message.messages))

    def test_done_fills_current_rawdata_task(self):
        """register-ssh-data inside a rawdata task fills that task, not a pointer."""
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        with open(os.path.join(tmp, "celebi.yaml"), "w", encoding="utf-8") as f:
            f.write("environment: rawdata\n")
        current = self._make_rawdata_task_current(tmp)
        states = iter([
            {"status": "done",
             "result": {"uuid": "md5abc", "impression_uuid": "imp-1",
                        "descriptor": "d"}},
        ])
        cc = mock.MagicMock()
        cc.register_remote_data.return_value = {"job_id": "job-1"}
        cc.register_remote_data_status.side_effect = lambda j: next(states)
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls, \
                mock.patch.object(object_creation.time, "sleep"), \
                mock.patch.object(object_creation, "tqdm",
                                  return_value=mock.MagicMock()), \
                mock.patch.object(object_creation, "_fill_or_create_pointer_task") as fill:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            message = object_creation.register_ssh_data("cluster", "/src/data", "d")

        fill.assert_not_called()
        yaml_file = YamlFile(os.path.join(tmp, "celebi.yaml"))
        self.assertEqual(yaml_file.read_variable("uuid", ""), "md5abc")
        self.assertEqual(yaml_file.read_variable("descriptor", ""), "d")
        self.assertTrue(
            any("Updated rawdata task at /proj/rawtask (register-ssh-data)" in str(m)
                for m in message.messages))

    def test_idempotent_result_fills_current_rawdata_task(self):
        """The result path also fills the current rawdata task directly."""
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        with open(os.path.join(tmp, "celebi.yaml"), "w", encoding="utf-8") as f:
            f.write("environment: rawdata\n")
        current = self._make_rawdata_task_current(tmp)
        cc = mock.MagicMock()
        cc.register_remote_data.return_value = {
            "result": {"uuid": "md5abc", "impression_uuid": "imp-1",
                       "descriptor": "d"}}
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls, \
                mock.patch.object(object_creation, "_fill_or_create_pointer_task") as fill:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            _message = object_creation.register_ssh_data("cluster", "/src/data", "d")

        cc.register_remote_data_status.assert_not_called()
        fill.assert_not_called()
        yaml_file = YamlFile(os.path.join(tmp, "celebi.yaml"))
        self.assertEqual(yaml_file.read_variable("uuid", ""), "md5abc")

    def test_cli_command(self):
        """Test cli command."""
        from click.testing import CliRunner
        self.assertEqual(register_ssh_data_command.name, "register-ssh-data")
        with mock.patch("CelebiChrono.interface.shell.register_ssh_data") as fn:
            result = CliRunner().invoke(register_ssh_data_command,
                                        ["cluster", "/src/data",
                                         "--descriptor", "d"])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("cluster", "/src/data", "d")

    def test_done_path_sets_default_runner(self):
        """Test done path sets default runner."""
        current = self._make_current("directory", path="/proj/dir")
        states = iter([
            {"status": "done",
             "result": {"uuid": "md5abc", "impression_uuid": "imp-1",
                        "descriptor": "d"}},
        ])
        cc = mock.MagicMock()
        cc.register_remote_data.return_value = {"job_id": "job-1"}
        cc.register_remote_data_status.side_effect = lambda j: next(states)
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls, \
                mock.patch.object(object_creation.time, "sleep"), \
                mock.patch.object(object_creation, "tqdm",
                                  return_value=mock.MagicMock()), \
                mock.patch.object(object_creation, "_fill_or_create_pointer_task",
                                  return_value=mock.MagicMock(messages=[])) as fill:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            object_creation.register_ssh_data("cluster", "/src/data", "d")
        fill.assert_called_once_with(
            "/proj", current, "d", "md5abc", "", "register-ssh-data",
            default_runner="cluster")

    def test_rawdata_context_sets_default_runner(self):
        """Test rawdata context sets default runner."""
        tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(tmp, ".celebi"))
        current = self._make_current("task", path=tmp, env="rawdata")
        with open(os.path.join(tmp, "celebi.yaml"), "w", encoding="utf-8") as f:
            f.write("environment: rawdata\nuuid: \ndescriptor: d\n")
        cc = mock.MagicMock()
        cc.register_remote_data.return_value = {"job_id": "job-1"}
        cc.register_remote_data_status.return_value = {
            "status": "done",
            "result": {"uuid": "md5abc", "impression_uuid": "imp-1",
                       "descriptor": "d"}}
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls, \
                mock.patch.object(object_creation.time, "sleep"), \
                mock.patch.object(object_creation, "tqdm",
                                  return_value=mock.MagicMock()):
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            object_creation.register_ssh_data("cluster", "/src/data", "d")
        current.set_default_runner.assert_called_once_with("cluster")


class _FakeBar:
    """Determinate progress bar shim recording tqdm interactions."""

    instances = []

    def __init__(self, **kwargs):
        self.total = kwargs.get("total")
        self.n = 0
        self.desc = kwargs.get("desc", "")
        self.closed = False
        _FakeBar.instances.append(self)

    def set_description(self, desc):
        """Record the description change."""
        self.desc = desc

    def refresh(self):
        """No-op."""

    def close(self):
        """Record the close."""
        self.closed = True


class TestRegisterSshDataProgressBar(unittest.TestCase):

    """Test the determinate byte progress bar."""

    def setUp(self):
        """Set Up."""
        _FakeBar.instances = []

    def _run(self, states):
        """Run register_ssh_data with the given poll states."""
        current = mock.MagicMock()
        current.object_type.return_value = "project"
        current.path = "/proj"
        current.project_path.return_value = "/proj"
        current.project_uuid.return_value = "proj-uuid"
        cc = mock.MagicMock()
        cc.register_remote_data.return_value = {"job_id": "job-1"}
        cc.register_remote_data_status.side_effect = lambda j: next(states)
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls, \
                mock.patch.object(object_creation.time, "sleep"), \
                mock.patch.object(object_creation, "tqdm",
                                  side_effect=_FakeBar), \
                mock.patch.object(object_creation,
                                  "_fill_or_create_pointer_task",
                                  return_value=mock.MagicMock(messages=[])):
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            return object_creation.register_ssh_data(
                "cluster", "/src/data", "d")

    def test_progress_drives_bar_bytes(self):
        """The bar total/n come from the server's byte progress."""
        states = iter([
            {"status": "hashing",
             "progress": {"stage": "hashing", "bytes_done": 3,
                          "bytes_total": 14}},
            {"status": "copying",
             "progress": {"stage": "copying", "bytes_done": 10,
                          "bytes_total": 14}},
            {"status": "done",
             "result": {"uuid": "md5abc", "impression_uuid": "imp-1",
                        "descriptor": "d"}},
        ])
        self._run(states)
        progress_bar = _FakeBar.instances[-1]
        self.assertEqual(progress_bar.total, 14)
        self.assertEqual(progress_bar.n, 10)
        self.assertTrue(progress_bar.closed)

    def test_bar_desc_follows_stage(self):
        """Stage transitions update the bar description."""
        states = iter([
            {"status": "hashing",
             "progress": {"stage": "hashing", "bytes_done": 1,
                          "bytes_total": 14}},
            {"status": "copying",
             "progress": {"stage": "copying", "bytes_done": 2,
                          "bytes_total": 14}},
            {"status": "done",
             "result": {"uuid": "md5abc", "impression_uuid": "imp-1",
                        "descriptor": "d"}},
        ])
        self._run(states)
        progress_bar = _FakeBar.instances[-1]
        self.assertIn("copying", progress_bar.desc)
        self.assertTrue(progress_bar.closed)

    def test_bar_closes_on_failed(self):
        """A failed job closes the bar and reports the error."""
        states = iter([{"status": "failed", "error": "boom"}])
        message = self._run(states)
        progress_bar = _FakeBar.instances[-1]
        self.assertTrue(progress_bar.closed)
        self.assertTrue(any("boom" in str(m) for m in message.messages))

    def test_bar_done_clamps_over_total(self):
        """bytes_done above bytes_total (CoW du overshoot) is clamped."""
        states = iter([
            {"status": "copying",
             "progress": {"stage": "copying", "bytes_done": 99,
                          "bytes_total": 14}},
            {"status": "done",
             "result": {"uuid": "md5abc", "impression_uuid": "imp-1",
                        "descriptor": "d"}},
        ])
        self._run(states)
        progress_bar = _FakeBar.instances[-1]
        self.assertEqual(progress_bar.n, 14)

    def test_bar_indeterminate_without_progress(self):
        """Polls without progress keep the bar total unset."""
        states = iter([
            {"status": "hashing"},
            {"status": "done",
             "result": {"uuid": "md5abc", "impression_uuid": "imp-1",
                        "descriptor": "d"}},
        ])
        self._run(states)
        progress_bar = _FakeBar.instances[-1]
        self.assertIsNone(progress_bar.total)

    def test_no_bar_for_idempotent_result(self):
        """The result fast path creates no bar."""
        current = mock.MagicMock()
        current.object_type.return_value = "project"
        current.path = "/proj"
        current.project_path.return_value = "/proj"
        current.project_uuid.return_value = "proj-uuid"
        cc = mock.MagicMock()
        cc.register_remote_data.return_value = {
            "result": {"uuid": "md5abc", "impression_uuid": "imp-1",
                       "descriptor": "d"}}
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls, \
                mock.patch.object(object_creation, "tqdm") as tqdm_mock, \
                mock.patch.object(object_creation,
                                  "_fill_or_create_pointer_task",
                                  return_value=mock.MagicMock(messages=[])):
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            object_creation.register_ssh_data("cluster", "/src/data", "d")
        tqdm_mock.assert_not_called()
