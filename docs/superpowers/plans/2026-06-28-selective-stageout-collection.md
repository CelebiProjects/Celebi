# Selective, type-aware stageout collection & booking — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `collect`/`book-reana` operate on individual stageout files by name and type (default: plots + logs only) instead of all-or-nothing, and let `status` show which output files exist in the runner vs already downloaded to Yuki.

**Architecture:** A new shared classifier in Yuki labels files `plot`/`data`; the runner workflow classes gain "list remote files" and "download a filtered subset" methods; new/repurposed HTTP endpoints expose light-default and selective collection plus a file-status view; the Celebi client parses a `collect` selector and renders a status table, and threads an `--upload` mode into booking.

**Tech Stack:** Python 3.9–3.13, Flask (Yuki HTTP server), `reana_client` (mocked in tests), `requests` (Celebi→Yuki), `unittest`/`unittest.mock` + `pytest`, Click (CLI).

## Global Constraints

- Two sibling repos: `Celebi` (`/Users/wave/workdir/Celebi/Celebi`, package `CelebiChrono`) and `Yuki` (`/Users/wave/workdir/Celebi/Yuki`, package `Yuki`). Yuki imports `CelebiChrono.*`, so both are importable in Yuki's test env.
- No new output directory — only `stageout/` and `logs/` exist. The earlier `deliverable/` idea is dropped.
- File-type classification lives in **one** place: `Yuki/kernel/file_types.py`. The Celebi client never classifies; it passes a selection spec and renders server-provided `type`.
- `PLOT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".svg", ".webp", ".eps"}` (verbatim).
- Use only the standard library for matching (`fnmatch`, `os`); no new runtime dependencies.
- Downloads are **idempotent per file**: skip a file already present in Storage. The whole-dir marker (`stageout.downloaded`) means "the complete set is present" and is written **only** by a full collect, never by a selective/partial one.
- Forward-only: no migration of existing impressions.
- Run tests from each repo's `UnitTest/` dir (`cd UnitTest && python -m pytest -v`). Keep pylint clean (`.pylintrc` in each repo).
- One task = one commit. Commit messages: `feat:`/`test:`/`refactor:` prefix; scope the body to the task.

## Selector vocabulary (used across client & server)

A **selection spec** is one of: the keyword `plots`, `data`, or `all`; a glob pattern (contains `*`, `?`, or `[`); or a literal filename. `collect`/`collect logs` map to dedicated endpoints; everything else flows through `/collect-files` with a `type=`, `pattern=`, or `names=` query.

| Client `collect` arg | Server call | Effect |
|---|---|---|
| *(none)* | `GET /collect` | plots + logs (light default) |
| `all` | `GET /collect-outputs` then `GET /collect-logs` | every stageout file + logs |
| `plots` | `GET /collect-files?kind=stageout&type=plots` | plot files only |
| `data` | `GET /collect-files?kind=stageout&type=data` | non-plot files only |
| `logs` | `GET /collect-logs` | logs only |
| `*.root` / `mass.png` | `GET /collect-files?kind=stageout&pattern=*.root` (or `names=`) | matching files |

---

# Phase A — Yuki (server)

### Task A1: Shared file-type classifier

**Files:**
- Create: `Yuki/kernel/file_types.py`
- Test: `Yuki/UnitTest/test_file_types.py`

**Interfaces:**
- Produces:
  - `PLOT_EXTENSIONS: set[str]`
  - `is_plot(filename: str) -> bool`
  - `classify(filename: str) -> str` — returns `"plot"` or `"data"`
  - `make_predicate(spec: str) -> Callable[[str], bool]` — `spec` is `"plots"`, `"data"`, `"all"`, a glob, or a literal filename; the returned predicate takes a **basename** and returns whether it matches.

- [ ] **Step 1: Write the failing test**

Create `Yuki/UnitTest/test_file_types.py`:
```python
from Yuki.kernel import file_types


def test_is_plot_by_extension():
    assert file_types.is_plot("mass.png") is True
    assert file_types.is_plot("fit.PDF") is True          # case-insensitive
    assert file_types.is_plot("ntuple.root") is False


def test_classify():
    assert file_types.classify("mass.png") == "plot"
    assert file_types.classify("ntuple.root") == "data"


def test_make_predicate_type_keywords():
    plots = file_types.make_predicate("plots")
    data = file_types.make_predicate("data")
    every = file_types.make_predicate("all")
    assert plots("mass.png") and not plots("ntuple.root")
    assert data("ntuple.root") and not data("mass.png")
    assert every("anything.xyz") is True


def test_make_predicate_glob_and_name():
    glob = file_types.make_predicate("*.root")
    name = file_types.make_predicate("mass.png")
    assert glob("ntuple.root") and not glob("mass.png")
    assert name("mass.png") and not name("other.png")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wave/workdir/Celebi/Yuki/UnitTest && python -m pytest test_file_types.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'Yuki.kernel.file_types'`

- [ ] **Step 3: Write minimal implementation**

Create `Yuki/kernel/file_types.py`:
```python
"""Classification of job output files into 'plot' vs 'data', plus a
selection-spec predicate builder. Single source of truth for what counts
as a plot, shared by collect filtering, booking filtering, and status views.
"""
import fnmatch
import os

PLOT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".svg", ".webp", ".eps"}


def is_plot(filename):
    """True when the file's extension marks it as a plot/image."""
    return os.path.splitext(filename)[1].lower() in PLOT_EXTENSIONS


def classify(filename):
    """Return 'plot' or 'data' for a stageout filename."""
    return "plot" if is_plot(filename) else "data"


def make_predicate(spec):
    """Build a basename predicate from a selection spec.

    spec is one of: 'plots', 'data', 'all', a glob pattern, or a literal
    filename. Returns a function (basename) -> bool.
    """
    if spec in ("all", "", None):
        return lambda name: True
    if spec == "plots":
        return is_plot
    if spec == "data":
        return lambda name: not is_plot(name)
    if any(ch in spec for ch in "*?["):
        return lambda name: fnmatch.fnmatch(name, spec)
    return lambda name: name == spec
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wave/workdir/Celebi/Yuki/UnitTest && python -m pytest test_file_types.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
cd /Users/wave/workdir/Celebi/Yuki
git add Yuki/kernel/file_types.py UnitTest/test_file_types.py
git commit -m "feat: add file_types classifier for plot/data and selection specs"
```

---

### Task A2: REANA — list remote files & download a filtered subset

**Files:**
- Modify: `Yuki/kernel/reana_workflow.py` (add two methods after `download_logs`, ~line 449)
- Test: `Yuki/UnitTest/test_reana_workflow_select.py`

**Interfaces:**
- Consumes: `file_types.is_plot` (A1); existing `self.get_name()`, `self.get_access_token(self.machine_id)`, `self.machine_id`, `self.project_uuid`, `self.logger`, module globals `client`, `REANA_AVAILABLE`, `self.set_environment`.
- Produces:
  - `list_runner_files(self, impression, kind="stageout") -> list[dict]` — each `{"name": <basename-relative-to-kind>, "size": int}`.
  - `download_selected(self, impression, predicate, kind="stageout") -> None` — downloads only remote files whose basename satisfies `predicate` and that are not already in Storage; never writes the dir marker.

- [ ] **Step 1: Write the failing test**

