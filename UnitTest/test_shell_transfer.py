"""Tests for the shell transfer function."""
from unittest import mock

from CelebiChrono.interface.shell_modules import file_operations


def test_transfer_no_current_object():
    with mock.patch.object(file_operations.MANAGER, "current_object",
                           return_value=None):
        msg = file_operations.transfer("yuki", "runner:pkufarm")
        assert any("No current object" in m[0] for m in msg.messages)


def test_transfer_polls_until_done():
    current = mock.MagicMock()
    current.project_uuid.return_value = "proj"
    current.impression.return_value = "imp"
    with mock.patch.object(file_operations.MANAGER, "current_object",
                           return_value=current):
        cc = mock.MagicMock()
        cc.transfer.return_value = {"job_id": "abc123"}
        cc.transfer_status.side_effect = [
            {"status": "running", "bytes_done": 0, "bytes_total": 100},
            {"status": "running", "bytes_done": 50, "bytes_total": 100},
            {"status": "done", "report": {"transferred": ["a.txt"],
                                           "skipped": [], "failed": []}},
        ]
        with mock.patch("CelebiChrono.interface.shell_modules.file_operations.ChernCommunicator") as CC:
            CC.instance.return_value = cc
            with mock.patch("time.sleep"):
                msg = file_operations.transfer("yuki", "runner:pkufarm")
    assert any("Transferred 1, skipped 0, failed 0" in m[0] for m in msg.messages)


def test_transfer_aborts_on_consecutive_unknown():
    current = mock.MagicMock()
    current.project_uuid.return_value = "proj"
    current.impression.return_value = "imp"
    with mock.patch.object(file_operations.MANAGER, "current_object",
                           return_value=current):
        cc = mock.MagicMock()
        cc.transfer.return_value = {"job_id": "abc123"}
        cc.transfer_status.return_value = {"status": "unknown",
                                           "error": "job not found"}
        with mock.patch("CelebiChrono.interface.shell_modules.file_operations.ChernCommunicator") as CC:
            CC.instance.return_value = cc
            with mock.patch("time.sleep"):
                msg = file_operations.transfer("yuki", "runner:pkufarm")
    errors = [m[0] for m in msg.messages if m[1] == "error"]
    assert any("unknown" in e and "aborting" in e for e in errors)
    assert cc.transfer_status.call_count == 10
