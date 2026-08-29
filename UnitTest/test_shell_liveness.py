"""Tests for the shell liveness functions."""
import json
import os
from unittest import mock

from CelebiChrono.interface.shell_modules import communication as comm
from CelebiChrono.utils.message import Message


def _project(tmp_path):
    """A minimal project dir with a .celebi/config.json project_uuid."""
    (tmp_path / ".celebi").mkdir()
    with open(tmp_path / ".celebi" / "config.json", "w",
              encoding="utf-8") as f:
        json.dump({"project_uuid": "proj-1"}, f)
    return str(tmp_path)


def test_sync_live_pushes_sets(monkeypatch, tmp_path):
    """sync_live computes the sets and pushes them to DITE."""
    project = _project(tmp_path)
    monkeypatch.setattr("CelebiChrono.utils.path_utils.project_path",
                        lambda: project)
    cherncc = mock.MagicMock()
    cherncc.put_live_set.return_value = {"stored": True, "live": 0,
                                         "superseded": 0,
                                         "live_workflows": 0}
    with mock.patch.object(comm, "ChernCommunicator") as cc:
        cc.instance.return_value = cherncc
        result = comm.sync_live()
    assert isinstance(result, Message)
    cherncc.put_live_set.assert_called_once_with(
        "proj-1", mock.ANY, mock.ANY)


def test_sync_live_failure_is_a_warning(monkeypatch, tmp_path):
    """A failing push returns a Message, never raises."""
    project = _project(tmp_path)
    monkeypatch.setattr("CelebiChrono.utils.path_utils.project_path",
                        lambda: project)
    cherncc = mock.MagicMock()
    cherncc.put_live_set.side_effect = ConnectionError("down")
    with mock.patch.object(comm, "ChernCommunicator") as cc:
        cc.instance.return_value = cherncc
        result = comm.sync_live()  # no raise
    assert isinstance(result, Message)


def test_purge_stale_cache_delegates():
    cherncc = mock.MagicMock()
    cherncc.purge_stale_cache.return_value = {"purged": [], "skipped": [],
                                              "dry_run": True}
    with mock.patch.object(comm, "ChernCommunicator") as cc:
        cc.instance.return_value = cherncc
        result = comm.purge_stale_cache("pkufarm", dry_run=True)
    cherncc.purge_stale_cache.assert_called_once_with(
        "pkufarm", dry_run=True)
    assert isinstance(result, Message)
    assert result.data["purge_count"] == 0


def test_purge_stale_workflows_delegates():
    cherncc = mock.MagicMock()
    cherncc.purge_stale_workflows.return_value = {"purged": [],
                                                  "skipped": [],
                                                  "dry_run": False}
    with mock.patch.object(comm, "ChernCommunicator") as cc:
        cc.instance.return_value = cherncc
        result = comm.purge_stale_workflows("pkufarm")
    cherncc.purge_stale_workflows.assert_called_once_with(
        "pkufarm", dry_run=False)
    assert isinstance(result, Message)
    assert result.data["purge_count"] == 0
    assert isinstance(result, Message)


def test_purge_stale_cache_syncs_live_first():
    """purge_stale_cache pushes the live set before purging."""
    cherncc = mock.MagicMock()
    cherncc.purge_stale_cache.return_value = {"purged": [], "skipped": [],
                                              "dry_run": True}
    with mock.patch.object(comm, "ChernCommunicator") as cc, \
            mock.patch.object(comm, "sync_live") as sync:
        cc.instance.return_value = cherncc
        sync.return_value = Message()
        result = comm.purge_stale_cache("pkufarm", dry_run=True)
    sync.assert_called_once_with()
    cherncc.purge_stale_cache.assert_called_once_with(
        "pkufarm", dry_run=True)
    assert isinstance(result, Message)


def test_purge_stale_cache_proceeds_when_sync_warns():
    """A failed sync (warning Message) never blocks the purge."""
    cherncc = mock.MagicMock()
    cherncc.purge_stale_cache.return_value = {"purged": [], "skipped": [],
                                              "dry_run": False}
    sync = Message()
    sync.add("Live-set sync failed (safe to ignore): down", "warning")
    with mock.patch.object(comm, "ChernCommunicator") as cc, \
            mock.patch.object(comm, "sync_live", return_value=sync):
        cc.instance.return_value = cherncc
        result = comm.purge_stale_cache("pkufarm")
    cherncc.purge_stale_cache.assert_called_once_with(
        "pkufarm", dry_run=False)
    assert isinstance(result, Message)
    assert any("sync failed" in text for text, _ in result.messages)


def test_purge_stale_workflows_syncs_live_first():
    """purge_stale_workflows pushes the live set before purging."""
    cherncc = mock.MagicMock()
    cherncc.purge_stale_workflows.return_value = {"purged": [],
                                                  "skipped": [],
                                                  "dry_run": False}
    with mock.patch.object(comm, "ChernCommunicator") as cc, \
            mock.patch.object(comm, "sync_live") as sync:
        cc.instance.return_value = cherncc
        sync.return_value = Message()
        comm.purge_stale_workflows("pkufarm")
    sync.assert_called_once_with()
    cherncc.purge_stale_workflows.assert_called_once_with(
        "pkufarm", dry_run=False)