Create `Yuki/UnitTest/test_reana_workflow_select.py`:
```python
import os
import tempfile
from unittest import mock

from Yuki.kernel import reana_workflow


def _make_wf():
    wf = reana_workflow.ReanaWorkflow.__new__(reana_workflow.ReanaWorkflow)
    wf.machine_id = "runner-1"
    wf.project_uuid = "proj-1"
    wf.logger = lambda *a, **k: None
    wf.get_name = lambda: "wfname"
    wf.get_access_token = lambda mid: "tok"
    wf.set_environment = lambda mid: None
    return wf


def test_list_runner_files_strips_prefix_and_keeps_size():
    wf = _make_wf()
    fake = [
        {"name": "imp1234567/stageout/mass.png", "size": 10},
        {"name": "imp1234567/stageout/ntuple.root", "size": 999},
    ]
    with mock.patch.object(reana_workflow, "REANA_AVAILABLE", True), \
         mock.patch.object(reana_workflow, "client") as cli:
        cli.list_files.return_value = fake
        out = wf.list_runner_files("1234567abc", "stageout")
    assert {"name": "mass.png", "size": 10} in out
    assert {"name": "ntuple.root", "size": 999} in out


def test_download_selected_only_matching_and_skips_existing(tmp_path):
    wf = _make_wf()
    home = tmp_path
    storage = home / ".Yuki" / "Storage" / "proj-1" / "imp7" / "runner-1" / "stageout"
    storage.mkdir(parents=True)
    (storage / "already.png").write_bytes(b"old")     # pre-existing -> skip
    fake = [
        {"name": "impimp7000/stageout/already.png", "size": 3},
        {"name": "impimp7000/stageout/new.png", "size": 4},
        {"name": "impimp7000/stageout/ntuple.root", "size": 5},
    ]
    with mock.patch.dict(os.environ, {"HOME": str(home)}), \
         mock.patch.object(reana_workflow, "REANA_AVAILABLE", True), \
         mock.patch.object(reana_workflow, "client") as cli:
        cli.list_files.return_value = fake
        cli.download_file.return_value = (b"data",)
        wf.download_selected("imp7", reana_workflow.file_types.is_plot, "stageout")
        downloaded = {c.args[1] for c in cli.download_file.call_args_list}
    assert "impimp7000/stageout/new.png" in downloaded      # matched plot, missing
    assert "impimp7000/stageout/already.png" not in downloaded   # skipped (exists)
    assert "impimp7000/stageout/ntuple.root" not in downloaded   # not a plot
    assert not (storage / "stageout.downloaded").exists()        # no marker on partial
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wave/workdir/Celebi/Yuki/UnitTest && python -m pytest test_reana_workflow_select.py -v`
Expected: FAIL — `AttributeError: ... has no attribute 'list_runner_files'` (and `reana_workflow.file_types` missing).

- [ ] **Step 3: Write minimal implementation**

In `Yuki/kernel/reana_workflow.py`, add the import near the top (with the other `from .` imports):
```python
from . import file_types
```
Then insert these two methods after `download_logs` (after line 449, before `ping`):
```python
    def list_runner_files(self, impression, kind="stageout"):
        """List files in the runner workspace under imp<short>/<kind> without
        downloading. Returns [{"name": <relative-to-kind>, "size": int}]."""
        if not REANA_AVAILABLE:
            raise ImportError("reana_client is not available")
        self.set_environment(self.machine_id)
        prefix = "imp" + impression[0:7] + "/" + kind + "/"
        try:
            files = client.list_files(
                self.get_name(),
                self.get_access_token(self.machine_id),
                "imp" + impression[0:7] + "/" + kind,
            )
        except Exception as e:
            self.logger(f"Failed to list runner files: {e}")
            return []
        result = []
        for f in files:
            name = f["name"]
            rel = name[len(prefix):] if name.startswith(prefix) else os.path.basename(name)
            if rel:
                result.append({"name": rel, "size": f.get("size", 0)})
        return result

    def download_selected(self, impression, predicate, kind="stageout"):
        """Download only remote files whose basename satisfies predicate and
        that are not already in Storage. Does not write the dir marker."""
        if not REANA_AVAILABLE:
            raise ImportError("reana_client is not available")
        self.set_environment(self.machine_id)
        path = os.path.join(os.environ["HOME"], ".Yuki", "Storage",
                            self.project_uuid, impression, self.machine_id)
        prefix = "imp" + impression[0:7] + "/" + kind + "/"
        try:
            files = client.list_files(
                self.get_name(),
                self.get_access_token(self.machine_id),
                "imp" + impression[0:7] + "/" + kind,
            )
        except Exception as e:
            self.logger(f"Failed to list runner files: {e}")
            return
        os.makedirs(os.path.join(path, kind), exist_ok=True)
        for f in files:
            name = f["name"]
            rel = name[len(prefix):] if name.startswith(prefix) else os.path.basename(name)
            if not rel or not predicate(os.path.basename(rel)):
                continue
            dest = os.path.join(path, kind, rel)
            if os.path.exists(dest):
                continue
            try:
                output = client.download_file(
                    self.get_name(), name, self.get_access_token(self.machine_id))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as fh:
                    fh.write(output[0])
                self.logger(f"Downloaded selected {kind}: {rel}")
            except Exception as e:
                self.logger(f"Failed to download {rel}: {e}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wave/workdir/Celebi/Yuki/UnitTest && python -m pytest test_reana_workflow_select.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
cd /Users/wave/workdir/Celebi/Yuki
git add Yuki/kernel/reana_workflow.py UnitTest/test_reana_workflow_select.py
git commit -m "feat: REANA list_runner_files and download_selected (filtered, idempotent)"
```

---

### Task A3: Native — list local files & download a filtered subset (idempotent)

**Files:**
- Modify: `Yuki/kernel/native_workflow.py` (`_collect_artifacts` ~line 388; add two methods after `download_logs` ~line 451)
- Test: `Yuki/UnitTest/test_native_workflow_select.py`

**Interfaces:**
- Consumes: existing `self.local_exec_path`, `self.project_uuid`, `self.machine_id`, `self.logger`.
- Produces:
  - `list_runner_files(self, impression, kind="stageout") -> list[dict]`
  - `download_selected(self, impression, predicate, kind="stageout") -> None`
- Also: `_collect_artifacts` becomes idempotent (skips files already in Storage).

- [ ] **Step 1: Write the failing test**

Create `Yuki/UnitTest/test_native_workflow_select.py`:
```python
import os
from unittest import mock

from Yuki.kernel import native_workflow


def _make_wf(tmp_path):
    wf = native_workflow.NativeWorkflow.__new__(native_workflow.NativeWorkflow)
    wf.local_exec_path = str(tmp_path / "exec")
    wf.project_uuid = "proj-1"
    wf.machine_id = "runner-1"
    wf.logger = lambda *a, **k: None
    src = tmp_path / "exec" / "imp7654321" / "stageout"
    src.mkdir(parents=True)
    (src / "mass.png").write_bytes(b"img")
    (src / "ntuple.root").write_bytes(b"data")
    return wf


def test_list_runner_files_native(tmp_path):
    wf = _make_wf(tmp_path)
    out = {f["name"]: f["size"] for f in wf.list_runner_files("7654321xyz", "stageout")}
    assert out["mass.png"] == 3
    assert "ntuple.root" in out


def test_download_selected_native_only_plots(tmp_path):
    wf = _make_wf(tmp_path)
    with mock.patch.dict(os.environ, {"HOME": str(tmp_path / "home")}):
        wf.download_selected("7654321xyz", native_workflow.file_types.is_plot, "stageout")
        dst = (tmp_path / "home" / ".Yuki" / "Storage" / "proj-1"
               / "7654321xyz" / "runner-1" / "stageout")
        assert (dst / "mass.png").exists()
        assert not (dst / "ntuple.root").exists()
        assert not (dst.parent / "stageout.downloaded").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wave/workdir/Celebi/Yuki/UnitTest && python -m pytest test_native_workflow_select.py -v`
