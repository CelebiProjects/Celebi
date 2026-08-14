"""Tests for verify-data shell function and CLI command."""
import unittest
from unittest import mock

from CelebiChrono.interface.shell_modules import object_creation
from CelebiChrono.celebi_cli.commands.object_creation import verify_data_command


class TestVerifyData(unittest.TestCase):

    def _make_current(self, env="rawdata", impressed=True, obj_type="task"):
        current = mock.MagicMock()
        current.object_type.return_value = obj_type
        current.environment.return_value = env
        current.path = "/proj/tasks/mydata"
        current.project_uuid.return_value = "proj-uuid"
        impression = mock.MagicMock()
        impression.uuid = "imp-1"
        current.impression.return_value = impression if impressed else None
        return current

    def test_match_renders_success(self):
        current = self._make_current()
        cc = mock.MagicMock()
        cc.verify_data.return_value = {
            "match": True, "expected": "abc", "actual": "abc",
            "location": "runner pkufarm212", "error": None}
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            message = object_creation.verify_data()
        cc.verify_data.assert_called_once_with("proj-uuid", "imp-1")
        self.assertTrue(any("verified" in str(m).lower()
                            for m in message.messages))

    def test_mismatch_renders_error(self):
        current = self._make_current()
        cc = mock.MagicMock()
        cc.verify_data.return_value = {
            "match": False, "expected": "abc", "actual": "xyz",
            "location": "yuki storage", "error": None}
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            message = object_creation.verify_data()
        text = "".join(str(m) for m in message.messages)
        self.assertIn("abc", text)
        self.assertIn("xyz", text)

    def test_non_rawdata_rejected(self):
        current = self._make_current(env="reanahub/x")
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls:
            manager.current_object.return_value = current
            message = object_creation.verify_data()
        cccls.instance.assert_not_called()
        self.assertTrue(any("rawdata" in str(m).lower()
                            for m in message.messages))

    def test_not_impressed_rejected(self):
        current = self._make_current(impressed=False)
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls:
            manager.current_object.return_value = current
            message = object_creation.verify_data()
        cccls.instance.assert_not_called()
        self.assertTrue(any("impress" in str(m).lower()
                            for m in message.messages))

    def test_server_error_surfaced(self):
        current = self._make_current()
        cc = mock.MagicMock()
        cc.verify_data.return_value = {
            "match": False, "expected": "", "actual": "",
            "location": "", "error": "no local data directory"}
        with mock.patch.object(object_creation, "MANAGER") as manager, \
                mock.patch.object(object_creation, "ChernCommunicator") as cccls:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            message = object_creation.verify_data()
        self.assertTrue(any("no local data" in str(m)
                            for m in message.messages))

    def test_cli_command(self):
        from click.testing import CliRunner
        with mock.patch("CelebiChrono.interface.shell.verify_data") as fn:
            result = CliRunner().invoke(verify_data_command, [])
        self.assertEqual(result.exit_code, 0, result.output)
        fn.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
