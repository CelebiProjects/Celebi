"""Tests for the purge-ssh-runner-cache shell function."""
import unittest
from unittest import mock

from CelebiChrono.interface.shell_modules import communication


class TestPurgeSshRunnerCacheShellFunction(unittest.TestCase):

    """Test Purge Ssh Runner Cache Shell Function."""

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
        if impression_uuid is None:
            obj.impression.return_value = None
        else:
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

    def test_purge_forwards_explicit_args_and_renders_summary(self):
        """Test purge forwards explicit args and renders summary."""
        cc = self._cherncc(purge_runner_cache=mock.MagicMock(return_value={
            "purged": [{"impression": "imp-a", "kind": "cache"}],
            "skipped": [{"impression": "imp-b",
                         "reason": "registration still running"}],
            "dry_run": False}))
        with mock.patch.object(communication, "ChernCommunicator") as cls:
            cls.instance.return_value = cc
            message = communication.purge_ssh_runner_cache(
                "farm", project="proj", impression="imp-a", dry_run=False)
        cc.purge_runner_cache.assert_called_once_with(
            "farm", project="proj", impression="imp-a", dry_run=False)
        text = str(message)
        self.assertIn("Purged 1 cache entry", text)
        self.assertIn("imp-b", text)
        self.assertIn("registration still running", text)

    def test_purge_uses_current_impression_by_default(self):
        """Test purge defaults to the current impression's scope."""
        cc = self._cherncc(purge_runner_cache=mock.MagicMock(return_value={
            "purged": [], "skipped": [], "dry_run": False}))
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls:
            manager.current_object.return_value = self._current_object()
            cls.instance.return_value = cc
            communication.purge_ssh_runner_cache("farm")
        cc.purge_runner_cache.assert_called_once_with(
            "farm", project="proj", impression="imp-cur", dry_run=False)

    def test_purge_no_impression_errors(self):
        """Test purge errors when the current object has no impression."""
        cc = self._cherncc()
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls:
            manager.current_object.return_value = self._current_object(
                impression_uuid=None)
            cls.instance.return_value = cc
            message = communication.purge_ssh_runner_cache("farm")
        cc.purge_runner_cache.assert_not_called()
        self.assertIn("no impression", str(message))
        self.assertFalse(message.success)

    def test_purge_explicit_impression_skips_context(self):
        """Test purge with an explicit impression does not read the context."""
        cc = self._cherncc(purge_runner_cache=mock.MagicMock(return_value={
            "purged": [], "skipped": [], "dry_run": False}))
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls:
            cls.instance.return_value = cc
            communication.purge_ssh_runner_cache("farm", impression="imp-a")
        manager.current_object.assert_not_called()
        cc.purge_runner_cache.assert_called_once_with(
            "farm", project=None, impression="imp-a", dry_run=False)

    def test_purge_renders_server_error(self):
        """Test purge renders server error."""
        cc = self._cherncc(purge_runner_cache=mock.MagicMock(
            return_value={"error": "not an ssh runner"}))
        with mock.patch.object(communication, "ChernCommunicator") as cls:
            cls.instance.return_value = cc
            message = communication.purge_ssh_runner_cache(
                "local", impression="imp-a")
        self.assertIn("not an ssh runner", str(message))
        self.assertFalse(message.success)

    def test_purge_connection_error(self):
        """Test purge surfaces connection errors."""
        cc = self._cherncc()
        cc.purge_runner_cache.side_effect = ConnectionError("refused")
        with mock.patch.object(communication, "ChernCommunicator") as cls:
            cls.instance.return_value = cc
            message = communication.purge_ssh_runner_cache(
                "farm", impression="imp-a")
        self.assertIn("refused", str(message))
        self.assertFalse(message.success)

    def test_purge_registered_data_hint(self):
        """Test purge hints to restore registered data."""
        cc = self._cherncc(purge_runner_cache=mock.MagicMock(return_value={
            "purged": [{"impression": "imp-a", "kind": "registered"}],
            "skipped": [], "dry_run": False}))
        with mock.patch.object(communication, "ChernCommunicator") as cls:
            cls.instance.return_value = cc
            message = communication.purge_ssh_runner_cache(
                "farm", impression="imp-a")
        self.assertIn("register-ssh-data", str(message))

    def test_purge_dry_run_renders_plan(self):
        """Test purge dry run renders the plan."""
        cc = self._cherncc(purge_runner_cache=mock.MagicMock(return_value={
            "purged": [{"impression": "imp-a", "kind": "cache"}],
            "skipped": [], "dry_run": True}))
        with mock.patch.object(communication, "ChernCommunicator") as cls:
            cls.instance.return_value = cc
            message = communication.purge_ssh_runner_cache(
                "farm", impression="imp-a", dry_run=True)
        self.assertIn("Dry run", str(message))

    def test_purge_folder_fans_out_to_impressed_subobjects(self):
        """Test purge in a folder purges every impressed subobject."""
        sub_a = self._subobject(impression_uuid="abc1234")
        sub_b = self._subobject(impression_uuid="def5678")
        sub_plain = self._subobject(impression_uuid=None)
        cc = self._cherncc(purge_runner_cache=mock.MagicMock(return_value={
            "purged": [{"impression": "imp", "kind": "cache"}],
            "skipped": [], "dry_run": False}))
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls:
            manager.current_object.return_value = self._folder(
                [sub_a, sub_b, sub_plain])
            cls.instance.return_value = cc
            message = communication.purge_ssh_runner_cache("farm")
        self.assertEqual(cc.purge_runner_cache.call_count, 2)
        calls = [(call.kwargs.get("project"), call.kwargs.get("impression"))
                 for call in cc.purge_runner_cache.call_args_list]
        self.assertIn(("proj", "abc1234"), calls)
        self.assertIn(("proj", "def5678"), calls)
        text = str(message)
        self.assertIn("abc1234", text)
        self.assertIn("def5678", text)
        self.assertIn("Total: purged 2 cache entries", text)

    def test_purge_folder_without_impressions_errors(self):
        """Test purge in a folder with no impressed subobjects errors."""
        cc = self._cherncc()
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls:
            manager.current_object.return_value = self._folder(
                [self._subobject(impression_uuid=None)])
            cls.instance.return_value = cc
            message = communication.purge_ssh_runner_cache("farm")
        cc.purge_runner_cache.assert_not_called()
        self.assertIn("no impression", str(message))
        self.assertFalse(message.success)


if __name__ == "__main__":
    unittest.main()
