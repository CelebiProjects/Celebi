"""Tests for the Data registration line in status()."""
import os
import shutil
import tempfile
import unittest
from unittest import mock

from CelebiChrono.interface.shell_modules import task_configuration
from CelebiChrono.utils.message import Message


class TestStatusRegistration(unittest.TestCase):

    """Test the registration line appended by status()."""

    def setUp(self):
        """Set Up."""
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _rawdata_current(self, impression="imp-1"):
        """A current rawdata task object with an impression recorded."""
        with open(os.path.join(self.tmp, "celebi.yaml"), "w",
                  encoding="utf-8") as f:
            f.write("environment: rawdata\n")
        current = mock.MagicMock()
        current.object_type.return_value = "task"
        current.path = self.tmp
        current.config_file = mock.MagicMock()
        current.config_file.read_variable.return_value = impression
        printed = Message()
        printed.add("Status of the object", "info")
        current.printed_status.return_value = printed
        return current

    def _run_status(self, current, state):
        cc = mock.MagicMock()
        cc.register_remote_data_impression_status.return_value = state
        with mock.patch.object(task_configuration, "MANAGER") as manager, \
                mock.patch("CelebiChrono.kernel.chern_communicator."
                           "ChernCommunicator") as cccls:
            manager.current_object.return_value = current
            cccls.instance.return_value = cc
            return task_configuration.status(), cc

    def test_copying_line_with_bytes(self):
        """Copying shows the byte progress."""
        current = self._rawdata_current()
        message, cc = self._run_status(current, {
            "status": "copying",
            "progress": {"bytes_done": 10, "bytes_total": 14,
                         "stage": "copying"}})
        text = "".join(m[0] for m in message.messages)
        self.assertIn("Data registration: copying — 10/14 bytes", text)
        cc.register_remote_data_impression_status.assert_called_once_with(
            "imp-1")

    def test_archived_line(self):
        """A done job shows archived."""
        current = self._rawdata_current()
        message, _cc = self._run_status(current,
                                        {"status": "done", "result": {}})
        text = "".join(m[0] for m in message.messages)
        self.assertIn("Data registration: archived", text)

    def test_failed_line_with_error(self):
        """A failed job shows the error."""
        current = self._rawdata_current()
        message, _cc = self._run_status(current,
                                        {"status": "failed",
                                         "error": "remote copy failed: boom"})
        text = "".join(m[0] for m in message.messages)
        self.assertIn("Data registration: failed — remote copy failed: boom",
                      text)

    def test_no_line_when_no_impression(self):
        """Tasks without an impression do not query the server."""
        current = self._rawdata_current(impression="")
        message, cc = self._run_status(current, None)
        text = "".join(m[0] for m in message.messages)
        self.assertNotIn("Data registration", text)
        cc.register_remote_data_impression_status.assert_not_called()

    def test_no_line_when_not_rawdata(self):
        """Non-rawdata tasks do not query the server."""
        with open(os.path.join(self.tmp, "celebi.yaml"), "w",
                  encoding="utf-8") as f:
            f.write("environment: normal\n")
        current = mock.MagicMock()
        current.object_type.return_value = "task"
        current.path = self.tmp
        printed = Message()
        printed.add("Status of the object", "info")
        current.printed_status.return_value = printed
        message, cc = self._run_status(current, None)
        text = "".join(m[0] for m in message.messages)
        self.assertNotIn("Data registration", text)
        cc.register_remote_data_impression_status.assert_not_called()


if __name__ == "__main__":
    unittest.main()
