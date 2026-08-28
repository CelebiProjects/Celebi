"""Tests for the cache-results shell function."""
import unittest
from unittest import mock

from CelebiChrono.interface.shell_modules import communication


class TestCacheResultsShellFunction(unittest.TestCase):

    """Test Cache Results Shell Function."""

    def _cherncc(self, **attrs):
        """Cherncc."""
        cc = mock.MagicMock()
        for key, value in attrs.items():
            setattr(cc, key, value)
        return cc

    def _current_object(self, project="proj", impression_uuid="imp-cur"):
        """A current-object stub with the given impression scope."""
        obj = mock.MagicMock()
        obj.object_type.return_value = "task"
        obj.project_uuid.return_value = project
        imp = mock.MagicMock()
        imp.uuid = impression_uuid
        obj.impression.return_value = imp
        return obj

    def _subobject(self, project="proj", impression_uuid=None):
        """A subobject stub with the given impression scope."""
        obj = mock.MagicMock()
        obj.project_uuid.return_value = project
        if impression_uuid is None:
            obj.impression.return_value = None
        else:
            imp = mock.MagicMock()
            imp.uuid = impression_uuid
            obj.impression.return_value = imp
        return obj

    def _folder(self, subobjects):
        """A folder stub whose recursive walk yields the subobjects."""
        folder = mock.MagicMock()
        folder.object_type.return_value = "directory"
        folder.sub_objects_recursively.return_value = subobjects
        return folder

    def test_cache_results_uses_context_and_polls(self):
        """Test cache results uses the current impression and polls to done."""
        cc = self._cherncc(
            cache_results=mock.MagicMock(return_value={"job_id": "job-9"}),
            cache_results_status=mock.MagicMock(side_effect=[
                {"status": "copying"},
                {"status": "done", "result": {"cached": 3, "bytes": 33}},
            ]))
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls, \
                mock.patch.object(communication.time, "sleep"), \
                mock.patch("builtins.print"):
            manager.current_object.return_value = self._current_object()
            cls.instance.return_value = cc
            message = communication.cache_results("farm")
        cc.cache_results.assert_called_once_with("farm", "proj", "imp-cur")
        self.assertIn("Cached 3 files", str(message))
        self.assertTrue(message.success)

    def test_cache_results_no_impression_errors(self):
        """Test cache results errors without an impression."""
        obj = mock.MagicMock()
        obj.project_uuid.return_value = "proj"
        obj.impression.return_value = None
        cc = self._cherncc()
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls:
            manager.current_object.return_value = obj
            cls.instance.return_value = cc
            message = communication.cache_results("farm")
        cc.cache_results.assert_not_called()
        self.assertIn("no impression", str(message))
        self.assertFalse(message.success)

    def test_cache_results_server_error(self):
        """Test cache results renders server errors."""
        cc = self._cherncc(cache_results=mock.MagicMock(
            return_value={"error": "not an ssh runner"}))
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls:
            manager.current_object.return_value = self._current_object()
            cls.instance.return_value = cc
            message = communication.cache_results("local")
        self.assertIn("not an ssh runner", str(message))
        self.assertFalse(message.success)

    def test_cache_results_failed_status(self):
        """Test cache results surfaces a failed job."""
        cc = self._cherncc(
            cache_results=mock.MagicMock(return_value={"job_id": "job-9"}),
            cache_results_status=mock.MagicMock(return_value={
                "status": "failed", "error": "remote copy failed"}))
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls, \
                mock.patch.object(communication.time, "sleep"), \
                mock.patch("builtins.print"):
            manager.current_object.return_value = self._current_object()
            cls.instance.return_value = cc
            message = communication.cache_results("farm")
        self.assertIn("remote copy failed", str(message))
        self.assertFalse(message.success)

    def test_cache_results_unknown_status_bailout(self):
        """Test cache results gives up after 10 consecutive unknowns."""
        cc = self._cherncc(
            cache_results=mock.MagicMock(return_value={"job_id": "job-9"}),
            cache_results_status=mock.MagicMock(
                return_value={"status": "unknown"}))
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls, \
                mock.patch.object(communication.time, "sleep") as sleep, \
                mock.patch("builtins.print"):
            manager.current_object.return_value = self._current_object()
            cls.instance.return_value = cc
            message = communication.cache_results("farm")
        self.assertEqual(sleep.call_count, 10)
        self.assertIn("giving up", str(message))
        self.assertFalse(message.success)

    def test_cache_results_connection_error(self):
        """Test cache results surfaces connection errors."""
        cc = self._cherncc()
        cc.cache_results.side_effect = ConnectionError("refused")
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls:
            manager.current_object.return_value = self._current_object()
            cls.instance.return_value = cc
            message = communication.cache_results("farm")
        self.assertIn("refused", str(message))
        self.assertFalse(message.success)

    def test_cache_results_folder_fans_out(self):
        """Test cache results in a folder starts a job per impression."""
        cc = self._cherncc(
            cache_results=mock.MagicMock(
                side_effect=[{"job_id": "job-1"}, {"job_id": "job-2"}]),
            cache_results_status=mock.MagicMock(side_effect=[
                {"status": "done", "result": {"cached": 3, "bytes": 33}},
                {"status": "done", "result": {"cached": 2, "bytes": 22}},
            ]))
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls, \
                mock.patch.object(communication.time, "sleep"), \
                mock.patch("builtins.print"):
            manager.current_object.return_value = self._folder([
                self._subobject(impression_uuid="abc1234"),
                self._subobject(impression_uuid="def5678"),
                self._subobject(impression_uuid=None),
            ])
            cls.instance.return_value = cc
            message = communication.cache_results("farm")
        self.assertEqual(cc.cache_results.call_count, 2)
        calls = [(call.args[1], call.args[2])
                 for call in cc.cache_results.call_args_list]
        self.assertIn(("proj", "abc1234"), calls)
        self.assertIn(("proj", "def5678"), calls)
        text = str(message)
        self.assertIn("abc1234", text)
        self.assertIn("def5678", text)
        self.assertIn("Total: cached 5 files", text)
        self.assertTrue(message.success)

    def test_cache_results_folder_without_impressions_errors(self):
        """Test cache results in an empty folder errors."""
        cc = self._cherncc()
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls:
            manager.current_object.return_value = self._folder(
                [self._subobject(impression_uuid=None)])
            cls.instance.return_value = cc
            message = communication.cache_results("farm")
        cc.cache_results.assert_not_called()
        self.assertIn("no impression", str(message))
        self.assertFalse(message.success)


if __name__ == "__main__":
    unittest.main()
