# celebi (CelebiChrono): `celebi book` Client Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `celebi book` publishes a project's canonical impressions (output file lists + plots) to a celebi_server booking instance in one command: git guard → server-side impress → local impress → Yuki pack → sync → Yuki upload → report. `celebi register-celebi-server` stores the server URL.

**Architecture:** A new shell module `interface/shell_modules/server_booking.py` holds the orchestration (one public `book()` + `register_celebi_server()`), reusing `reana_booking._consume_ndjson_stream` for Yuki progress and `metadata.ConfigFile` for `hosts.json`. Git interaction is a thin `_run_git` wrapper so tests monkeypatch one seam. The CLI surface is two click commands in `celebi_cli/commands/booking.py`, wired in `cli.py`. The user bearer token goes only to celebi_server; Yuki receives only the scoped grant.

**Tech Stack:** click, requests, subprocess git, pytest.

**Spec:** `/Users/wave/workdir/Celebi/celebi_server/docs/superpowers/specs/2026-09-07-celebi-booking-design.md` (§celebi additions, §booking flow)

## Global Constraints

- Impression uuids validated against `^[0-9a-f]{32}$` on every hop.
- User bearer token is sent ONLY to celebi_server (`Authorization: Bearer <token>`). Yuki receives ONLY the grant from the sync response. The token is never placed in a Yuki request body.
- Server endpoints used (verified against celebi_server routes):
  - `POST /api/projects/{uuid}/impress` (bearer) → 202 job record `{job_id, status, impressions, error, log_tail, ...}`; `GET /api/projects/{uuid}/impress/{job_id}` for polling. status ∈ pending|running|succeeded|failed.
  - `POST /api/projects/{uuid}/impressions/sync` (bearer) body `{"manifest": [...]}` → `{to_upload, to_download, grant}`. Every manifest entry MUST have string `uuid` and string `sha256` (422 otherwise) — manifest = packed impressions only.
- Yuki endpoints used (implemented by the Yuki plan): `POST /book-celebi-server/pack` body `{"project_uuid", "impressions": [uuid...]}` → NDJSON, final data `{"packed": [{"uuid","path","sha256","size","file_count"}], "missing": [...]}`; `POST /book-celebi-server/upload` body `{"celebi_server_url", "project_uuid", "archives": [{"uuid","sha256","size"}], "grant"}` → NDJSON, final data `{"uploaded": [...], "failed": [{"uuid","error"}]}`.
- Booking flow order is fixed: pack → sync → upload (archive sha256 must be declared before the grant is issued).
- Invariant: `to_upload ⊆ packed uuids` — extras are a hard error naming them.
- Local impress is idempotent (`is_impressed_fast`); re-running `book` on an unchanged project is a no-op upload-wise (server delta returns empty to_upload).
- Errors are reported through the `Message` class (`message.add(text, "error")`); commands print `message.colored()`; `Message.success` false if any error was added.

---

### Task 1: `server_booking.py` — URL resolution + git guard + helpers

**Files:**
- Create: `CelebiChrono/interface/shell_modules/server_booking.py`
- Test: `tests/test_celebi_cli_booking.py`

**Interfaces:**
- Produces:
  - `_get_celebi_server_url(server_url="") -> str` — precedence: argument > `$CELEBI_SERVER_URL` > hosts.json `celebi_server_url`; "" if unset.
  - `register_celebi_server(server_url="") -> Message` — writes hosts.json `celebi_server_url` (via `metadata.ConfigFile`); validates URL starts with http:// or https://.
  - `_run_git(project_path, args) -> subprocess.CompletedProcess` — `subprocess.run(["git", *args], cwd=project_path, capture_output=True, text=True)`.
  - `_git_guard(project_path, message) -> str` — returns HEAD sha on success; adds error to `message` and returns "" on failure:
    - not a git work tree → "not a git repository"
    - `git status --porcelain` non-empty → "working tree is not clean"
    - no upstream (`git rev-parse --abbrev-ref --symbolic-full-name @{u}` rc≠0) → "no upstream branch configured"
    - `git rev-list --left-right --count HEAD...@{u}` → "0\t0" ok; "N\t0" → `git push`, push rc≠0 → error; "0\tM" → error "behind upstream — pull first"; diverged → error
  - `_build_manifest(project_path, packed, git_commit) -> list[dict]` — one entry per packed archive: `{"uuid", "sha256", "size", "git_commit", "parents"}` where `parents` is read from `.celebi/impressions/<uuid>/config.json` (`parents`, default `[]`).
  - `_check_upload_subset(to_upload, packed_uuids, message) -> bool` — false + error naming extras if `to_upload ⊄ packed`.
  - `UUID32_RE = re.compile(r"^[0-9a-f]{32}$")`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_celebi_cli_booking.py
"""Tests for celebi_server booking (book / register-celebi-server)."""
import json
import os
import re

import pytest

from CelebiChrono.interface.shell_modules import server_booking as sb
from CelebiChrono.utils.message import Message


# --- URL resolution ---------------------------------------------------------

def test_server_url_precedence_argument(tmp_path, monkeypatch):
    monkeypatch.setenv("CELEBI_SERVER_URL", "http://env:1")
    assert sb._get_celebi_server_url("http://arg:2") == "http://arg:2"