Expected: FAIL — `AttributeError: ... 'list_runner_files'`.

- [ ] **Step 3: Write minimal implementation**

In `Yuki/kernel/native_workflow.py`, add near the top imports:
```python
from . import file_types
```
Make `_collect_artifacts` idempotent — change its copy loop (currently lines 415-419) to skip existing files:
```python
        for i, filename in enumerate(filelist):
            src_file = os.path.join(src_path, filename)
            dst_file = os.path.join(dst_path, filename)
            if os.path.exists(dst_file):
                continue
            shutil.copy2(src_file, dst_file)
            self.logger(f"[LOCAL] [{i+1}/{total_files}] Collected {label}: {filename}")
```
Add two methods after `download_logs` (after line 451):
```python
    def list_runner_files(self, impression, kind="stageout"):
        """List files in the local execution dir under imp<short>/<kind>."""
        src_path = os.path.join(
            self.local_exec_path, f"imp{impression[0:7]}", kind)
        if not os.path.isdir(src_path):
            return []
        result = []
        for filename in os.listdir(src_path):
            full = os.path.join(src_path, filename)
            size = os.path.getsize(full) if os.path.isfile(full) else 0
            result.append({"name": filename, "size": size})
        return result

    def download_selected(self, impression, predicate, kind="stageout"):
        """Copy only matching, not-yet-present files into Storage. No marker."""
        src_path = os.path.join(
            self.local_exec_path, f"imp{impression[0:7]}", kind)
        if not os.path.isdir(src_path):
            self.logger(f"[LOCAL] No {kind} found at: {src_path}")
            return
        dst_path = os.path.join(
            os.environ["HOME"], ".Yuki", "Storage",
            self.project_uuid, impression, self.machine_id, kind)
        os.makedirs(dst_path, exist_ok=True)
        for filename in os.listdir(src_path):
            if not predicate(filename):
                continue
            dst_file = os.path.join(dst_path, filename)
            if os.path.exists(dst_file):
                continue
            shutil.copy2(os.path.join(src_path, filename), dst_file)
            self.logger(f"[LOCAL] Collected selected {kind}: {filename}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wave/workdir/Celebi/Yuki/UnitTest && python -m pytest test_native_workflow_select.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
cd /Users/wave/workdir/Celebi/Yuki
git add Yuki/kernel/native_workflow.py UnitTest/test_native_workflow_select.py
git commit -m "feat: native list_runner_files/download_selected; idempotent _collect_artifacts"
```

---

### Task A4: ImpressionStorage — light `collect`, `collect_files`, `file_status`

**Files:**
- Modify: `Yuki/kernel/impression_storage.py`
- Test: `Yuki/UnitTest/test_impression_storage_select.py`

**Interfaces:**
- Consumes: `file_types.is_plot`, `file_types.make_predicate`, `file_types.classify` (A1); workflow `download_selected`/`download_logs`/`list_runner_files` (A2/A3); existing `_get_runner_contexts`, `self.impression`, `self.job_path`, `self.runners_id`.
- Produces:
  - `collect(self)` — **repurposed**: on `CODA` download plots + logs; on `FAILED`/`DISSONANCE` download logs.
  - `collect_files(self, kind, spec)` — download stageout subset matching `spec`.
  - `file_status(self, kind="stageout") -> list[dict]` — merged runner+Storage listing.

- [ ] **Step 1: Write the failing test**

Create `Yuki/UnitTest/test_impression_storage_select.py`:
```python
import os
from unittest import mock

from Yuki.kernel import impression_storage as ims
from Yuki.kernel.status_constants import CODA


def _storage(tmp_path):
    s = ims.ImpressionStorage.__new__(ims.ImpressionStorage)
    s.project_uuid = "proj-1"
    s.impression = "imp7"
    s.job_path = str(tmp_path / "job")
    s.runners = ["runner"]
    s.runners_id = {"runner": "runner-1"}
    return s


def test_collect_light_downloads_plots_and_logs(tmp_path):
    s = _storage(tmp_path)
    job = mock.Mock(); job.status.return_value = CODA
    wf = mock.Mock()
    s._get_runner_contexts = lambda: [("runner", job, wf)]
    s.collect()
    # download_selected called with the is_plot predicate on stageout
    assert wf.download_selected.call_args.args[1] is ims.file_types.is_plot
    wf.download_logs.assert_called_once()
    wf.download_outputs.assert_not_called()


def test_collect_files_uses_predicate(tmp_path):
    s = _storage(tmp_path)
    wf = mock.Mock()
    s._get_runner_contexts = lambda: [("runner", mock.Mock(), wf)]
    s.collect_files("stageout", "*.root")
    pred = wf.download_selected.call_args.args[1]
    assert pred("ntuple.root") and not pred("mass.png")


def test_file_status_merges(tmp_path):
    s = _storage(tmp_path)
    stageout = tmp_path / "job" / "runner-1" / "stageout"
    stageout.mkdir(parents=True)
    (stageout / "mass.png").write_bytes(b"img")        # downloaded
    wf = mock.Mock()
    wf.list_runner_files.return_value = [
        {"name": "mass.png", "size": 3},
        {"name": "ntuple.root", "size": 99},
    ]
    s._get_runner_contexts = lambda: [("runner", mock.Mock(), wf)]
    rows = {r["name"]: r for r in s.file_status("stageout")}
    assert rows["mass.png"]["in_yuki"] and rows["mass.png"]["type"] == "plot"
    assert rows["ntuple.root"]["in_runner"] and not rows["ntuple.root"]["in_yuki"]
    assert rows["ntuple.root"]["type"] == "data"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wave/workdir/Celebi/Yuki/UnitTest && python -m pytest test_impression_storage_select.py -v`
Expected: FAIL — `collect_files`/`file_status` missing; `collect` still calls `download`.

- [ ] **Step 3: Write minimal implementation**

