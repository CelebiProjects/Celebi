# Selective, type-aware stageout collection & booking

**Date:** 2026-06-28
**Status:** Approved design, pending implementation plan
**Repos affected:** `Celebi` (client, `CelebiChrono`) and `Yuki` (server, "DITE"), sibling directories under `/Users/wave/workdir/Celebi/`.

## Problem

Every `collect` pulls a task's entire `stageout/` directory from the runner (REANA / native) into Yuki's local Storage. In HEP workflows `stageout/` often contains multi-GB data samples that are rarely needed locally — the user almost always just wants to see the plots and logs. The same all-or-nothing behavior affects `book-reana`, which uploads the whole `stageout/` (and never uploads logs). There is also no way to *see* what a finished task produced without first downloading all of it.

## Goals

1. `status` on a finished task lists the `stageout/` files (name, size, type), showing which exist in the runner vs which are already downloaded to Yuki.
2. `collect` can fetch a **subset** of files — by name or glob pattern.
3. `collect` can fetch files **by type** (plots / data / logs).
4. `collect` with no arguments defaults to a **light** set: plots + logs only.
5. `book-reana` can upload a subset, defaulting to **plots + logs** (not the large data), and uploads logs (which it currently never does).

## Non-goals

- No new output directory (the earlier `deliverable/` idea is dropped). Everything stays in the existing `stageout/` and `logs/` directories.
- No migration of existing impressions. Forward-only: old finished tasks keep working (their files are shown as already-downloaded; runner listing is best-effort).
- Making the plot/type extension set user-configurable is out of scope (a sensible built-in default ships; configurability is future work).
- The bulk `export-imp-stageout` / `import-imp-stageout` transfer routes are not changed.

## Background: current architecture (verified during exploration)

Data flow: **Runner** (REANA/native) → `collect` → **Yuki Storage** → `export` → **Client**.

- A finished job has `stageout/` (outputs) and `logs/` (logs) inside its runner workspace. Yuki downloads them into `~/.Yuki/Storage/<project_uuid>/<impression>/<machine_id>/{stageout,logs}/`, writing whole-dir marker files `stageout.downloaded` / `logs.downloaded`.
- Client `collect` (`CelebiChrono/kernel/vtask_job.py:123` → `chern_communicator.py` `collect`/`collect_outputs`/`collect_logs`) calls server endpoints `/collect`, `/collect-outputs`, `/collect-logs` (`Yuki/server/routes/workflow.py:17`). Server logic in `Yuki/kernel/impression_storage.py:45` (`collect` → stageout on success / logs on failure; `collect_outputs` → all stageout; `collect_logs` → logs).
- Per-workflow download lives in `Yuki/kernel/reana_workflow.py` (`download`, `download_outputs`, `download_logs`), `Yuki/kernel/native_workflow.py` (`_collect_artifacts`), and `Yuki/kernel/file_staging.py` (`stage_out`).
- **Listing without downloading is already possible**: REANA `client.list_files(name, token, "imp<short>/stageout")` returns remote file dicts with `name` and `size` (`reana_workflow.py:331`, used today only as a prelude to downloading). Native files are local under `~/.Yuki/LocalWorkflows/<uuid>/imp<short>/stageout/` — `os.listdir` + `os.path.getsize`.
- **Downloads are currently all-or-nothing** (one marker), but `client.download_file()` already fetches a single named file in a loop — subset download is a small extension.
- **`/outputs/<project>/<impression>/<machine>`** (`Yuki/server/routes/execution.py:117` → `ContainerJob.outputs()`) lists the Storage `stageout/` directory = the **already-downloaded** set. Client uses it via `output_files()` and the pattern-globbing `export()` (`CelebiChrono/kernel/vtask_job.py:401,424`).
- **Status**: client `VTask.printed_status()` (`CelebiChrono/kernel/vtask.py:132`) renders job status from `GET /status/...` (`Yuki/server/routes/status.py:59`). It does not currently show a per-file table.
- **Predecessor inputs**: before running a task, `_check_preceding_jobs` (`CelebiChrono/kernel/vtask_job.py:466`) calls `cherncc.collect(pre.impression())` to ensure the predecessor's outputs are in Storage, then `_link_preceding_jobs` exports them as the task's inputs. Downstream tasks consume the predecessor's **data** (full stageout).
- **book-reana**: `--stageout` flag (default off) flows client → `POST /book-reana` form field → `reana_booker.book_project(stageout=...)` → `_upload_stageout_files()` (`Yuki/kernel/reana_booker.py:479`), which walks **all** files under every impression's `stageout/` and uploads them to `impression_data/<impression>/stageout/...`. No type/size filtering; logs are never uploaded.

