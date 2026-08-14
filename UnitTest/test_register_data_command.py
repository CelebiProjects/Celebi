"""Tests for register-data shell function and CLI command."""
import os
import shutil
import tempfile
import unittest
from unittest import mock

from CelebiChrono.interface.shell_modules import object_creation
from CelebiChrono.celebi_cli.commands.object_creation import register_data_command
from CelebiChrono.utils.metadata import YamlFile


class TestRegisterData(unittest.TestCase):

    def _make_current(self, obj_type="project", path="/proj", env=None):
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
                mock.patch.object(object_creation, "_fill_or_create_pointer_task",
                                  return_value=mock.MagicMock(messages=[])) as fill:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            message = object_creation.register_data("cluster", "/src/data", "d")

        fill.assert_called_once_with(
            "/proj", current, "d", "md5abc", "", "register-data")
        self.assertTrue(any("Registered" in str(m) for m in message.messages))

    def test_failed_job_reports_error(self):
        current = self._make_current("project")
        states = iter([{"status": "failed", "error": "remote md5 failed: boom"}])
        cc = mock.MagicMock()
        cc.register_remote_data.return_value = {"job_id": "job-1"}
        cc.register_remote_data_status.side_effect = lambda j: next(states)
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls, \
                mock.patch.object(object_creation.time, "sleep"), \
                mock.patch.object(object_creation, "_fill_or_create_pointer_task") as fill:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            message = object_creation.register_data("cluster", "/src/data")
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
                mock.patch.object(object_creation.time, "sleep") as sleep:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            message = object_creation.register_data("cluster", "/src/data")

        # 10 polls, then an error instead of an unbounded loop
        self.assertEqual(cc.register_remote_data_status.call_count, 10)
        self.assertEqual(sleep.call_count, 9)
        sleep.assert_called_with(3)
        self.assertTrue(
            any("unknown" in str(m) and "aborting" in str(m)
                for m in message.messages))

    def test_server_error_returned(self):
        current = self._make_current("project")
        cc = mock.MagicMock()
        cc.register_remote_data.return_value = {"error": "requires an ssh runner"}
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            message = object_creation.register_data("local", "/p")
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
            message = object_creation.register_data("cluster", "/src/data", "d")

        cc.register_remote_data_status.assert_not_called()
        fill.assert_called_once_with(
            "/proj", current, "d", "md5abc", "", "register-data")
        self.assertTrue(any("Registered" in str(m) for m in message.messages))

    def test_done_fills_current_rawdata_task(self):
        """register-data inside a rawdata task fills that task, not a pointer."""
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
                mock.patch.object(object_creation, "_fill_or_create_pointer_task") as fill:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            message = object_creation.register_data("cluster", "/src/data", "d")

        fill.assert_not_called()
        yaml_file = YamlFile(os.path.join(tmp, "celebi.yaml"))
        self.assertEqual(yaml_file.read_variable("uuid", ""), "md5abc")
        self.assertEqual(yaml_file.read_variable("descriptor", ""), "d")
        self.assertTrue(
            any("Updated rawdata task at /proj/rawtask (register-data)" in str(m)
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
            message = object_creation.register_data("cluster", "/src/data", "d")

        cc.register_remote_data_status.assert_not_called()
        fill.assert_not_called()
        yaml_file = YamlFile(os.path.join(tmp, "celebi.yaml"))
        self.assertEqual(yaml_file.read_variable("uuid", ""), "md5abc")

    def test_cli_command(self):
        from click.testing import CliRunner
        with mock.patch("CelebiChrono.interface.shell.register_data") as fn:
            result = CliRunner().invoke(register_data_command,
                                        ["cluster", "/src/data",
                                         "--descriptor", "d"])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("cluster", "/src/data", "d")