In `Yuki/kernel/impression_storage.py`, add imports at the top:
```python
import os
from . import file_types
```
Replace the `collect` method (lines 45-56) with:
```python
    def collect(self):
        """Light default: plots + logs on success, logs on failure."""
        for name, job, workflow in self._get_runner_contexts():
            job_status = job.status(musical=True)
            if job_status == CODA:
                print(f"[{name}] Collecting plots + logs...")
                workflow.download_selected(self.impression, file_types.is_plot, "stageout")
                workflow.download_logs(self.impression)
            elif job_status in (FAILED, DISSONANCE):
                print(f"[{name}] Collecting logs...")
                workflow.download_logs(self.impression)
```
Add after `collect_outputs` (after line 63):
```python
    def collect_files(self, kind, spec):
        """Download a subset of <kind> files matching a selection spec."""
        predicate = file_types.make_predicate(spec)
        for name, job, workflow in self._get_runner_contexts():
            if job.status(musical=True) == CODA:
                print(f"[{name}] Collecting {kind} matching {spec!r}...")
                workflow.download_selected(self.impression, predicate, kind)

    def file_status(self, kind="stageout"):
        """Merge runner listing with downloaded Storage state for <kind>."""
        result = []
        for name, _job, workflow in self._get_runner_contexts():
            machine_id = self.runners_id.get(name)
            storage_dir = os.path.join(self.job_path, machine_id, kind)
            downloaded = set(os.listdir(storage_dir)) if os.path.isdir(storage_dir) else set()
            try:
                runner_files = workflow.list_runner_files(self.impression, kind)
            except Exception:
                runner_files = []
            seen = set()
            for rf in runner_files:
                seen.add(rf["name"])
                result.append({
                    "name": rf["name"],
                    "size": rf.get("size", 0),
                    "type": file_types.classify(rf["name"]),
                    "in_runner": True,
                    "in_yuki": rf["name"] in downloaded,
                })
            for fn in sorted(downloaded - seen):
                full = os.path.join(storage_dir, fn)
                result.append({
                    "name": fn,
                    "size": os.path.getsize(full) if os.path.isfile(full) else 0,
                    "type": file_types.classify(fn),
                    "in_runner": False,
                    "in_yuki": True,
                })
        return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wave/workdir/Celebi/Yuki/UnitTest && python -m pytest test_impression_storage_select.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
cd /Users/wave/workdir/Celebi/Yuki
git add Yuki/kernel/impression_storage.py UnitTest/test_impression_storage_select.py
git commit -m "feat: light collect, collect_files, and file_status on ImpressionStorage"
```

---

### Task A5: Routes — `/collect-files` and `/file-status`

**Files:**
- Modify: `Yuki/server/routes/workflow.py` (add `/collect-files`)
- Modify: `Yuki/server/routes/execution.py` (add `/file-status`)
- Test: `Yuki/UnitTest/test_routes_select.py`

**Interfaces:**
- Consumes: `ImpressionStorage.collect_files`/`file_status` (A4).
- Produces: HTTP `GET /collect-files/<project_uuid>/<impression>` (query `kind`,`type`,`pattern`,`names`); `GET /file-status/<project_uuid>/<impression>/<machine>` (query `kind`) → JSON list.

- [ ] **Step 1: Write the failing test**

Create `Yuki/UnitTest/test_routes_select.py`:
```python
from unittest import mock

from Yuki.server.routes import workflow as wf_routes
from Yuki.server.routes import execution as ex_routes


def test_collect_files_route_passes_spec():
    app = _app(wf_routes.bp)
    with mock.patch.object(wf_routes, "ImpressionStorage") as S:
        inst = S.return_value
        c = app.test_client()
        r = c.get("/collect-files/proj/imp?kind=stageout&pattern=*.root")
        assert r.status_code == 200
        inst.collect_files.assert_called_once_with("stageout", "*.root")


def test_collect_files_route_type_keyword():
    app = _app(wf_routes.bp)
    with mock.patch.object(wf_routes, "ImpressionStorage") as S:
        c = app.test_client()
        c.get("/collect-files/proj/imp?type=plots")
        S.return_value.collect_files.assert_called_once_with("stageout", "plots")


def test_file_status_route_returns_json():
    app = _app(ex_routes.bp)
    with mock.patch.object(ex_routes, "ImpressionStorage") as S:
        S.return_value.file_status.return_value = [
            {"name": "mass.png", "size": 3, "type": "plot",
             "in_runner": True, "in_yuki": True}]
        c = app.test_client()
        r = c.get("/file-status/proj/imp/runner?kind=stageout")
        assert r.status_code == 200
        assert r.get_json()[0]["name"] == "mass.png"


def _app(bp):
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(bp)
    return app
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wave/workdir/Celebi/Yuki/UnitTest && python -m pytest test_routes_select.py -v`
Expected: FAIL — 404 for the new routes (and `ImpressionStorage` not imported in `execution`).

- [ ] **Step 3: Write minimal implementation**

In `Yuki/server/routes/workflow.py`, add `from flask import request` (extend the existing flask import) and append:
```python
@bp.route("/collect-files/<project_uuid>/<impression>", methods=['GET'])
def collect_files(project_uuid, impression):
    """Collect a subset of files matching a selection spec.

    Query: kind (default stageout); one of type / pattern / names.
    """
    kind = request.args.get("kind", "stageout")
    if request.args.get("type"):
        spec = request.args.get("type")
    elif request.args.get("pattern"):
        spec = request.args.get("pattern")
    elif request.args.get("names"):
        spec = request.args.get("names")   # comma list handled below
    else:
        spec = "all"
    storage = ImpressionStorage(project_uuid, impression)
    if request.args.get("names"):
        for one in request.args.get("names").split(","):
            if one:
                storage.collect_files(kind, one)
    else:
        storage.collect_files(kind, spec)
    return "ok"
```
In `Yuki/server/routes/execution.py`, add `from Yuki.kernel.impression_storage import ImpressionStorage` and `from flask import jsonify, request` (extend existing imports), then append:
```python
@bp.route("/file-status/<project_uuid>/<impression>/<machine>", methods=['GET'])
def file_status(project_uuid, impression, machine):
    """Return merged runner + Storage file listing for an impression."""
    kind = request.args.get("kind", "stageout")
    storage = ImpressionStorage(project_uuid, impression)
    return jsonify(storage.file_status(kind))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wave/workdir/Celebi/Yuki/UnitTest && python -m pytest test_routes_select.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
cd /Users/wave/workdir/Celebi/Yuki
git add Yuki/server/routes/workflow.py Yuki/server/routes/execution.py UnitTest/test_routes_select.py
git commit -m "feat: add /collect-files and /file-status routes"
```

---

### Task A6: Refactor status.py to use file_types (dedupe image lists)

**Files:**
- Modify: `Yuki/server/routes/status.py` (lines ~227-228; and ~356-361 if present)
- Test: `Yuki/UnitTest/test_file_types.py` (extend — assert parity with the old inline set)

**Interfaces:**
- Consumes: `file_types.is_plot` (A1). No external signature change.

- [ ] **Step 1: Write the failing test**

Append to `Yuki/UnitTest/test_file_types.py`:
```python
def test_is_plot_covers_legacy_image_set():
    # The old status.py inline set: png/jpg/jpeg/gif must still classify as plot.
    for ext in (".png", ".jpg", ".jpeg", ".gif"):
        assert file_types.is_plot("x" + ext) is True
```

- [ ] **Step 2: Run test to verify it fails (or passes trivially), then make the refactor**

Run: `cd /Users/wave/workdir/Celebi/Yuki/UnitTest && python -m pytest test_file_types.py -v`
Expected: PASS (the assertion already holds). This test guards the refactor below.

- [ ] **Step 3: Apply the refactor**

In `Yuki/server/routes/status.py`, add `from Yuki.kernel import file_types` to the imports. Replace the inline image check at line 228:
```python
        is_image = file_types.is_plot(filename)
```
(Leave `is_text`, `watermarked`, `is_log` as-is.) If the second inline image list near line 356-361 exists in this file, replace its `is_image = ext in [...]` with `is_image = file_types.is_plot(filename)` too.

- [ ] **Step 4: Run the status route tests**

Run: `cd /Users/wave/workdir/Celebi/Yuki/UnitTest && python -m pytest -k "status or file_types" -v`
Expected: PASS (no regressions).

- [ ] **Step 5: Commit**

```bash
cd /Users/wave/workdir/Celebi/Yuki
git add Yuki/server/routes/status.py UnitTest/test_file_types.py
git commit -m "refactor: status.py uses file_types.is_plot instead of inline image list"
```

