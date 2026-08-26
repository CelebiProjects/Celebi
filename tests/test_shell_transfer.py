"""Tests for the shell-level `transfer` function."""
from unittest import mock

import CelebiChrono.interface.shell_modules.file_operations as fo


class _FakeImpression:  # pylint: disable=too-few-public-methods
    """Stand-in for VImpression carrying a uuid."""

    def __init__(self, uuid):
        """Store the uuid."""
        self.uuid = uuid


class _FakeObject:  # pylint: disable=too-few-public-methods
    """Minimal current object providing project_uuid and impression."""

    def __init__(self, project_uuid, impression):
        """Store the values to return."""
        self._project_uuid = project_uuid
        self._impression = impression

    def project_uuid(self):
        """Return the project uuid."""
        return self._project_uuid

    def impression(self):
        """Return the impression (object or None)."""
        return self._impression


class _FakeManager:  # pylint: disable=too-few-public-methods
    """Manager returning a fixed current object."""

    def __init__(self, current):
        """Store the current object."""
        self.current = current

    def current_object(self):
        """Return the current object."""
        return self.current


def _done_state():
    """A terminal 'done' transfer state."""
    return {
        "status": "done",
        "bytes_total": 0,
        "bytes_done": 0,
        "current_file": "",
        "report": {"transferred": [1], "skipped": [], "failed": []},
    }


def test_transfer_sends_impression_uuid_string():
    """transfer sends the impression uuid string, not the VImpression object."""
    fake_obj = _FakeObject("proj-uuid", _FakeImpression("imp-uuid"))
    with mock.patch.object(fo, "MANAGER", new=_FakeManager(fake_obj)), \
         mock.patch.object(fo, "ChernCommunicator") as mock_cc:
        mock_cc.instance.return_value.transfer.return_value = {"job_id": "j1"}
        mock_cc.instance.return_value.transfer_status.return_value = \
            _done_state()
        result = fo.transfer("yuki", "runner:r1")

    mock_cc.instance.return_value.transfer.assert_called_once_with(
        "proj-uuid", "imp-uuid", "yuki", "runner:r1",
        pattern=None, force=False)
    assert result.success
    assert any("Transferred 1" in text for text, _ in result.messages)


def test_transfer_reports_error_when_no_impression():
    """transfer reports an error instead of calling the server without one."""
    fake_obj = _FakeObject("proj-uuid", None)
    with mock.patch.object(fo, "MANAGER", new=_FakeManager(fake_obj)), \
         mock.patch.object(fo, "ChernCommunicator") as mock_cc:
        result = fo.transfer("yuki", "runner:r1")

    mock_cc.instance.return_value.transfer.assert_not_called()
    assert not result.success
    assert any("No project/impression selected" in text
               for text, _ in result.messages)
