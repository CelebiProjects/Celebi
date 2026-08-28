"""Tests for ChernCommunicator purge_runner_cache."""
from unittest import mock

import requests

from CelebiChrono.kernel.chern_communicator import ChernCommunicator


class MockResponse:
    """Minimal requests.Response stand-in."""

    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        """Return the canned body."""
        return self._json


def test_purge_runner_cache_posts_to_server():
    """The purge POST carries runner, filters and a long timeout."""
    cc = ChernCommunicator.instance()
    summary = {"purged": [{"impression": "imp-a"}], "skipped": [],
               "dry_run": False}
    with mock.patch("requests.post") as post:
        post.return_value = MockResponse(200, summary)
        result = cc.purge_runner_cache("farm", project="proj",
                                       impression="imp-a", dry_run=False)
        assert result == summary
        post.assert_called_once()
        args, kwargs = post.call_args
        assert args[0].endswith("/purge-runner-cache")
        assert kwargs["json"] == {"runner": "farm", "project": "proj",
                                  "impression": "imp-a", "dry_run": False}
        assert kwargs["timeout"] > 10  # purge runs remote deletes


def test_purge_runner_cache_returns_server_error():
    """A server-side error body is returned as {"error": ...}."""
    cc = ChernCommunicator.instance()
    with mock.patch("requests.post") as post:
        post.return_value = MockResponse(400, {"error": "not an ssh runner"})
        result = cc.purge_runner_cache("local")
        assert result == {"error": "not an ssh runner"}


def test_purge_runner_cache_connection_error():
    """Transport failures raise ConnectionError."""
    cc = ChernCommunicator.instance()
    with mock.patch("requests.post") as post:
        post.side_effect = requests.exceptions.ConnectionError("refused")
        try:
            cc.purge_runner_cache("farm")
        except ConnectionError as e:
            assert "refused" in str(e)
        else:
            raise AssertionError("expected ConnectionError")


def test_cache_results_posts_to_server():
    """The cache-results POST carries runner/project/impression."""
    cc = ChernCommunicator.instance()
    with mock.patch("requests.post") as post:
        post.return_value = MockResponse(200, {"job_id": "job-9"})
        result = cc.cache_results("farm", "proj", "imp1")
        assert result == {"job_id": "job-9"}
        post.assert_called_once()
        args, kwargs = post.call_args
        assert args[0].endswith("/cache-results")
        assert kwargs["json"] == {"runner": "farm", "project_uuid": "proj",
                                  "impression": "imp1"}


def test_cache_results_status_gets_from_server():
    """Job state is polled via GET /cache-results/<job_id>."""
    cc = ChernCommunicator.instance()
    with mock.patch("requests.get") as get:
        get.return_value = MockResponse(200, {"status": "done"})
        result = cc.cache_results_status("job-9")
        assert result["status"] == "done"
        assert get.call_args[0][0].endswith("/cache-results/job-9")


def test_cache_results_returns_server_error():
    """A server-side error body is returned as {"error": ...}."""
    cc = ChernCommunicator.instance()
    with mock.patch("requests.post") as post:
        post.return_value = MockResponse(400, {"error": "not an ssh runner"})
        result = cc.cache_results("local", "proj", "imp1")
        assert result == {"error": "not an ssh runner"}


def test_whereabouts_gets_from_server():
    """The whereabouts GET hits /whereabouts/<project>/<impression>."""
    cc = ChernCommunicator.instance()
    body = {"impression": "imp1", "yuki": {"origin": "collected"},
            "runners": {}, "registered": None, "note": None}
    with mock.patch("requests.get") as get:
        get.return_value = MockResponse(200, body)
        result = cc.whereabouts("proj", "imp1")
        assert result == body
        assert get.call_args[0][0].endswith("/whereabouts/proj/imp1")