---

### Task A7: Selective + logs-inclusive booking

**Files:**
- Modify: `Yuki/kernel/reana_booker.py` (`book_project` ~line 95 & 191-197; `_upload_stageout_files` ~line 479)
- Modify: `Yuki/server/routes/booking.py` (lines 157, 166, 204; and the `/book-reana-stream` handler near line 255/304 — apply the same three edits)
- Test: `Yuki/UnitTest/test_reana_booker_upload_mode.py`

**Interfaces:**
- Consumes: `file_types.make_predicate` (A1).
- Produces: `book_project(..., upload_mode="plots+logs")`; `_upload_stageout_files(workflow_id, project_path, repo_metadata, upload_mode="plots+logs")` filters by mode and additionally uploads `logs/` when the mode includes logs.

Mode semantics: `upload_mode` is a `+`-joined set of tokens. `plots`→plot stageout files; `data`→non-plot stageout files; `all`→every stageout file; `logs`→include the logs dir. Default `plots+logs`.

- [ ] **Step 1: Write the failing test**

Create `Yuki/UnitTest/test_reana_booker_upload_mode.py`:
```python
import os
from unittest import mock

from Yuki.kernel import reana_booker


def _booker():
    b = reana_booker.ReanaBooker.__new__(reana_booker.ReanaBooker)
    b.access_token = "tok"
    b._notify = lambda *a, **k: None
    return b


def _layout(tmp_path):
    base = tmp_path / ".Yuki" / "Storage" / "proj-1" / "imp-abc" / "runner-1"
    (base / "stageout").mkdir(parents=True)
    (base / "logs").mkdir(parents=True)
    (base / "stageout" / "mass.png").write_bytes(b"img")
    (base / "stageout" / "ntuple.root").write_bytes(b"data")
    (base / "logs" / "celebi.stdout").write_bytes(b"log")
    return base


def _run(booker, tmp_path, mode):
    cfg = tmp_path / "proj" / ".celebi"
    cfg.mkdir(parents=True)
    (cfg / "config.json").write_text('{"project_uuid": "proj-1"}')
    meta = {"objects": [{"impression": "imp-abc"}]}
    uploaded = []
    with mock.patch.dict(os.environ, {"YUKIDIR": str(tmp_path / ".Yuki")}), \
         mock.patch.object(reana_booker, "reana_client") as rc:
        rc.upload_file.side_effect = lambda **kw: uploaded.append(kw["file_name"])
        booker._upload_stageout_files("wf", str(tmp_path / "proj"), meta, upload_mode=mode)
    return uploaded


def test_default_plots_and_logs(tmp_path):
    _layout(tmp_path)
    names = _run(_booker(), tmp_path, "plots+logs")
    assert any(n.endswith("stageout/mass.png") for n in names)
    assert any(n.endswith("logs/celebi.stdout") for n in names)
    assert not any(n.endswith("ntuple.root") for n in names)   # data excluded


def test_all_includes_data(tmp_path):
    _layout(tmp_path)
    names = _run(_booker(), tmp_path, "all")
    assert any(n.endswith("stageout/ntuple.root") for n in names)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wave/workdir/Celebi/Yuki/UnitTest && python -m pytest test_reana_booker_upload_mode.py -v`
Expected: FAIL — `_upload_stageout_files()` has no `upload_mode` kwarg.

- [ ] **Step 3: Write minimal implementation**

In `Yuki/kernel/reana_booker.py` add `from . import file_types` near the imports. Change `book_project` signature (line ~95) from `stageout: bool = False` to add `upload_mode: str = "plots+logs"`, and the call site (line 194) to:
```python
        if stageout:
            try:
                self._upload_stageout_files(
                    workflow_id, project_path, new_metadata, upload_mode=upload_mode)
```
Change `_upload_stageout_files` signature (line 479-480) to:
```python
    def _upload_stageout_files(self, workflow_id: str, project_path: str,
                                repo_metadata: dict, upload_mode: str = "plots+logs"):
```
Add, right after computing `impressions` and before the per-impression loop (~line 540), the mode parsing:
```python
        tokens = set(upload_mode.split("+"))
        include_logs = "logs" in tokens or "all" in tokens
        if "all" in tokens:
            stageout_spec = "all"
        elif "data" in tokens and "plots" in tokens:
            stageout_spec = "all"
        elif "data" in tokens:
            stageout_spec = "data"
        elif "plots" in tokens:
            stageout_spec = "plots"
        else:
            stageout_spec = None     # logs-only mode uploads no stageout
        stage_pred = file_types.make_predicate(stageout_spec) if stageout_spec else (lambda n: False)
```
Wrap the existing stageout upload in the predicate by changing the inner loop (lines 556-557) to:
```python
                for root, _dirs, files in os.walk(stageout_dir):
                    for filename in files:
                        if not stage_pred(filename):
                            continue
                        file_path = os.path.join(root, filename)
```
Then, still inside the `for runner_id in os.listdir(impression_dir)` loop, after the stageout `os.walk` block, add the logs upload:
```python
                if include_logs:
                    logs_dir = os.path.join(impression_dir, runner_id, "logs")
                    if os.path.isdir(logs_dir):
                        for root, _dirs, files in os.walk(logs_dir):
                            for filename in files:
                                file_path = os.path.join(root, filename)
                                rel_path = os.path.relpath(file_path, logs_dir)
                                upload_name = (
                                    f"impression_data/{impression_id}/logs/{rel_path}")
                                try:
                                    with open(file_path, "rb") as f:
                                        content = f.read()
                                    reana_client.upload_file(
                                        workflow=workflow_id, file_=content,
                                        file_name=upload_name, access_token=self.access_token)
                                    total_uploaded += 1
                                except Exception as e:
                                    logger.warning("Failed to upload log %s: %s", upload_name, e)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wave/workdir/Celebi/Yuki/UnitTest && python -m pytest test_reana_booker_upload_mode.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Wire the route, then commit**

In `Yuki/server/routes/booking.py`, in **both** the `/book-reana` and the streaming booking handler, read the new field and pass it through. Add after the `stageout = ...` line (166, and its streaming twin ~255):
```python
        upload_mode = request.form.get("upload", "plots+logs")
        if upload_mode == "all":
            stageout = True            # ensure the upload step runs
```
and change the `book_project(...)` call (line 204, and streaming twin ~304) to:
```python
            result = booker.book_project(
                project_path, project_name, stageout=stageout, upload_mode=upload_mode)
```
Also update the route docstring's form-field list to mention `upload`.

```bash
cd /Users/wave/workdir/Celebi/Yuki
git add Yuki/kernel/reana_booker.py Yuki/server/routes/booking.py UnitTest/test_reana_booker_upload_mode.py
git commit -m "feat: selective, logs-inclusive REANA booking via upload_mode"
```

> **Note:** existing `--stageout` (sent as form field `stageout=true`) still triggers a full upload because `book_project` keeps `stageout` as the on/off switch; `upload_mode` defaults to `plots+logs`, so an old client sending only `stageout=true` uploads plots+logs+ (since data not in mode) — see Task B5 which makes the client send `upload=all` for `--stageout`.

---

# Phase B — Celebi (client)

### Task B1: Communicator — `file_status` and `collect_files`

**Files:**
- Modify: `CelebiChrono/kernel/chern_communicator.py` (after `collect_logs`, ~line 501)
- Test: `CelebiChrono` → `UnitTest/test_cherncommunicator_select.py`

**Interfaces:**
- Consumes: existing `self.serverurl()`, `self.project_uuid`, `self.timeout`.
- Produces:
  - `file_status(self, impression, machine="none", kind="stageout") -> list[dict]`
  - `collect_files(self, impression, kind="stageout", spec_type=None, pattern=None, names=None) -> str`

- [ ] **Step 1: Write the failing test**

Create `Celebi/UnitTest/test_cherncommunicator_select.py`:
```python
from unittest import mock
from CelebiChrono.kernel.chern_communicator import ChernCommunicator


