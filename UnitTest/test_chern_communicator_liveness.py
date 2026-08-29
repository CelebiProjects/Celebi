"""Tests for the liveness communicator methods."""
from unittest import mock

from CelebiChrono.kernel.chern_communicator import ChernCommunicator


def _communicator():
    cherncc = ChernCommunicator.instance()
    cherncc.config_file = mock.MagicMock()
    cherncc.config_file.read_variable.return_value = "dite.example:3315"
    cherncc.timeout = 5
    return cherncc


def test_put_live_set_posts_json():
    """put_live_set PUTs the live/superseded lists to DITE."""
    cherncc = _communicator()
    response = mock.MagicMock()
    response.json.return_value = {"stored": True, "live": 1,
                                  "superseded": 0, "live_workflows": 0}
    with mock.patch("CelebiChrono.kernel.chern_communicator.requests") as req:
        req.put.return_value = response
        result = cherncc.put_live_set("proj", ["a"], ["b"])
    req.put.assert_called_once_with(
        "http://dite.example:3315/live-set/proj",
        json={"live": ["a"], "superseded": ["b"]}, timeout=5)
    response.raise_for_status.assert_called_once_with()
    assert result == {"stored": True, "live": 1, "superseded": 0,
                      "live_workflows": 0}


def test_purge_stale_cache_posts_superseded_scope():
    """purge_stale_cache asks for the superseded scope."""
    cherncc = _communicator()
    response = mock.MagicMock()
    response.json.return_value = {"purged": [], "skipped": [],
                                  "dry_run": True}
    with mock.patch("CelebiChrono.kernel.chern_communicator.requests") as req:
        req.post.return_value = response
        result = cherncc.purge_stale_cache("pkufarm", dry_run=True)
    req.post.assert_called_once_with(
        "http://dite.example:3315/purge-runner-cache",
        json={"runner": "pkufarm", "superseded": True, "dry_run": True},
        timeout=600)
    assert result["dry_run"] is True


def test_purge_stale_workflows_posts_runner():
    """purge_stale_workflows posts the runner and dry-run flag."""
    cherncc = _communicator()
    response = mock.MagicMock()
    response.json.return_value = {"purged": [], "skipped": [],
                                  "dry_run": False}
    with mock.patch("CelebiChrono.kernel.chern_communicator.requests") as req:
        req.post.return_value = response
        cherncc.purge_stale_workflows("pkufarm")
    req.post.assert_called_once_with(
        "http://dite.example:3315/purge-runner-workflows",
        json={"runner": "pkufarm", "dry_run": False}, timeout=600)


def test_purge_stale_cache_posts_project_scope():
    """With project_uuid, the cache purge body carries the project."""
    cherncc = _communicator()
    response = mock.MagicMock()
    response.json.return_value = {"purged": [], "skipped": [],
                                  "dry_run": True}
    with mock.patch("CelebiChrono.kernel.chern_communicator.requests") as req:
        req.post.return_value = response
        cherncc.purge_stale_cache("pkufarm", project_uuid="proj")
    assert req.post.call_args[1]["json"]["project"] == "proj"


def test_purge_stale_workflows_posts_project_scope():
    """With project_uuid, the workflow purge body carries it."""
    cherncc = _communicator()
    response = mock.MagicMock()
    response.json.return_value = {"purged": [], "skipped": [],
                                  "dry_run": True}
    with mock.patch("CelebiChrono.kernel.chern_communicator.requests") as req:
        req.post.return_value = response
        cherncc.purge_stale_workflows("pkufarm", project_uuid="proj")
    assert req.post.call_args[1]["json"]["project_uuid"] == "proj"