## Design

### Section 1 — Shared file classification (Yuki)

New module `Yuki/kernel/file_types.py` is the single source of truth for output file categories, replacing the ad-hoc image-extension lists currently duplicated in `Yuki/server/routes/status.py`.

```python
PLOT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".svg", ".webp", ".eps"}

def is_plot(filename: str) -> bool: ...        # extension in PLOT_EXTENSIONS
def classify(filename: str) -> str: ...        # "plot" | "data"
def make_predicate(spec) -> Callable[[str], bool]:
    """Build a name-predicate from a selection spec:
       type keyword 'plots'|'data'|'all', a glob pattern, or an explicit name list."""
```

Categories:
- **plot** — filename extension in `PLOT_EXTENSIONS`.
- **data** — any other file in `stageout/`.
- **logs** — membership of the `logs/` directory (not an extension; handled by directory, not `classify`).

`Yuki/server/routes/status.py` is refactored to import these helpers instead of its inline `is_image` lists, so the browser view and the new features agree on what a "plot" is.

### Section 2 — Visibility: `status` lists stageout files

**Server.** New method `list_runner_files(impression, kind="stageout")` on each workflow class (`reana_workflow.py`, `native_workflow.py`) returning `[{name, size}]`:
- REANA: `client.list_files(...)` on the `imp<short>/<kind>` prefix, mapping `name` (stripped of the `imp<short>/` prefix) and `size`. Returns `[]` if the workspace no longer exists (expired) — caught, not fatal.
- Native: `os.listdir` + `os.path.getsize` on `LocalWorkflows/<uuid>/imp<short>/<kind>/`.

New endpoint `GET /file-status/<project_uuid>/<impression>/<machine>?kind=stageout` (`Yuki/server/routes/execution.py` or `status.py`) returns the **merged** view of runner files and Storage files:
```json
[ { "name": "mass.png", "size": 245760, "type": "plot", "in_runner": true, "in_yuki": true },
  { "name": "ntuple.root", "size": 3435973836, "type": "data", "in_runner": true, "in_yuki": false } ]
```
- `in_yuki` = file present in `Storage/.../<machine>/stageout/`.
- `in_runner` = file present in the runner listing.
- `type` = `file_types.classify(name)`.
- If the runner listing is empty/unavailable, entries are built from Storage alone (all `in_runner=false`, `in_yuki=true`) plus a flag/note in the response so the client can warn that the runner workspace is unavailable.

**Client.** New `ChernCommunicator.file_status(impression, machine="none", kind="stageout")`. `VTask.printed_status()` is extended so that for a finished (`coda`) task it appends a stageout table:
```
stageout:
  NAME           SIZE     TYPE   IN YUKI
  mass.png       240 KB   plot   ✓
  fit.pdf        1.1 MB   plot   ✗
  ntuple.root    3.2 GB   data   ✗
```
Type and sizes come straight from the server response (client does no classification). When the runner workspace is unavailable, the table shows the downloaded files and prints a one-line note.

### Section 3 — Selective collect

**Idempotent, file-level downloads.** Downloads become idempotent per file: a file already present in Storage `stageout/` is skipped. The whole-dir marker (`stageout.downloaded`) now means "the complete set has been downloaded" and is written **only** after a full collect (all stageout). Partial/selective collects never write it. This lets a light `collect` (plots only) and a later `collect data` coexist correctly.

