"""Tests for register-data shell function and CLI command."""
import unittest
from unittest import mock

from CelebiChrono.interface.shell_modules import object_creation
from CelebiChrono.celebi_cli.commands.object_creation import register_data_command


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

    def test_cli_command(self):
        from click.testing import CliRunner
        with mock.patch("CelebiChrono.interface.shell.register_data") as fn:
            result = CliRunner().invoke(register_data_command,
                                        ["cluster", "/src/data",
                                         "--descriptor", "d"])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with("cluster", "/src/data", "d")