def _cc():
    cc = ChernCommunicator.__new__(ChernCommunicator)
    cc.project_uuid = "proj"
    cc.timeout = 1
    cc.serverurl = lambda: "host:1"
    return cc


def test_collect_files_builds_type_query():
    cc = _cc()
    imp = mock.Mock(uuid="abc")
    with mock.patch("CelebiChrono.kernel.chern_communicator.requests") as rq:
        rq.get.return_value.text = "ok"
        cc.collect_files(imp, kind="stageout", spec_type="plots")
        url = rq.get.call_args.args[0]
    assert "/collect-files/proj/abc" in url and "type=plots" in url and "kind=stageout" in url


def test_file_status_parses_json():
    cc = _cc()
    imp = mock.Mock(uuid="abc")
    with mock.patch("CelebiChrono.kernel.chern_communicator.requests") as rq:
        rq.get.return_value.json.return_value = [{"name": "mass.png"}]
        out = cc.file_status(imp, "runner", "stageout")
    assert out[0]["name"] == "mass.png"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wave/workdir/Celebi/UnitTest && python -m pytest test_cherncommunicator_select.py -v`
Expected: FAIL — methods missing.

- [ ] **Step 3: Write minimal implementation**

In `CelebiChrono/kernel/chern_communicator.py`, after `collect_logs` (line 501) add:
```python
    def collect_files(self, impression, kind="stageout",
                      spec_type=None, pattern=None, names=None):
        """Collect a subset of files matching a type, glob, or name list."""
        url = self.serverurl()
        params = f"kind={kind}"
        if spec_type:
            params += f"&type={spec_type}"
        elif pattern:
            params += f"&pattern={pattern}"
        elif names:
            params += f"&names={','.join(names)}"
        r = requests.get(
            f"http://{url}/collect-files/{self.project_uuid}/{impression.uuid}?{params}",
            timeout=self.timeout * 1000,
        )
        return r.text

    def file_status(self, impression, machine="none", kind="stageout"):
        """Return merged runner+Storage file listing for an impression."""
        url = self.serverurl()
        imp = impression.uuid if hasattr(impression, "uuid") else impression
        try:
            r = requests.get(
                f"http://{url}/file-status/{self.project_uuid}/{imp}/{machine}?kind={kind}",
                timeout=self.timeout,
            )
            return r.json()
        except Exception:
            return []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wave/workdir/Celebi/UnitTest && python -m pytest test_cherncommunicator_select.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
cd /Users/wave/workdir/Celebi/Celebi
git add CelebiChrono/kernel/chern_communicator.py UnitTest/test_cherncommunicator_select.py
git commit -m "feat: client collect_files and file_status communicator methods"
```

---

### Task B2: `JobManager.collect` selector + predecessor fix

**Files:**
- Modify: `CelebiChrono/kernel/vtask_job.py` (`collect` lines 123-136; `_check_preceding_jobs` line 479)
- Test: `Celebi/UnitTest/test_vtask_collect_selector.py`

**Interfaces:**
- Consumes: `cherncc.collect`/`collect_outputs`/`collect_logs`/`collect_files` (B1).
- Produces: `collect(self, selector="")` parsing per the Selector vocabulary table.

- [ ] **Step 1: Write the failing test**

Create `Celebi/UnitTest/test_vtask_collect_selector.py`:
```python
from unittest import mock
from CelebiChrono.kernel.vtask_job import JobManager


def _jm():
    jm = JobManager.__new__(JobManager)
    jm.impression = lambda: mock.Mock(uuid="abc")
    return jm


def _patch_cc():
    cc = mock.Mock()
    return mock.patch(
        "CelebiChrono.kernel.vtask_job.ChernCommunicator.instance",
        return_value=cc), cc


def test_default_calls_light_collect():
    jm = _jm(); p, cc = _patch_cc()
    with p:
        jm.collect("")
    cc.collect.assert_called_once()


def test_all_calls_outputs_and_logs():
    jm = _jm(); p, cc = _patch_cc()
    with p:
        jm.collect("all")
    cc.collect_outputs.assert_called_once()
    cc.collect_logs.assert_called_once()


def test_plots_keyword():
    jm = _jm(); p, cc = _patch_cc()
    with p:
        jm.collect("plots")
    assert cc.collect_files.call_args.kwargs["spec_type"] == "plots"


def test_glob_pattern():
    jm = _jm(); p, cc = _patch_cc()
    with p:
        jm.collect("*.root")
    assert cc.collect_files.call_args.kwargs["pattern"] == "*.root"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wave/workdir/Celebi/UnitTest && python -m pytest test_vtask_collect_selector.py -v`
Expected: FAIL — current `collect` only accepts `all|outputs|logs`.

- [ ] **Step 3: Write minimal implementation**

Replace `JobManager.collect` (lines 123-136) in `CelebiChrono/kernel/vtask_job.py`:
```python
    def collect(self, selector=""):
        """Collect job results by selector.

        "" -> plots+logs (light); "all" -> outputs+logs; "plots"/"data" ->
        typed stageout; "logs" -> logs; otherwise a glob/name pattern.
        """
        msg = Message()
        cherncc = ChernCommunicator.instance()
        impression = self.impression()
        selector = (selector or "").strip()
        if selector in ("", "outputs"):
            # "outputs" kept as deprecated alias for the light default's data path
            if selector == "outputs":
                cherncc.collect_outputs(impression)
            else:
                cherncc.collect(impression)
        elif selector == "all":
            cherncc.collect_outputs(impression)
            cherncc.collect_logs(impression)
        elif selector in ("plots", "data"):
            cherncc.collect_files(impression, kind="stageout", spec_type=selector)
        elif selector == "logs":
            cherncc.collect_logs(impression)
        elif any(ch in selector for ch in "*?["):
            cherncc.collect_files(impression, kind="stageout", pattern=selector)
        else:
            cherncc.collect_files(impression, kind="stageout", names=[selector])
        msg.add(f"Collected '{selector or 'plots+logs'}' of impression {impression}")
        return msg
```
Change `_check_preceding_jobs` line 479 from `cherncc.collect(pre.impression())` to:
```python
            cherncc.collect_outputs(pre.impression())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wave/workdir/Celebi/UnitTest && python -m pytest test_vtask_collect_selector.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
cd /Users/wave/workdir/Celebi/Celebi
git add CelebiChrono/kernel/vtask_job.py UnitTest/test_vtask_collect_selector.py
git commit -m "feat: collect selector parsing; predecessor prep collects full stageout"
```

---

### Task B3: `status` shows the stageout file table

**Files:**
- Modify: `CelebiChrono/kernel/vtask.py` (`printed_status`, replace the `Output files` block lines 189-192)
- Test: `Celebi/UnitTest/test_printed_status_table.py`

**Interfaces:**
- Consumes: `cherncc.file_status` (B1). Renders name/size/type/in-yuki rows.

- [ ] **Step 1: Write the failing test**

Create `Celebi/UnitTest/test_printed_status_table.py`:
```python
from unittest import mock
from CelebiChrono.kernel.vtask import VTask