def test_server_url_env_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("CELEBI_SERVER_URL", "http://env:1")
    monkeypatch.chdir(tmp_path)   # no hosts.json here
    assert sb._get_celebi_server_url("") == "http://env:1"


def test_server_url_hosts_json(tmp_path, monkeypatch):
    monkeypatch.delenv("CELEBI_SERVER_URL", raising=False)
    os.makedirs(tmp_path / ".celebi")
    with open(tmp_path / ".celebi" / "hosts.json", "w") as f:
        json.dump({"celebi_server_url": "http://hosts:3"}, f)
    monkeypatch.chdir(tmp_path)
    assert sb._get_celebi_server_url("") == "http://hosts:3"


def test_server_url_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("CELEBI_SERVER_URL", raising=False)
    monkeypatch.chdir(tmp_path)
    assert sb._get_celebi_server_url("") == ""


def test_register_celebi_server_writes_hosts(tmp_path, monkeypatch):
    monkeypatch.delenv("CELEBI_SERVER_URL", raising=False)
    os.makedirs(tmp_path / ".celebi")
    monkeypatch.chdir(tmp_path)
    msg = sb.register_celebi_server("http://server:3320")
    assert msg.success
    with open(tmp_path / ".celebi" / "hosts.json") as f:
        assert json.load(f)["celebi_server_url"] == "http://server:3320"