**Server.** New `download_selected(impression, kind, predicate)` on the workflow classes:
- REANA: `list_files(...)` → filter names by `predicate` → for each, skip if already in Storage, else `download_file(...)` and write into Storage.
- Native / `file_staging`: `os.listdir` the exec dir → filter → `shutil.copy2` the missing ones into Storage.

`Yuki/kernel/impression_storage.py` gains `collect_files(kind, spec)` (iterating runner contexts like the existing `collect*` methods), and its existing `collect` is **repurposed to the light default**: download plots from `stageout/` + all logs. `collect_outputs` keeps its meaning (all stageout data) and `collect_logs` is unchanged. `download_outputs`/`_collect_artifacts` are made idempotent (skip files already present) and keep writing the full-set marker.

Endpoints (`Yuki/server/routes/workflow.py`):
- `GET /collect/<p>/<i>` — repurposed → **plots + logs** (light default).
- `GET /collect-files/<p>/<i>?kind=stageout&type=plots|data|all&pattern=<glob>&names=a,b,c` — new, selective.
- `GET /collect-outputs/<p>/<i>` — unchanged meaning: all stageout (data + plots).
- `GET /collect-logs/<p>/<i>` — unchanged.

**Client.** `collect [SELECTOR ...]` argument parsing (in `vtask_job.collect`, surfaced through `vobj_execution.collect`, the shell `do_collect`, and the `celebi_cli` command):

| Invocation | Meaning | Communicator call |
|---|---|---|
| `collect` | plots + logs (light default) | `collect` → `/collect` |
| `collect all` | everything (data + plots + logs) | `collect_outputs` + `collect_logs` |
| `collect plots` | plot files from stageout | `collect_files(kind=stageout, type=plots)` |
| `collect data` | non-plot files from stageout | `collect_files(kind=stageout, type=data)` |
| `collect logs` | logs only | `collect_logs` |
| `collect '*.root'` / `collect mass.png` | glob / exact name(s) on stageout | `collect_files(kind=stageout, pattern=...)` / `names=...` |

Multiple positional selectors are allowed (e.g. `collect '*.root' '*.png'`). Anything that is not a reserved keyword (`all`/`plots`/`data`/`logs`) is treated as a glob/name pattern. The existing `contents="outputs"` API value is kept as a deprecated alias for `all`-stageout so existing callers and `collect_outputs()` keep working.

**Predecessor correctness.** `_check_preceding_jobs` is changed from `cherncc.collect(pre.impression())` to `cherncc.collect_outputs(pre.impression())` so that running a task still pulls the predecessor's full **data** stageout (downstream inputs), independent of the new light user-facing `collect` default. This is the automatic "download stageout when really needed" case.

### Section 4 — Selective book-reana

**Upload mode** replaces the boolean `--stageout`. An `upload` selection string flows client → server:
- Client `book_reana(..., upload="plots+logs")` (default) adds `"upload": <mode>` to the POST form data (`CelebiChrono/interface/shell_modules/reana_booking.py`).
- CLI/shell: `book-reana --upload <mode>` where `<mode>` ∈ `plots` | `logs` | `plots+logs` | `data` | `all` | `<glob>`; default `plots+logs`. The legacy `--stageout` flag is kept as a deprecated alias for `--upload all` (include the large data).

**Server.** `POST /book-reana` reads `upload` (default `plots+logs`) and passes it to `reana_booker.book_project(upload_mode=...)`. `_upload_stageout_files()` filters its `os.walk` loop with `file_types.make_predicate(upload_mode)`. A parallel step uploads the `logs/` directory to `impression_data/<impression>/logs/...` when the mode includes logs (`plots+logs`, `logs`, `all`). Booking thus defaults to uploading project code + plots + logs; large data is uploaded only with `--upload all`/`--upload data`/`--stageout`.

### Section 5 — Back-compat & edge cases