def test_status_table_lists_runner_and_downloaded():
    t = VTask.__new__(VTask)
    t.impression = lambda: mock.Mock(uuid="abc")
    rows = [
        {"name": "mass.png", "size": 240, "type": "plot", "in_runner": True, "in_yuki": True},
        {"name": "ntuple.root", "size": 3221225472, "type": "data",
         "in_runner": True, "in_yuki": False},
    ]
    cc = mock.Mock(); cc.file_status.return_value = rows
    msg = t._stageout_table(cc, "runner")     # helper under test
    text = "".join(m[0] for m in msg.messages)
    assert "mass.png" in text and "ntuple.root" in text
    assert "ROOT" not in text  # sanity: not echoing junk
    assert "✓" in text or "yes" in text.lower()   # downloaded marker shown
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wave/workdir/Celebi/UnitTest && python -m pytest test_printed_status_table.py -v`
Expected: FAIL — `_stageout_table` does not exist.

- [ ] **Step 3: Write minimal implementation**

In `CelebiChrono/kernel/vtask.py`, add a helper method to `VTask`:
```python
    @staticmethod
    def _human_size(num):
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if num < 1024 or unit == "TB":
                return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
            num /= 1024

    def _stageout_table(self, cherncc, runner):
        """Build a Message listing stageout files: name, size, type, in-Yuki."""
        message = Message()
        rows = cherncc.file_status(self.impression(), runner, "stageout")
        message.add("Stageout files:\n", "title0")
        if not rows:
            message.add("    (no files reported by runner; "
                        "use 'collect' then check again)\n")
            return message
        message.add(f"    {'NAME':<28}{'SIZE':>10}  {'TYPE':<6} IN YUKI\n")
        for r in rows:
            mark = "✓" if r.get("in_yuki") else "✗"
            message.add(
                f"    {r['name']:<28}{self._human_size(r.get('size', 0)):>10}  "
                f"{r.get('type', ''):<6} {mark}\n")
        return message
```
Replace the `Output files (collected on DIET)` block (lines 189-192) with:
```python
            message.messages.extend(self._stageout_table(cherncc, runner).messages)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wave/workdir/Celebi/UnitTest && python -m pytest test_printed_status_table.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/wave/workdir/Celebi/Celebi
git add CelebiChrono/kernel/vtask.py UnitTest/test_printed_status_table.py
git commit -m "feat: status shows stageout file table with runner vs downloaded state"
```

---

### Task B4: Thread the selector through command surfaces

**Files:**
- Modify: `CelebiChrono/kernel/vobj_execution.py` (`collect`, lines 298-326)
- Modify: `CelebiChrono/interface/shell_modules/execution_management.py` (`collect`, lines 89-124)
- Modify: `CelebiChrono/interface/chern_shell/commands_basic.py` (`do_collect`, lines 48-65)
- Modify: `CelebiChrono/celebi_cli/commands/execution_management.py` (`collect_command`, lines 179-196)
- Test: `Celebi/UnitTest/test_collect_command_surface.py`

**Interfaces:**
- Consumes: `JobManager.collect(selector)` (B2) via `VObject.collect`.
- Produces: each surface forwards a free-form selector string (default `""`).

- [ ] **Step 1: Write the failing test**

Create `Celebi/UnitTest/test_collect_command_surface.py`:
```python
from unittest import mock
from CelebiChrono.interface.chern_shell import commands_basic


def test_do_collect_forwards_pattern():
    cmd = commands_basic.__dict__  # module-level access to the shell class
    from CelebiChrono.interface.chern_shell.commands_basic import BasicCommands
    inst = BasicCommands.__new__(BasicCommands)
    with mock.patch(
        "CelebiChrono.interface.chern_shell.commands_basic.shell"
    ) as sh:
        sh.collect.return_value = mock.Mock(messages=[])
        inst.do_collect("*.root")
        sh.collect.assert_called_once_with("*.root")
```
(If the shell class name differs, adjust the import; verify with
`grep -n "class .*Cmd\|def do_collect" CelebiChrono/interface/chern_shell/commands_basic.py`.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wave/workdir/Celebi/UnitTest && python -m pytest test_collect_command_surface.py -v`
Expected: FAIL — current `do_collect` ignores arbitrary args and routes only `all`/`outputs`/`logs`.

- [ ] **Step 3: Write minimal implementation**

`vobj_execution.py` `collect` (line 298) — change signature and forwarding to pass the selector straight through:
```python
    def collect(self, contents="") -> Message:
        """ Collect the results from the runner. """
        cherncc = ChernCommunicator.instance()
        dite_status = cherncc.dite_status()
        if dite_status != "connected":
            msg = Message()
            msg.add("DITE is not connected. Please check the connection.", "warning")
            return msg
        if not self.is_task_or_algorithm():
            for sub_object in self.sub_objects_recursively():
                if sub_object.is_task():
                    sub_object.collect(contents)
            msg = Message()
            msg.add("Results of sub-tasks collected.", "info")
            return msg
        if self.is_task():
            self.get_vtask(self.path).collect(contents)
            msg = Message()
            msg.add(f"Results of task {self.path} collected.", "info")
            return msg
        msg = Message()
        msg.add(f"Algorithm {self.path} doesn't have results to collect.", "info")
        return msg
```
`shell_modules/execution_management.py` `collect` (line 89) — drop the 3-value whitelist and forward the string:
```python
def collect(contents: str = "") -> Message:
    """Collect task results. contents: '', 'all', 'plots', 'data', 'logs',
    or a glob/filename. Default ('') collects plots + logs."""
    return MANAGER.current_object().collect(contents)
```
`chern_shell/commands_basic.py` `do_collect` (lines 48-65):
```python
    def do_collect(self, arg: str) -> None:
        """Collect results. Usage: collect [all|plots|data|logs|<glob>|<name>]"""
        try:
            result = shell.collect(arg.strip())
            if result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error collecting data: {e}")
```
`celebi_cli/commands/execution_management.py` `collect_command` (lines 179-196):
```python
@click.command(name="collect")
@click.argument("contents", type=str, default="", required=False)
def collect_command(contents: str) -> None:
    """Collect task results: [all|plots|data|logs|<glob>|<name>] (default: plots+logs)."""
    try:
        from CelebiChrono.interface.shell import collect
        _handle_result(collect(contents))
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wave/workdir/Celebi/UnitTest && python -m pytest test_collect_command_surface.py -v`
Expected: PASS. Also run the existing suite to catch fallout: `python -m pytest -k collect -v`.

- [ ] **Step 5: Commit**

```bash
cd /Users/wave/workdir/Celebi/Celebi
git add CelebiChrono/kernel/vobj_execution.py CelebiChrono/interface/shell_modules/execution_management.py CelebiChrono/interface/chern_shell/commands_basic.py CelebiChrono/celebi_cli/commands/execution_management.py UnitTest/test_collect_command_surface.py
git commit -m "feat: forward free-form collect selector through all command surfaces"
```

---

### Task B5: book-reana `--upload` mode