def test_register_rejects_bad_scheme(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    msg = sb.register_celebi_server("ftp://nope")
    assert not msg.success


# --- git guard --------------------------------------------------------------

class FakeGit:
    """Monkeypatch sb._run_git with scripted answers."""

    def __init__(self, mapping):
        self.mapping = mapping          # tuple(args) -> (rc, stdout)
        self.calls = []

    def __call__(self, project_path, args):
        import subprocess
        self.calls.append(list(args))
        rc, out = self.mapping.get(tuple(args), (1, ""))
        return subprocess.CompletedProcess(["git", *args], rc, stdout=out,
                                           stderr="")


def test_git_guard_clean_up_to_date(tmp_path, monkeypatch):
    f = FakeGit({
        ("rev-parse", "--is-inside-work-tree"): (0, "true\n"),
        ("status", "--porcelain"): (0, ""),
        ("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"):
            (0, "origin/master\n"),
        ("rev-list", "--left-right", "--count", "HEAD...@{u}"): (0, "0\t0\n"),
        ("rev-parse", "HEAD"): (0, "abc123\n"),
    })
    monkeypatch.setattr(sb, "_run_git", f)
    msg = Message()
    assert sb._git_guard(str(tmp_path), msg) == "abc123"
    assert msg.success


def test_git_guard_pushes_when_ahead(tmp_path, monkeypatch):
    f = FakeGit({
        ("rev-parse", "--is-inside-work-tree"): (0, "true\n"),
        ("status", "--porcelain"): (0, ""),
        ("rev-parse", "--abbrev-ref", "--symbolic-full-code", "@{u}"): None,
        ("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"):
            (0, "origin/master\n"),
        ("rev-list", "--left-right", "--count", "HEAD...@{u}"): (0, "2\t0\n"),
        ("push",): (0, ""),
        ("rev-parse", "HEAD"): (0, "abc123\n"),
    })
    monkeypatch.setattr(sb, "_run_git", f)
    msg = Message()
    assert sb._git_guard(str(tmp_path), msg) == "abc123"
    assert ("push",) in [tuple(c) for c in f.calls]


def test_git_guard_dirty_tree(tmp_path, monkeypatch):
    f = FakeGit({
        ("rev-parse", "--is-inside-work-tree"): (0, "true\n"),
        ("status", "--porcelain"): (0, " M celebi.yaml\n"),
    })
    monkeypatch.setattr(sb, "_run_git", f)
    msg = Message()
    assert sb._git_guard(str(tmp_path), msg) == ""
    assert not msg.success


def test_git_guard_behind(tmp_path, monkeypatch):
    f = FakeGit({
        ("rev-parse", "--is-inside-work-tree"): (0, "true\n"),
        ("status", "--porcelain"): (0, ""),
        ("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"):
            (0, "origin/master\n"),
        ("rev-list", "--left-right", "--count", "HEAD...@{u}"): (0, "0\t3\n"),
    })
    monkeypatch.setattr(sb, "_run_git", f)
    msg = Message()
    assert sb._git_guard(str(tmp_path), msg) == ""
    assert not msg.success


# --- manifest ---------------------------------------------------------------

def test_build_manifest_reads_parents(tmp_path):
    imp = "a" * 32
    imp_dir = tmp_path / ".celebi" / "impressions" / imp
    imp_dir.mkdir(parents=True)
    with open(imp_dir / "config.json", "w") as f:
        json.dump({"parents": ["b" * 32]}, f)
    packed = [{"uuid": imp, "sha256": "s" * 64, "size": 10}]
    manifest = sb._build_manifest(str(tmp_path), packed, "abc")
    assert manifest == [{
        "uuid": imp, "sha256": "s" * 64, "size": 10,
        "git_commit": "abc", "parents": ["b" * 32],
    }]


def test_build_manifest_defaults_parents_empty(tmp_path):
    imp = "a" * 32
    imp_dir = tmp_path / ".celebi" / "impressions" / imp
    imp_dir.mkdir(parents=True)
    with open(imp_dir / "config.json", "w") as f:
        json.dump({}, f)
    manifest = sb._build_manifest(
        str(tmp_path), [{"uuid": imp, "sha256": "s", "size": 1}], "abc")
    assert manifest[0]["parents"] == []


# --- invariant --------------------------------------------------------------

def test_upload_subset_ok():
    msg = Message()
    assert sb._check_upload_subset([{"uuid": "a" * 32}], {"a" * 32}, msg)
    assert msg.success


def test_upload_subset_violation_named():
    msg = Message()
    extra = "e" * 32
    assert not sb._check_upload_subset([{"uuid": extra}], {"a" * 32}, msg)
    assert extra in msg.messages[0][0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_celebi_cli_booking.py -x`
Expected: FAIL (`ModuleNotFoundError: CelebiChrono.interface.shell_modules.server_booking`)

- [ ] **Step 3: Implement**

Create `CelebiChrono/interface/shell_modules/server_booking.py`:

```python
"""celebi_server booking: `celebi book` orchestration.

Flow (spec: docs/superpowers/specs/2026-09-07-celebi-booking-design.md):
  1. git guard (clean tree, upstream, push if ahead)
  2. server-side impress on celebi_server (POST /api/projects/{uuid}/impress)
  3. local impress (idempotent; uuids are content-derived so both agree)
  4. pack via Yuki  (POST /book-celebi-server/pack)
  5. sync           (POST /api/projects/{uuid}/impressions/sync)
  6. upload via Yuki (POST /book-celebi-server/upload, grant relayed)
  7. report

The user bearer token only ever goes to celebi_server. Yuki receives only
the scoped upload grant from the sync response.
"""
import os
import re
import subprocess
import time

import requests

from ...utils import csys, metadata
from ...utils.message import Message

UUID32_RE = re.compile(r"^[0-9a-f]{32}$")
IMPRESS_POLL_INTERVAL = 2.0
IMPRESS_POLL_TIMEOUT = 30 * 60


def _project_hosts_path():
    project_path = csys.project_path()
    if not project_path:
        return ""
    return os.path.join(project_path, ".celebi", "hosts.json")


def _get_celebi_server_url(server_url=""):
    """Resolve booking server URL: --server > env > hosts.json."""
    if server_url:
        return server_url
    env_url = os.environ.get("CELEBI_SERVER_URL", "")
    if env_url:
        return env_url
    hosts_path = _project_hosts_path()
    if hosts_path and os.path.exists(hosts_path):
        return metadata.ConfigFile(hosts_path).read_variable(
            "celebi_server_url", "")
    return ""


def register_celebi_server(server_url=""):
    """Store the celebi_server URL in the project's hosts.json."""
    message = Message()
    server_url = (server_url or "").strip()
    if not server_url.startswith(("http://", "https://")):
        message.add(
            f"Invalid celebi_server URL '{server_url}' "
            "(want http://host:port).\n", "error")
        return message
    hosts_path = _project_hosts_path()
    if not hosts_path:
        message.add("Not inside a Celebi project.\n", "error")
        return message
    metadata.ConfigFile(hosts_path).write_variable(
        "celebi_server_url", server_url)
    message.add(f"Registered celebi_server: {server_url}\n", "success")
    return message


def _run_git(project_path, args):
    return subprocess.run(
        ["git", *args], cwd=project_path, capture_output=True, text=True)


def _git_guard(project_path, message):
    """Require clean tree + pushed upstream. Returns HEAD sha or ""."""
    proc = _run_git(project_path, ["rev-parse", "--is-inside-work-tree"])
    if proc.returncode != 0 or proc.stdout.strip() != "true":
        message.add("Not a git repository. Booking requires git.\n", "error")
        return ""
    proc = _run_git(project_path, ["status", "--porcelain"])
    if proc.stdout.strip():
        message.add(
            "Working tree is not clean. Commit or stash your changes "
            "before booking.\n", "error")
        return ""
    proc = _run_git(
        project_path, ["rev-parse", "--abbrev-ref", "--symbolic-full-name",
                       "@{u}"])
    if proc.returncode != 0:
        message.add(
            "No upstream branch configured. Booking pushes to the "
            "project's GitLab upstream, so set one up first.\n", "error")
        return ""
    upstream = proc.stdout.strip()
    proc = _run_git(
        project_path, ["rev-list", "--left-right", "--count",
                       f"HEAD...{upstream}"])
    ahead, _, behind = proc.stdout.partition("\t")
    ahead, behind = int(ahead), int(behind.strip() or 0)
    if ahead and behind:
        message.add(
            f"Branch has diverged from {upstream} (ahead {ahead}, "
            f"behind {behind}). Rebase or merge first.\n", "error")
        return ""
    if behind:
        message.add(
            f"Branch is behind {upstream} by {behind} commit(s). "
            "Pull first.\n", "error")
        return ""
    if ahead:
        proc = _run_git(project_path, ["push"])
        if proc.returncode != 0:
            message.add(f"git push failed: {proc.stderr}\n", "error")
            return ""
    proc = _run_git(project_path, ["rev-parse", "HEAD"])
    return proc.stdout.strip()


def _build_manifest(project_path, packed, git_commit):
    """One sync-manifest entry per packed impression."""
    manifest = []
    for entry in packed:
        imp_dir = os.path.join(
            project_path, ".celebi", "impressions", entry["uuid"])
        parents = []
        config_path = os.path.join(imp_dir, "config.json")
        if os.path.isfile(config_path):
            parents = metadata.ConfigFile(config_path).read_variable(
                "parents", []) or []
        manifest.append({
            "uuid": entry["uuid"],
            "sha256": entry["sha256"],
            "size": entry["size"],
            "git_commit": git_commit,
            "parents": parents,
        })
    return manifest


def _check_upload_subset(to_upload, packed_uuids, message):
    extras = [e["uuid"] for e in to_upload
              if e["uuid"] not in packed_uuids]
    if extras:
        message.add(
            "Server asked to upload impressions that were not packed: "
            + ", ".join(extras) + "\n", "error")
        return False
    return True
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_celebi_cli_booking.py -v`
Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add CelebiChrono/interface/shell_modules/server_booking.py tests/test_celebi_cli_booking.py
git commit -m "Add celebi_server booking helpers (URL resolve, git guard, manifest)"
```

---

### Task 2: `book()` orchestration

**Files:**
- Modify: `CelebiChrono/interface/shell_modules/server_booking.py`
- Test: `tests/test_celebi_cli_book.py` (new file; keeps Task 1 unit tests separate from the orchestration mocks)

**Interfaces:**
- Consumes: Task 1 helpers; `reana_booking._consume_ndjson_stream` and `reana_booking._get_yuki_server_url` (existing); `MANAGER` from `._manager` for local impress
- Produces:
  - `def book(server_url="", token="", allow_partial=False, verify_ssl=True) -> Message`
    - Steps (each failure adds an error message and returns early):
      1. Resolve server URL (error if unset, hint `celebi register-celebi-server --url URL`); token from arg or `$CELEBI_SERVER_TOKEN` (error if unset).
      2. `project_path = csys.project_path()` (error if not in project); `project_uuid` from `.celebi/config.json` `project_uuid` (error if empty).
      3. `_git_guard` → HEAD sha.
      4. Server impress: `POST {server}/api/projects/{uuid}/impress` bearer. Body of 202 = job record. If `status` in (pending, running): poll `GET .../impress/{job_id}` every 2s until terminal or 30 min timeout. failed → error with `error` + `log_tail`. `server_uuids = job["impressions"]`; validate each against `UUID32_RE`.
      5. Local impress: `from ._manager import MANAGER; MANAGER.current_object().impress()`; then verify every uuid in `server_uuids` has a local `.celebi/impressions/<uuid>` dir — mismatch → error ("server/client impress disagree — tree must be clean and pushed").
      6. Pack: `POST {yuki}/book-celebi-server/pack` JSON `{"project_uuid": uuid, "impressions": server_uuids}` with `stream=True`; `_consume_ndjson_stream` collects final data into `message.data`; read `packed`/`missing`. If `missing` and not `allow_partial` → error naming missing. If `allow_partial`, warning + continue with `packed` only.
      7. Manifest = `_build_manifest(project_path, packed, head_sha)`; sync: `POST {server}/api/projects/{uuid}/impressions/sync` bearer, JSON `{"manifest": manifest}` → `to_upload, to_download, grant`.
      8. `_check_upload_subset(to_upload, {p["uuid"] for p in packed}, message)`.
      9. If `to_upload` empty → report "already up to date" with counts; return.
      10. If no `grant` → error ("server did not issue an upload grant — a write role on the project is required").
      11. Upload: `POST {yuki}/book-celebi-server/upload` JSON `{"celebi_server_url": server, "project_uuid": uuid, "archives": [{uuid, sha256, size} for to_upload], "grant": grant}` stream → final data `uploaded`/`failed`. `failed` non-empty → error entries.
      12. Report: `message.data` gets `{"booked": len(uploaded), "missing": missing, "to_download": [u for u in to_download], "browse": f"{server}/projects/{uuid}"}`; success line "Booked N impression(s) to {server}".

- [ ] **Step 1: Write the failing test**

The test fakes `requests.request` at the `requests` module level (import `requests` in `server_booking` and monkeypatch `requests.request`), and stubs local impress + NDJSON consumption. `server_booking` must call `requests.request(method, url, ...)` — NOT `requests.post` — so one monkeypatch covers all verbs. (The Task 3 implementation uses `requests.request` accordingly.)

```python
# tests/test_celebi_cli_book.py
"""Orchestration tests for book(): call order, auth separation, invariants."""
import json
import os

import pytest

from CelebiChrono.interface.shell_modules import server_booking as sb
from CelebiChrono.utils.message import Message


UUID_A, UUID_B = "a" * 32, "b" * 32
SERVER = "http://server:3320"
YUKI = "http://yuki:3315"


class FakeResponse:
    def __init__(self, payload=None, lines=None):
        self.status_code = 200
        self._payload = payload or {}
        self._lines = lines or []

    def json(self):
        return self._payload

    def raise_for_status(self):
        pass

    def iter_lines(self):
        for line in self._lines:
            yield line if isinstance(line, bytes) else line.encode()


class Recorder:
    """Fake requests.request returning scripted responses by (method, url-suffix)."""

    def __init__(self, routes):
        self.routes = routes          # list of [(method, suffix), response]
        self.calls = []

    def __call__(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        for (m, suffix), resp in self.routes:
            if method == m and url.endswith(suffix):
                return resp
        raise AssertionError(f"no route for {method} {url}")


def _project(tmp_path, monkeypatch, uuids=(UUID_A,)):
    proj = tmp_path / "proj"
    (proj / ".celebi" / "impressions").mkdir(parents=True)
    with open(proj / ".celebi" / "config.json", "w") as f:
        json.dump({"project_uuid": "p" * 32}, f)
    for u in uuids:
        imp_dir = proj / ".celebi" / "impressions" / u
        imp_dir.mkdir()
        with open(imp_dir / "config.json", "w") as f:
            json.dump({"parents": []}, f)
    monkeypatch.chdir(proj)
    return proj


def _common_stubs(monkeypatch, proj, head="abc123"):
    monkeypatch.setattr(sb, "_git_guard", lambda p, m: head)
    fake_impress = lambda self: None
    monkeypatch.setattr(
        "CelebiChrono.interface.shell_modules._manager.MANAGER"
        ".current_object",
        lambda: type("O", (), {"impress": fake_impress})())
    monkeypatch.setattr(sb, "_get_yuki_server_url", lambda: YUKI)


def _impress_routes(status="succeeded"):
    return [
        (("POST", "/impress"),
         FakeResponse({"job_id": "j1", "status": status,
                       "impressions": [UUID_A, UUID_B], "error": None,
                       "log_tail": None})),
    ]


def _pack_lines(packed, missing=None):
    final = {"done": True, "success": True,
             "data": {"packed": packed, "missing": missing or []}}
    return [json.dumps(final).encode()]


def test_book_happy_path(tmp_path, monkeypatch):
    proj = _project(tmp_path, monkeypatch)
    _common_stubs(monkeypatch, proj)
    packed = [{"uuid": UUID_A, "path": "/yuki/staging/a.tar.gz",
               "sha256": "s" * 64, "size": 10, "file_count": 1}]
    rec = Recorder(_impress_routes() + [
        (("POST", "/book-celebi-server/pack"),
         FakeResponse(lines=_pack_lines(packed))),
        (("POST", "/impressions/sync"),
         FakeResponse({"to_upload": [{"uuid": UUID_A, "sha256": "s" * 64,
                                      "size": 10}],
                       "to_download": [], "grant": "grant-xyz"})),
        (("POST", "/book-celebi-server/upload"),
         FakeResponse(lines=[json.dumps({"done": True, "success": True,
                                         "data": {"uploaded": [UUID_A],
                                                  "failed": []}}).encode()])),
    ])
    monkeypatch.setattr("requests.request", rec)

    msg = sb.book(server_url=SERVER, token="user-token")
    assert msg.success, msg.messages
    urls = [c[1] for c in rec.calls]
    assert urls[0] == f"{SERVER}/api/projects/{'p'*32}/impress"
    assert f"{YUKI}/book-celebi-server/pack" in urls
    assert f"{SERVER}/api/projects/{'p'*32}/impressions/sync" in urls
    assert f"{YUKI}/book-celebi-server/upload" in urls
    # order: pack BEFORE sync BEFORE upload
    assert urls.index(f"{YUKI}/book-celebi-server/pack") < \
        urls.index(f"{SERVER}/api/projects/{'p'*32}/impressions/sync") < \
        urls.index(f"{YUKI}/book-celebi-server/upload")
    # auth separation: server calls carry user bearer; Yuki never sees it
    for method, url, kwargs in rec.calls:
        auth = kwargs.get("headers", {}).get("Authorization", "")
        if "/api/projects/" in url:
            assert auth == "Bearer user-token"
        else:
            assert "user-token" not in json.dumps(kwargs.get("json", {}))
            assert auth == ""
    # grant relayed to Yuki, never to the sync endpoint body
    upload_call = [c for c in rec.calls
                   if c[1].endswith("/book-celebi-server/upload")][0]
    assert upload_call[2]["json"]["grant"] == "grant-xyz"
    sync_call = [c for c in rec.calls if c[1].endswith("/impressions/sync")][0]
    assert "grant" not in sync_call[2]["json"]
    assert msg.data["booked"] == 1
    assert msg.data["missing"] == []
    assert msg.data["browse"] == f"{SERVER}/projects/{'p'*32}"


def test_book_manifest_declares_pack_sha(tmp_path, monkeypatch):
    proj = _project(tmp_path, monkeypatch)
    _common_stubs(monkeypatch, proj)
    packed = [{"uuid": UUID_A, "path": "/yuki/staging/a.tar.gz",
               "sha256": "s" * 64, "size": 10, "file_count": 1}]
    rec = Recorder(_impress_routes() + [
        (("POST", "/book-celebi-server/pack"),
         FakeResponse(lines=_pack_lines(packed))),
        (("POST", "/impressions/sync"),
         FakeResponse({"to_upload": [], "to_download": [], "grant": None})),
    ])
    monkeypatch.setattr("requests.request", rec)
    msg = sb.book(server_url=SERVER, token="t")
    assert msg.success
    sync = [c for c in rec.calls if c[1].endswith("/impressions/sync")][0]
    (entry,) = sync[2]["json"]["manifest"]
    assert entry["uuid"] == UUID_A
    assert entry["sha256"] == "s" * 64
    assert entry["git_commit"] == "abc123"
    # empty delta: no upload call, "up to date" reported
    assert not any("book-celebi-server/upload" in c[1] for c in rec.calls)
    assert any("up to date" in t for t, _ in msg.messages)


def test_book_missing_hard_error_unless_allow_partial(tmp_path, monkeypatch):
    proj = _project(tmp_path, monkeypatch)
    _common_stubs(monkeypatch, proj)
    rec = Recorder(_impress_routes() + [
        (("POST", "/book-celebi-server/pack"),
         FakeResponse(lines=_pack_lines([], missing=[UUID_B]))),
    ])
    monkeypatch.setattr("requests.request", rec)
    msg = sb.book(server_url=SERVER, token="t")
    assert not msg.success
    assert UUID_B in msg.messages[0][0]
    # never reached sync
    assert not any("impressions/sync" in c[1] for c in rec.calls)

    msg = sb.book(server_url=SERVER, token="t", allow_partial=True)
    assert msg.success
    assert msg.data["missing"] == [UUID_B]


def test_book_failed_impress_reports_log_tail(tmp_path, monkeypatch):
    proj = _project(tmp_path, monkeypatch)
    _common_stubs(monkeypatch, proj)
    rec = Recorder([
        (("POST", "/impress"),
         FakeResponse({"job_id": "j1", "status": "failed",
                       "impressions": None, "error": "exit 2",
                       "log_tail": "boom"})),
    ])
    monkeypatch.setattr("requests.request", rec)
    msg = sb.book(server_url=SERVER, token="t")
    assert not msg.success
    assert "boom" in msg.messages[0][0]


def test_book_no_grant_is_error(tmp_path, monkeypatch):
    proj = _project(tmp_path, monkeypatch)
    _common_stubs(monkeypatch, proj)
    packed = [{"uuid": UUID_A, "path": "/yuki/staging/a.tar.gz",
               "sha256": "s" * 64, "size": 10, "file_count": 1}]
    rec = Recorder(_impress_routes() + [
        (("POST", "/book-celebi-server/pack"),
         FakeResponse(lines=_pack_lines(packed))),
        (("POST", "/impressions/sync"),
         FakeResponse({"to_upload": [{"uuid": UUID_A, "sha256": "s" * 64,
                                      "size": 10}],
                       "to_download": [], "grant": None})),
    ])
    monkeypatch.setattr("requests.request", rec)
    msg = sb.book(server_url=SERVER, token="t")
    assert not msg.success
    assert not any("book-celebi-server/upload" in c[1] for c in rec.calls)


def test_book_impress_mismatch_local_missing(tmp_path, monkeypatch):
    # server says UUID_A+UUID_B but local impress only produced UUID_A
    proj = _project(tmp_path, monkeypatch, uuids=(UUID_A,))
    _common_stubs(monkeypatch, proj)
    rec = Recorder(_impress_routes())
    monkeypatch.setattr("requests.request", rec)
    msg = sb.book(server_url=SERVER, token="t")
    assert not msg.success
    assert UUID_B in msg.messages[0][0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_celebi_cli_book.py -x`
Expected: FAIL (`AttributeError: module ... has no attribute 'book'`)

- [ ] **Step 3: Implement**

Append to `CelebiChrono/interface/shell_modules/server_booking.py`:

```python
def _consume_json_stream(response, message):
    """Reuse Yuki NDJSON consumption; final data lands in message.data."""
    from .reana_booking import _consume_ndjson_stream
    _consume_ndjson_stream(response, message)


def _get_yuki_server_url():
    from .reana_booking import _get_yuki_server_url as _yuki
    return _yuki()


def _server_request(method, url, token, message, **kwargs):
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.request(
            method, url, headers=headers, timeout=300, **kwargs)
        response.raise_for_status()
        return response
    except requests.exceptions.ConnectionError:
        message.add(f"Cannot reach celebi_server at {url}.\n", "error")
    except requests.exceptions.Timeout:
        message.add(f"Request to {url} timed out.\n", "error")
    except requests.exceptions.HTTPError:
        detail = ""
        try:
            detail = response.text[:400]
        except Exception:  # noqa: BLE001
            pass
        message.add(f"{method} {url} failed: {detail}\n", "error")
    return None


def _yuki_request(url, payload, message):
    try:
        response = requests.request(
            "POST", url, json=payload, stream=True, timeout=300)
        if response.status_code != 200:
            message.add(f"Yuki rejected the request (HTTP "
                        f"{response.status_code}): {response.text[:400]}\n",
                        "error")
            return None
        _consume_json_stream(response, message)
        return message.data
    except requests.exceptions.ConnectionError:
        message.add(f"Cannot reach Yuki server at {url}.\n", "error")
    except requests.exceptions.Timeout:
        message.add(f"Request to {url} timed out.\n", "error")
    return None


def _server_impress(server, project_uuid, token, message):
    """Trigger and poll the server-side impress job. Returns uuid list."""
    url = f"{server}/api/projects/{project_uuid}/impress"
    response = _server_request("POST", url, token, message)
    if response is None:
        return None
    job = response.json()
    deadline = time.time() + IMPRESS_POLL_TIMEOUT
    while job.get("status") in ("pending", "running"):
        if time.time() > deadline:
            message.add("Server-side impress timed out.\n", "error")
            return None
        time.sleep(IMPRESS_POLL_INTERVAL)
        response = _server_request(
            "GET", f"{url}/{job['job_id']}", token, message)
        if response is None:
            return None
        job = response.json()
    if job.get("status") != "succeeded":
        message.add(
            f"Server-side impress failed: {job.get('error')}\n"
            f"--- log tail ---\n{job.get('log_tail') or ''}\n", "error")
        return None
    uuids = job.get("impressions") or []
    bad = [u for u in uuids if not UUID32_RE.match(u)]
    if bad:
        message.add(f"Server returned invalid impression uuids: {bad}\n",
                    "error")
        return None
    return sorted(uuids)


def _local_impress(project_path, server_uuids, message):
    """Run the local impress and verify uuid agreement with the server."""
    from ._manager import MANAGER
    MANAGER.current_object().impress()
    missing = [u for u in server_uuids if not os.path.isdir(
        os.path.join(project_path, ".celebi", "impressions", u))]
    if missing:
        message.add(
            "Server and local impress disagree (missing locally: "
            + ", ".join(missing)
            + "). The working tree must be clean and pushed before "
            "booking.\n", "error")
        return False
    return True


def book(server_url="", token="", allow_partial=False, verify_ssl=True):
    """Book the current project to a celebi_server (see module docstring)."""
    message = Message()
    server = _get_celebi_server_url(server_url).rstrip("/")
    if not server:
        message.add(
            "celebi_server URL not set. Use --server, set "
            "CELEBI_SERVER_URL, or run 'celebi register-celebi-server "
            "--url URL'.\n", "error")
        return message
    token = token or os.environ.get("CELEBI_SERVER_TOKEN", "")
    if not token:
        message.add(
            "celebi_server token not set. Use --token or set "
            "CELEBI_SERVER_TOKEN.\n", "error")
        return message

    project_path = csys.project_path()
    if not project_path:
        message.add("Not inside a Celebi project.\n", "error")
        return message
    project_uuid = metadata.ConfigFile(
        os.path.join(project_path, ".celebi", "config.json")
    ).read_variable("project_uuid", "")
    if not project_uuid:
        message.add("Project has no uuid (.celebi/config.json).\n", "error")
        return message

    # 1. git
    head_sha = _git_guard(project_path, message)
    if not head_sha:
        return message

    # 2. server-side impress
    server_uuids = _server_impress(server, project_uuid, token, message)
    if server_uuids is None:
        return message

    # 3. local impress (idempotent; content-derived uuids must agree)
    if not _local_impress(project_path, server_uuids, message):
        return message

    # 4. pack via Yuki
    yuki_url = "http://" + _get_yuki_server_url() \
        if not _get_yuki_server_url().startswith("http") \
        else _get_yuki_server_url()
    pack_data = _yuki_request(
        f"{yuki_url}/book-celebi-server/pack",
        {"project_uuid": project_uuid, "impressions": server_uuids},
        message)
    if pack_data is None:
        return message
    packed = pack_data.get("packed") or []
    missing = pack_data.get("missing") or []
    if missing and not allow_partial:
        message.add(
            "Yuki has no bookable contents for: " + ", ".join(missing)
            + ".\nCollect the results first, or re-run with "
            "--allow-partial.\n", "error")
        return message
    if missing:
        message.add("Skipping missing impressions: "
                    + ", ".join(missing) + "\n", "warning")

    # 5. sync
    manifest = _build_manifest(project_path, packed, head_sha)
    response = _server_request(
        "POST", f"{server}/api/projects/{project_uuid}/impressions/sync",
        token, message, json={"manifest": manifest})
    if response is None:
        return message
    sync = response.json()
    to_upload = sync.get("to_upload") or []
    to_download = sync.get("to_download") or []
    grant = sync.get("grant")
    if not _check_upload_subset(
            to_upload, {p["uuid"] for p in packed}, message):
        return message

    # 6. upload via Yuki under the grant
    uploaded, failed_uploads = [], []
    if to_upload:
        if not grant:
            message.add(
                "The server did not issue an upload grant. Booking "
                "requires a write role on this project.\n", "error")
            return message
        by_uuid = {p["uuid"]: p for p in packed}
        archives = [
            {"uuid": e["uuid"],
             "sha256": by_uuid[e["uuid"]]["sha256"],
             "size": by_uuid[e["uuid"]]["size"]}
            for e in to_upload
        ]
        upload_data = _yuki_request(
            f"{yuki_url}/book-celebi-server/upload",
            {"celebi_server_url": server, "project_uuid": project_uuid,
             "archives": archives, "grant": grant},
            message)
        if upload_data is None:
            return message
        uploaded = upload_data.get("uploaded") or []
        failed_uploads = upload_data.get("failed") or []
        if failed_uploads:
            message.add(
                "Upload failures: "
                + "; ".join(f"{f['uuid']}: {f['error']}"
                            for f in failed_uploads)
                + "\n", "error")
            return message

    # 7. report
    message.data.update({
        "booked": len(uploaded),
        "missing": missing,
        "to_download": [e["uuid"] for e in to_download],
        "browse": f"{server}/projects/{project_uuid}",
    })
    if to_upload:
        message.add(f"Booked {len(uploaded)} impression(s) to {server}.\n",
                    "success")
    else:
        message.add("celebi_server is already up to date.\n", "success")
    return message
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_celebi_cli_book.py tests/test_celebi_cli_booking.py -v`
Expected: all passed (19 tests). If `test_book_missing_hard_error_unless_allow_partial` fails on the second `book()` call because `_staging` state or stream consumption differs, check `_consume_ndjson_stream` clears `message.data` between calls — it updates in place, and each `book()` builds a fresh `Message`, so this is fine.

- [ ] **Step 5: Commit**

```bash
git add CelebiChrono/interface/shell_modules/server_booking.py tests/test_celebi_cli_book.py
git commit -m "Add book() orchestration: git guard, server impress, Yuki pack/sync/upload"
```

---

### Task 3: CLI commands + wiring

**Files:**
- Modify: `CelebiChrono/celebi_cli/commands/booking.py`
- Modify: `CelebiChrono/celebi_cli/cli.py`
- Test: `tests/test_celebi_cli_booking_commands.py`

**Interfaces:**
- Produces:
  - `celebi book` — options: `--server`, `--token`, `--allow-partial` (flag), `--no-stream` accepted for symmetry but ignored (booking is always streamed when the server supports it; the client consumes NDJSON either way — keep the flag as a no-op for CLI stability, documented in help).
  - `celebi register-celebi-server --url URL`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_celebi_cli_booking_commands.py
"""Registration tests for book / register-celebi-server commands."""
from CelebiChrono.celebi_cli.cli import cli


def test_book_command_registered():
    assert "book" in cli.commands


def test_register_celebi_server_command_registered():
    assert "register-celebi-server" in cli.commands
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_celebi_cli_booking_commands.py -x`
Expected: FAIL (assertion — commands not registered)

- [ ] **Step 3: Implement**

In `celebi_cli/commands/booking.py`, extend the import block at the top:

```python
from CelebiChrono.interface.shell_modules.server_booking import (
    register_celebi_server,
    book,
)
```

Append the two commands:

```python
@click.command(name="book")
@click.option("--server", "server_url", default="",
              help="celebi_server URL (or CELEBI_SERVER_URL env / "
                   "register-celebi-server)")
@click.option("--token", default="",
              help="celebi_server bearer token (or CELEBI_SERVER_TOKEN env)")
@click.option("--allow-partial", is_flag=True, default=False,
              help="Book the impressions Yuki holds; skip missing ones")
@click.option("--insecure", is_flag=True, default=False,
              help="Disable SSL certificate verification")
@click.option("--no-stream", is_flag=True, default=False,
              help="Accepted for symmetry; booking progress is consumed "
                   "as it arrives either way")
def book_command(server_url, token, allow_partial, insecure, no_stream):
    """Book this project to a celebi_server (file lists + plots).

    Requires a clean git tree synced with the upstream, a registered
    project on the server (ask the server admin), and a write role.
    """
    try:
        result = book(
            server_url=server_url,
            token=token,
            allow_partial=allow_partial,
            verify_ssl=not insecure,
        )
        if result.messages:
            print(result.colored())
        if not result.success:
            raise SystemExit(1)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001 - CLI boundary
        print(f"Error: {e}")


@click.command(name="register-celebi-server")
@click.option("--url", "server_url", default="",
              help="celebi_server URL, e.g. http://162.105.151.45:3320")
def register_celebi_server_command(server_url):
    """Store the celebi_server URL in the project's hosts.json."""
    try:
        result = register_celebi_server(server_url=server_url)
        if result.messages:
            print(result.colored())
    except Exception as e:  # noqa: BLE001 - CLI boundary
        print(f"Error: {e}")
```

In `cli.py`, after the existing booking command registrations (the block that adds `booking.booking_server_command` etc. — match the local style):

```python
cli.add_command(booking.book_command)
cli.add_command(booking.register_celebi_server_command)
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_celebi_cli_booking_commands.py -v`
Expected: 2 passed

- [ ] **Step 5: Full suite**

Run: `pytest tests UnitTest -q`
Expected: all green (new imports must not break existing CLI wiring tests)

- [ ] **Step 6: Commit**

```bash
git add CelebiChrono/celebi_cli/commands/booking.py CelebiChrono/celebi_cli/cli.py tests/test_celebi_cli_booking_commands.py
git commit -m "Wire 'book' and 'register-celebi-server' into celebi-cli"
```

---

## Self-review notes

- **Spec coverage:** §celebi 1 (server_booking.py URL resolution + book orchestration) → Tasks 1–2; §celebi 2 (CLI commands + wiring) → Task 3. ✔
- **Placeholder scan:** all steps contain exact code/commands. ✔
- **Type consistency:** `_git_guard(project_path, message) -> str`, `_build_manifest(project_path, packed, git_commit) -> list`, `_check_upload_subset(to_upload, packed_uuids, message) -> bool`, `book(server_url="", token="", allow_partial=False, verify_ssl=True) -> Message`, `register_celebi_server(server_url="") -> Message` — used identically across tasks and in tests. ✔
- **Ruling (recorded):** the spec's step-5 sketch said "manifest = all local impressions … plus {sha256, size} for the packed ones"; celebi_server's `_check_manifest` requires a string sha256 on EVERY entry, so the manifest is packed-only. Spec file corrected in place ( celebi_server spec §booking flow step 5). Local-only impressions surface through the `missing` report instead.
- **Known friction point:** `requests.request` (not `requests.post`) is the single HTTP seam so tests monkeypatch one symbol; the Task 2 implementation and tests agree on this.
