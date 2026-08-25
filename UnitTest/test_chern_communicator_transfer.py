"""Tests for ChernCommunicator transfer methods."""
from unittest import mock

from CelebiChrono.kernel.chern_communicator import ChernCommunicator


class MockResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json


def test_transfer_posts_to_server():
    cc = ChernCommunicator.instance()
    with mock.patch("requests.post") as post:
        post.return_value = MockResponse(200, {"job_id": "abc123"})
        result = cc.transfer("proj", "imp", "runner:pkufarm", "yuki",
                             pattern="*.txt", force=False)
        assert result == {"job_id": "abc123"}
        post.assert_called_once()
        args, kwargs = post.call_args
        assert "/transfer" in args[0]
        assert kwargs["json"]["project_uuid"] == "proj"


def test_transfer_status_gets_from_server():
    cc = ChernCommunicator.instance()
    with mock.patch("requests.get") as get:
        get.return_value = MockResponse(200, {"status": "running"})
        result = cc.transfer_status("abc123")
        assert result["status"] == "running"