**Files:**
- Modify: `CelebiChrono/interface/shell_modules/reana_booking.py` (`book_reana` sig line 375-382; `data` dict line 444-448)
- Modify: `CelebiChrono/celebi_cli/commands/booking.py` (lines 53-69)
- Modify: `CelebiChrono/main.py` (lines 606-622)
- Modify: `CelebiChrono/interface/chern_shell/commands_environment.py` (do_book_reana lines 322-355)
- Test: `Celebi/UnitTest/test_book_reana_upload.py`

**Interfaces:**
- Produces: `book_reana(..., upload="plots+logs")` sends form field `upload`; `--stageout` becomes an alias that sets `upload="all"`.

- [ ] **Step 1: Write the failing test**

Create `Celebi/UnitTest/test_book_reana_upload.py`:
```python
import inspect
from CelebiChrono.interface.shell_modules import reana_booking


def test_book_reana_has_upload_param_default_plots_logs():
    sig = inspect.signature(reana_booking.book_reana)
    assert "upload" in sig.parameters
    assert sig.parameters["upload"].default == "plots+logs"


def test_data_dict_includes_upload(monkeypatch):
    captured = {}

    def fake_sync(yuki_url, project_name, tar_buf, data, message):
        captured.update(data)
        return message

    monkeypatch.setattr(reana_booking, "_book_reana_sync", fake_sync)
    monkeypatch.setattr(reana_booking, "_pack_project_to_tar", lambda p: b"x")
    monkeypatch.setattr(reana_booking.csys, "project_path", lambda: "/tmp/proj")
    monkeypatch.setattr(reana_booking, "_get_yuki_server_url", lambda: "http://h:1")
    reana_booking.book_reana(project_path="/tmp/proj", upload="plots", stream=False)
    assert captured.get("upload") == "plots"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/wave/workdir/Celebi/UnitTest && python -m pytest test_book_reana_upload.py -v`
Expected: FAIL — no `upload` parameter.

- [ ] **Step 3: Write minimal implementation**

`reana_booking.py`: add `upload: str = "plots+logs"` to `book_reana`'s signature (keep `stageout: bool = False`), and in the `data` dict (line 444-448) replace the `stageout` entry logic with:
```python
    # --stageout is a legacy alias meaning "include the large data too".
    if stageout:
        upload = "all"
    data = {
        "project_name": project_name,
        "verify_ssl": "true" if verify_ssl else "false",
        "stageout": "true" if (stageout or upload == "all") else "false",
        "upload": upload,
    }
```
`celebi_cli/commands/booking.py` (53-69): add an option and pass it:
```python
@click.option("--upload", default="plots+logs",
              help="What to upload: plots+logs (default), plots, data, all, or a glob")
@click.option("--stageout", is_flag=True, default=False,
              help="[deprecated] alias for --upload all")
...
def book_reana_command(server_url, access_token, project_path, insecure, stageout, upload, no_stream):
    ...
            stageout=stageout,
            upload=upload,
```
`main.py` (606-622): mirror the same `--upload` option and `upload=upload` argument.
`chern_shell/commands_environment.py` `do_book_reana` (322-355): parse `--upload <mode>`:
```python
                elif args[i] == "--upload" and i + 1 < len(args):
                    upload = args[i + 1]
                    i += 1
```
initialize `upload = "plots+logs"` near the other defaults (line 332 area) and pass `upload=upload` into the `book_reana(...)` call (line 355).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/wave/workdir/Celebi/UnitTest && python -m pytest test_book_reana_upload.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
cd /Users/wave/workdir/Celebi/Celebi
git add CelebiChrono/interface/shell_modules/reana_booking.py CelebiChrono/celebi_cli/commands/booking.py CelebiChrono/main.py CelebiChrono/interface/chern_shell/commands_environment.py UnitTest/test_book_reana_upload.py
git commit -m "feat: book-reana --upload mode (default plots+logs); --stageout aliases --upload all"
```

---

### Task B6: Full-suite regression + docs

**Files:**
- Modify: `CelebiChrono/interface/shell_modules/execution_management.py` (docstrings for `collect`), `Yuki/server/routes/booking.py` (docstring) — reflect new behavior.
- Test: both repos' full suites.

- [ ] **Step 1: Run Yuki suite**

Run: `cd /Users/wave/workdir/Celebi/Yuki/UnitTest && python -m pytest -v`
Expected: PASS (existing + new). Investigate and fix any test that assumed `/collect` downloaded all stageout, or that `collect()` called `workflow.download`.

- [ ] **Step 2: Run Celebi suite**

Run: `cd /Users/wave/workdir/Celebi/UnitTest && python -m pytest -v`
Expected: PASS. Fix any existing test that called `collect("outputs")` expecting old behavior (the alias still routes to `collect_outputs`, so it should hold).

- [ ] **Step 3: Lint both packages**

Run:
```bash
cd /Users/wave/workdir/Celebi/Celebi && python -m pylint --rcfile=.pylintrc $(git ls-files "CelebiChrono/*.py") | tail -5
cd /Users/wave/workdir/Celebi/Yuki && python -m pylint --rcfile=.pylintrc $(git ls-files "Yuki/*.py") | tail -5
```
Expected: no new errors introduced by the changed files.

- [ ] **Step 4: Update user-facing docstrings**

Edit the `collect` docstring in `execution_management.py` and the `/book-reana` route docstring to describe the new selectors/`upload` field (no placeholders — write the actual text).

- [ ] **Step 5: Commit**

```bash
cd /Users/wave/workdir/Celebi/Celebi
git add -A && git commit -m "docs: document collect selectors and book-reana upload modes"
cd /Users/wave/workdir/Celebi/Yuki
git add -A && git commit -m "docs: document /book-reana upload field"
```

---

## Self-Review

**Spec coverage:**
- Spec §1 (classifier) → A1; status.py dedupe → A6.
- Spec §2 (status visibility) → A2/A3 `list_runner_files`, A4 `file_status`, A5 `/file-status`, B1 `file_status`, B3 status table.
- Spec §3 (selective collect, light default, idempotency, predecessor fix) → A2/A3 `download_selected`, A4 light `collect`/`collect_files`, A5 `/collect-files` + repurposed `/collect`, B1 `collect_files`, B2 selector + predecessor, B4 surfaces.
- Spec §4 (selective booking, logs upload, default plots+logs, `--stageout` alias) → A7, B5.
- Spec §5 (back-compat, REANA expiry, single source of truth) → A2/A4 (`list_runner_files` returns `[]` on error; `file_status` falls back to Storage), A6 (one classifier), B1 (`file_status` swallows errors).

**Placeholder scan:** No TBD/TODO; every code step shows complete code. Task B4 Step 1 notes a grep fallback for the shell class name — that is a verification instruction, not a placeholder; the implementer confirms the class name before editing.

**Type consistency:** `download_selected(impression, predicate, kind)` is defined identically in A2 (REANA) and A3 (native) and called that way in A4. `file_status` returns the same dict shape in A4 (server) and is consumed in B3 via B1. `collect_files(kind, spec)` (storage, A4) vs `collect_files(impression, kind=, spec_type=/pattern=/names=)` (communicator, B1) are deliberately different layers — the route (A5) bridges them by turning query params into `(kind, spec)`. `make_predicate` accepts the same spec tokens used by the client selector (B2) and booking modes (A7).

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-28-selective-stageout-collection.md`. Two execution options:

1. **Subagent-Driven (recommended)** — a fresh subagent per task, with review between tasks; fast iteration and isolation.
2. **Inline Execution** — execute tasks in this session with checkpoints for review.

Which approach?
