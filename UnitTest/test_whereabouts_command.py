"""Tests for the whereabouts shell function."""
import unittest
from unittest import mock

from CelebiChrono.interface.shell_modules import communication


class TestWhereaboutsShellFunction(unittest.TestCase):

    """Test Whereabouts Shell Function."""

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

    def test_whereabouts_renders_locations(self):
        """Test whereabouts renders yuki, runner states, and registration."""
        cc = self._cherncc(whereabouts=mock.MagicMock(return_value={
            "impression": "imp-cur",
            "yuki": {"origin": "collected", "files": 3, "bytes": 10},
            "runners": {"pkufarm212": {
                "workflow": {"origin": "produced", "files": 2},
                "cache": {"origin": "transferred", "files": 3, "bytes": 10},
            }},
            "registered": {"host_runner": "pkufarm212",
                           "source_path": "/data/src"},
            "note": None,
        }))
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls:
            manager.current_object.return_value = self._current_object()
            cls.instance.return_value = cc
            message = communication.whereabouts()
        cc.whereabouts.assert_called_once_with("proj", "imp-cur")
        text = str(message)
        self.assertIn("yuki", text)
        self.assertIn("collected", text)
        self.assertIn("pkufarm212", text)
        self.assertIn("transferred", text)
        self.assertIn("registered", text)
        self.assertIn("on pkufarm212", text)
        self.assertIn("/data/src", text)
        self.assertTrue(message.success)

    def test_whereabouts_rows_align(self):
        """Test whereabouts rows keep fixed column widths across locations."""
        cc = self._cherncc(whereabouts=mock.MagicMock(return_value={
            "impression": "imp-cur",
            "yuki": {"origin": "collected", "files": 3, "bytes": 10},
            "runners": {
                "cern": {"workflow": {"origin": "produced", "files": 1}},
                "pkufarm212": {
                    "cache": {"origin": "transferred", "files": 3},
                },
            },
            "registered": None,
            "note": None,
        }))
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls:
            manager.current_object.return_value = self._current_object()
            cls.instance.return_value = cc
            message = communication.whereabouts()
        lines = [text for text, _tag in message.messages]
        self.assertIn("  yuki                  ✓ collected      3 files · 10 B",
                      lines)
        self.assertIn(
            "  cern         workflow ✓ produced       1 files · "
            "cache    ✗ —              0 files", lines)
        self.assertIn(
            "  pkufarm212   workflow ✗ —              0 files · "
            "cache    ✓ transferred    3 files", lines)
        # The first mark of every row starts in the same column.
        marks = []
        for line in lines:
            if "Data whereabouts" in line:
                continue
            positions = [line.find(mark) for mark in ("✓", "✗")]
            marks.append(min(p for p in positions if p >= 0))
        self.assertEqual(len(set(marks)), 1)

    def test_whereabouts_no_impression_errors(self):
        """Test whereabouts errors without an impression."""
        obj = mock.MagicMock()
        obj.object_type.return_value = "task"
        obj.project_uuid.return_value = "proj"
        obj.impression.return_value = None
        cc = self._cherncc()
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls:
            manager.current_object.return_value = obj
            cls.instance.return_value = cc
            message = communication.whereabouts()
        cc.whereabouts.assert_not_called()
        self.assertIn("no impression", str(message))
        self.assertFalse(message.success)

    def test_whereabouts_note_and_missing_states(self):
        """Test whereabouts renders the note and absent states."""
        cc = self._cherncc(whereabouts=mock.MagicMock(return_value={
            "impression": "imp-cur",
            "yuki": None,
            "runners": {"pkufarm212": {}},
            "registered": None,
            "note": "distribution.json not recorded",
        }))
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls:
            manager.current_object.return_value = self._current_object()
            cls.instance.return_value = cc
            message = communication.whereabouts()
        text = str(message)
        self.assertIn("distribution.json not recorded", text)
        self.assertIn("not in local storage", text)

    def test_whereabouts_folder_fans_out(self):
        """Test whereabouts in a folder reports every impressed subobject."""
        cc = self._cherncc(whereabouts=mock.MagicMock(side_effect=[
            {"impression": "abc1234", "yuki": None, "runners": {},
             "registered": None, "note": "distribution.json not recorded"},
            {"impression": "def5678", "yuki": {"origin": "collected",
                                              "files": 1, "bytes": 5},
             "runners": {}, "registered": None, "note": None},
        ]))
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls:
            manager.current_object.return_value = self._folder([
                self._subobject(impression_uuid="abc1234"),
                self._subobject(impression_uuid="def5678"),
                self._subobject(impression_uuid=None),
            ])
            cls.instance.return_value = cc
            message = communication.whereabouts()
        self.assertEqual(cc.whereabouts.call_count, 2)
        text = str(message)
        self.assertIn("abc1234", text)
        self.assertIn("def5678", text)

    def test_whereabouts_connection_error(self):
        """Test whereabouts surfaces connection errors."""
        cc = self._cherncc()
        cc.whereabouts.side_effect = ConnectionError("refused")
        with mock.patch.object(communication, "MANAGER") as manager, \
                mock.patch.object(communication, "ChernCommunicator") as cls:
            manager.current_object.return_value = self._current_object()
            cls.instance.return_value = cc
            message = communication.whereabouts()
        self.assertIn("refused", str(message))
        self.assertFalse(message.success)


if __name__ == "__main__":
    unittest.main()