- **Old impressions:** `/file-status` falls back to Storage-only listing; `status` shows the downloaded files and a note. `collect` retains full capability.
- **REANA workspace expiry:** `list_runner_files` returns `[]` on error; `status` degrades to downloaded-only; selective `collect` of a not-yet-downloaded file then reports it is unavailable.
- **Idempotency:** mixing light and selective collects is safe because downloads skip files already in Storage and the full-set marker is only written on a complete collect.
- **Single source of truth:** plot/type classification lives only in `Yuki/kernel/file_types.py`; the client never classifies (it passes a spec and renders server-provided `type`).

## Affected files

### Celebi (client)
- `CelebiChrono/kernel/chern_communicator.py` — add `file_status`, `collect_files`; repurpose `collect` to light default; keep `collect_outputs`/`collect_logs`.
- `CelebiChrono/kernel/vtask_job.py` — `collect(selector...)` parsing; `_check_preceding_jobs` → `collect_outputs`; reuse `list_output_files`/`export` globbing.
- `CelebiChrono/kernel/vtask.py` — `printed_status()` stageout table.
- `CelebiChrono/kernel/vobj_execution.py` — thread selector through `collect`.
- `CelebiChrono/interface/shell_modules/execution_management.py` — `collect()` signature, helpers, docstrings.
- `CelebiChrono/interface/chern_shell/commands_basic.py` / `commands.py` — `do_collect` arg parsing.
- `CelebiChrono/interface/chern_shell/commands_environment.py` — `do_book_reana` `--upload` parsing.
- `CelebiChrono/interface/shell_modules/reana_booking.py` — `upload` param + form data.
- `CelebiChrono/celebi_cli/commands/execution_management.py` — `collect` CLI selector.
- `CelebiChrono/celebi_cli/commands/booking.py`, `CelebiChrono/main.py` — `--upload` option (deprecate `--stageout`).

### Yuki (server)
- `Yuki/kernel/file_types.py` — **new**, classification + predicate builder.
- `Yuki/kernel/reana_workflow.py` — `list_runner_files`, `download_selected`; idempotent downloads + marker semantics.
- `Yuki/kernel/native_workflow.py` — `list_runner_files`, `download_selected` (extend `_collect_artifacts`).
- `Yuki/kernel/file_staging.py` — idempotent / selective stage-out for native.
- `Yuki/kernel/impression_storage.py` — `collect` (light = plots+logs), `collect_files`, `file_status` helper; keep `collect_outputs`/`collect_logs`.
- `Yuki/server/routes/workflow.py` — repurpose `/collect`; add `/collect-files`.
- `Yuki/server/routes/execution.py` (or `status.py`) — add `/file-status`.
- `Yuki/server/routes/status.py` — use `file_types` instead of inline image lists.
- `Yuki/server/routes/booking.py` — read `upload` form param.
- `Yuki/kernel/reana_booker.py` — `book_project(upload_mode)`, `_upload_stageout_files(predicate)`, upload `logs/`.

## Testing

### Celebi `UnitTest/`
- `collect` selector parsing maps to the right communicator calls (default → `collect`; `all` → `collect_outputs`+`collect_logs`; `plots`/`data` → `collect_files` with type; glob/name → `collect_files` with pattern/names).
- `printed_status` renders the stageout table from a mocked `/file-status` response, including the runner-unavailable note.
- `book_reana` sends the `upload` form field (default `plots+logs`); `--stageout` alias maps to `all`.

### Yuki `UnitTest/`
- `file_types.classify` / `is_plot` / `make_predicate` (type keywords, glob, name list).
- `download_selected` for REANA (mock `list_files`/`download_file`) and native (temp dirs): downloads only matching files, skips files already in Storage, does not write the full-set marker.
- `/collect-files` route builds the predicate and invokes download; `/collect` does plots+logs.
- `/file-status` merges runner + Storage entries with correct `in_runner`/`in_yuki`/`type`; falls back when runner unavailable.
- Booking: `_upload_stageout_files` honors the predicate (plots+logs default excludes data; `all` includes it) and uploads logs.

## Open questions / future work

- Make the plot extension set user-configurable.
- Per-file size formatting / human-readable units in the status table.
- Optionally extend the bulk transfer routes (`export/import-imp-stageout`) with the same type filtering.
