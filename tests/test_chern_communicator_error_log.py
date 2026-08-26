"""Tests for ChernCommunicator error_log offset forwarding."""
from unittest import mock

from CelebiChrono.kernel.chern_communicator import ChernCommunicator


def test_error_log_forwards_offset_to_url():
    """error_log passes the offset as a query parameter to the server."""
    cc = ChernCommunicator.__new__(ChernCommunicator)
    cc.project_uuid = "proj-1"
    cc.timeout = 5

    impression = mock.MagicMock()
    impression.uuid = "imp-1"

    with mock.patch("requests.get") as mock_get:
        mock_get.return_value.text = "log content"
        cc.serverurl = lambda: "localhost:3315"
        result = cc.error_log(impression, 2, offset=42)

    assert result == "log content"
    mock_get.assert_called_once_with(
        "http://localhost:3315/error-log/proj-1/imp-1/2",
        params={"offset": 42},
        timeout=5,
    )


def test_error_log_defaults_to_offset_zero():
    """error_log defaults to offset 0 when no offset is supplied."""
    cc = ChernCommunicator.__new__(ChernCommunicator)
    cc.project_uuid = "proj-1"
    cc.timeout = 5

    impression = mock.MagicMock()
    impression.uuid = "imp-1"

    with mock.patch("requests.get") as mock_get:
        mock_get.return_value.text = "log content"
        cc.serverurl = lambda: "localhost:3315"
        result = cc.error_log(impression, 0)

    assert result == "log content"
    mock_get.assert_called_once_with(
        "http://localhost:3315/error-log/proj-1/imp-1/0",
        params={"offset": 0},
        timeout=5,
    )
