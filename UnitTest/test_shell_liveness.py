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


def test_purge_stale_cache_delegates(monkeypatch, tmp_path):
    project = _project(tmp_path)
    monkeypatch.setattr("CelebiChrono.utils.path_utils.project_path",
                        lambda: project)
    cherncc = mock.MagicMock()
    cherncc.purge_stale_cache.return_value = {"purged": [], "skipped": [],
                                              "dry_run": True}
    with mock.patch.object(comm, "ChernCommunicator") as cc:
        cc.instance.return_value = cherncc
        result = comm.purge_stale_cache("pkufarm", dry_run=True)
    cherncc.purge_stale_cache.assert_called_once_with(
        "pkufarm", dry_run=True, project_uuid="proj-1")
    assert isinstance(result, Message)
    assert result.data["purge_count"] == 0


def test_purge_stale_workflows_delegates(monkeypatch, tmp_path):
    project = _project(tmp_path)
    monkeypatch.setattr("CelebiChrono.utils.path_utils.project_path",
                        lambda: project)
    cherncc = mock.MagicMock()
    cherncc.purge_stale_workflows.return_value = {"purged": [],
                                                  "skipped": [],
                                                  "dry_run": False}
    with mock.patch.object(comm, "ChernCommunicator") as cc:
        cc.instance.return_value = cherncc
        result = comm.purge_stale_workflows("pkufarm")
    cherncc.purge_stale_workflows.assert_called_once_with(
        "pkufarm", dry_run=False, project_uuid="proj-1")
    assert isinstance(result, Message)
    assert result.data["purge_count"] == 0
    assert isinstance(result, Message)


def test_purge_stale_cache_syncs_live_first(monkeypatch, tmp_path):
    """purge_stale_cache pushes the live set before purging."""
    monkeypatch.setattr("CelebiChrono.utils.path_utils.project_path",
                        lambda: _project(tmp_path))
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
        "pkufarm", dry_run=True, project_uuid="proj-1")
    assert isinstance(result, Message)


def test_purge_stale_cache_proceeds_when_sync_warns(monkeypatch,
                                                        tmp_path):
    """A failed sync (warning Message) never blocks the purge."""
    monkeypatch.setattr("CelebiChrono.utils.path_utils.project_path",
                        lambda: _project(tmp_path))
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
        "pkufarm", dry_run=False, project_uuid="proj-1")
    assert isinstance(result, Message)
    assert any("sync failed" in text for text, _ in result.messages)


def test_purge_stale_workflows_syncs_live_first(monkeypatch, tmp_path):
    """purge_stale_workflows pushes the live set before purging."""
    monkeypatch.setattr("CelebiChrono.utils.path_utils.project_path",
                        lambda: _project(tmp_path))
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
        "pkufarm", dry_run=False, project_uuid="proj-1")


def test_purge_stale_cache_no_project_returns_error(monkeypatch):
    """Without a project, the purge refuses to run (never touches other
    projects)."""
    monkeypatch.setattr("CelebiChrono.utils.path_utils.project_path",
                        lambda: None)
    with mock.patch.object(comm, "ChernCommunicator") as cc:
        result = comm.purge_stale_cache("pkufarm")
    cc.instance.assert_not_called()
    assert any("No project" in text for text, _ in result.messages)


def test_purge_stale_workflows_no_project_returns_error(monkeypatch):
    """Without a project, the workflow purge refuses to run."""
    monkeypatch.setattr("CelebiChrono.utils.path_utils.project_path",
                        lambda: None)
    with mock.patch.object(comm, "ChernCommunicator") as cc:
        result = comm.purge_stale_workflows("pkufarm")
    cc.instance.assert_not_called()
    assert any("No project" in text for text, _ in result.messages)


def test_purge_stale_workflows_reports_already_gone(monkeypatch, tmp_path):
    """already_gone entries are summarized in one line."""
    monkeypatch.setattr("CelebiChrono.utils.path_utils.project_path",
                        lambda: _project(tmp_path))
    cherncc = mock.MagicMock()
    cherncc.purge_stale_workflows.return_value = {"purged": [],
                                                  "skipped": [],
                                                  "already_gone": 3,
                                                  "dry_run": False}
    with mock.patch.object(comm, "ChernCommunicator") as cc:
        cc.instance.return_value = cherncc
        result = comm.purge_stale_workflows("pkufarm")
    assert any("3 workspace(s) already gone" in text
               for text, _ in result.messages)


def test_purge_lines_omit_project_uuid(monkeypatch, tmp_path):
    """Purged/skipped lines name only the workflow — the purge is
    already scoped to the current project."""
    monkeypatch.setattr("CelebiChrono.utils.path_utils.project_path",
                        lambda: _project(tmp_path))
    cherncc = mock.MagicMock()
    cherncc.purge_stale_workflows.return_value = {
        "purged": [{"project": "proj-1", "workflow": "wf-1"}],
        "skipped": [{"project": "proj-1", "workflow": "wf-2",
                     "reason": "live"}],
        "already_gone": 0, "dry_run": True}
    with mock.patch.object(comm, "ChernCommunicator") as cc:
        cc.instance.return_value = cherncc
        result = comm.purge_stale_workflows("pkufarm")
    texts = [text for text, _ in result.messages]
    assert sum(t.strip() == "Purged workflow:" for t in texts) == 1
    assert any(t.strip() == "wf-1" for t in texts)
    assert sum(t.strip() == "Skipped workflow:" for t in texts) == 1
    assert any(t.strip() == "wf-2 — live" for t in texts)
    assert not any("proj-1" in t for t in texts)


def test_cache_purge_lines_omit_project_uuid(monkeypatch, tmp_path):
    """Cache purge lines name only the impression."""
    monkeypatch.setattr("CelebiChrono.utils.path_utils.project_path",
                        lambda: _project(tmp_path))
    cherncc = mock.MagicMock()
    cherncc.purge_stale_cache.return_value = {
        "purged": [{"project": "proj-1", "impression": "imp-1"}],
        "skipped": [{"project": "proj-1", "impression": "imp-2",
                     "reason": "registered"}],
        "dry_run": True}
    with mock.patch.object(comm, "ChernCommunicator") as cc:
        cc.instance.return_value = cherncc
        result = comm.purge_stale_cache("pkufarm")
    texts = [text for text, _ in result.messages]
    assert any("[imp-1] would be purged in cache" in t for t in texts)
    assert any("[imp-2] skipped in cache — registered" in t for t in texts)
    assert not any("proj-1" in t for t in texts)


def test_kill_workflow_delegates(monkeypatch, tmp_path):
    """kill_workflow resolves the current project and delegates."""
    monkeypatch.setattr("CelebiChrono.utils.path_utils.project_path",
                        lambda: _project(tmp_path))
    cherncc = mock.MagicMock()
    cherncc.kill_workflow.return_value = {"status": "killed",
                                          "workflow": "wf-1"}
    with mock.patch.object(comm, "ChernCommunicator") as cc:
        cc.instance.return_value = cherncc
        result = comm.kill_workflow("wf-1")
    cherncc.kill_workflow.assert_called_once_with("proj-1", "wf-1")
    assert any("wf-1" in text for text, _ in result.messages)


def test_kill_workflow_no_project_returns_error(monkeypatch):
    """Without a project, kill_workflow refuses to run."""
    monkeypatch.setattr("CelebiChrono.utils.path_utils.project_path",
                        lambda: None)
    with mock.patch.object(comm, "ChernCommunicator") as cc:
        result = comm.kill_workflow("wf-1")
    cc.instance.assert_not_called()
    assert any("No project" in text for text, _ in result.messages)
