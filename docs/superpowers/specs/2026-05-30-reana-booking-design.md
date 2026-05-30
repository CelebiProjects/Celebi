# REANA Repository Booking — Design Specification

**Date:** 2026-05-30  
**Status:** Approved  
**Branch:** `feature/reana-booking`

## Overview

Add a feature to Celebi that uploads a project's files to a REANA instance via REANA's REST API. REANA is used as a remote storage/catalog — no workflow execution is triggered. If a workflow named `celebi-{project_name}` already exists in REANA, it is reused.

## Goals

- Upload an entire Celebi project to REANA as a file catalog
- Reuse existing REANA workflows when possible (idempotent)
- Exclude internal/temporary files from the upload
- Support both CLI and interactive shell interfaces

## Non-Goals

- Generate or execute REANA workflows
- Manage REANA workflow runs or statuses
- Replace the existing DITE-server-based runner system

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                      User Interface                      │
│  ┌─────────────┐  ┌──────────────────────────────────┐  │
│  │ CLI:        │  │ Shell:                           │  │
│  │ chern       │  │ book-reana                       │  │
│  │ book-reana  │  │                                  │  │
│  └──────┬──────┘  └────────────────┬─────────────────┘  │
│         │                          │                    │
│         └────────────┬─────────────┘                    │
│                      ▼                                  │
│         ┌─────────────────────┐                         │
│         │   ReanaBooker       │                         │
│         │   (kernel module)   │                         │
│         └──────────┬──────────┘                         │
│                    │                                    │
│                    ▼                                    │
│         REANA REST API (direct, no DITE)                │
└─────────────────────────────────────────────────────────┘
```

### New Files

| File | Purpose |
|------|---------|
| `CelebiChrono/kernel/reana_booker.py` | Core class for REANA API communication |
| `CelebiChrono/kernel/reana_booking_spec.yaml` | Minimal no-op workflow spec for new workflows |
| `CelebiChrono/interface/chern_shell/commands_reana.py` | Shell command handler for `book-reana` |
| `UnitTest/test_reana_booker.py` | Unit tests for ReanaBooker |

### Modified Files

| File | Change |
|------|--------|
| `CelebiChrono/main.py` | Register `book-reana` CLI command |
| `CelebiChrono/interface/shell.py` | Add `book_reana()` shell function |
| `CelebiChrono/interface/chern_shell/commands_environment.py` | (Or new mixin) Wire `book-reana` into shell |
| `CelebiChrono/interface/chern_shell/completions.py` | Add completion for `book-reana` |

---

## Component Design

### `ReanaBooker` Class

```python
class ReanaBooker:
    """Handles direct communication with REANA REST API for repository booking."""

    def __init__(self, server_url: str, access_token: str) -> None
    def book_project(self, project_path: str, project_name: str) -> Message
    def _get_workflow(self, name: str) -> dict | None
    def _create_workflow(self, name: str) -> dict
    def _upload_files(self, workflow_id: str, project_path: str) -> None
    def _should_ignore(self, relative_path: str) -> bool
```

**Authentication:** Bearer token in `Authorization` header.

**API endpoints used:**
- `GET /api/workflows?search={name}` — check if workflow exists
- `POST /api/workflows` — create new workflow
- `POST /api/workflows/{id}/workspace/` — upload files

### Workflow Naming

- Format: `celebi-{project_name}`
- Example: project named `higgs-analysis` → workflow `celebi-higgs-analysis`
- If workflow exists, reuse it (do not create duplicate)

### Minimal Workflow Spec

Used only when creating a new workflow. A no-op serial workflow:

```yaml
version: 0.8.0
inputs:
  files: []
workflow:
  type: serial
  specification:
    steps:
      - name: booking-placeholder
        environment: 'reanahub/reana-env-alpine'
        commands:
          - echo "Celebi booking placeholder"
```

### File Exclusion Rules

Files matching these patterns are skipped during upload:

| Pattern | Reason |
|---------|--------|
| `.celebi/impressions/**` | Cached impression tarballs |
| `.celebi/impressions_store/**` | Stored impressions |
| `.celebi/config.local.json` | Local machine-specific settings |
| `.git/**` | Git internals |
| `__pycache__/**` | Python cache |
| `*.pyc` | Compiled Python |
| `*~` | Emacs backup files |
| `*.swp`, `*.swo` | Vim swap files |
| `*.~undo-tree~` | Emacs undo-tree files |
| `.DS_Store` | macOS metadata |
| `*.tmp`, `*.temp` | Generic temp files |

Additional exclusions can be defined in `.celebi/bookignore` (gitignore-style patterns).

**Note:** `.celebi/config.json` is **kept** — it contains shared project metadata.

---

## Data Flow

```
User runs: chern book-reana
          │
          ▼
┌─────────────────────────────┐
│  Parse CLI args / env vars  │ ──► REANA_SERVER_URL, REANA_ACCESS_TOKEN
└─────────────────────────────┘
          │
          ▼
┌─────────────────────────────┐
│  ReanaBooker.__init__()     │ ──► Auth headers with Bearer token
└─────────────────────────────┘
          │
          ▼
┌─────────────────────────────┐
│  GET /api/workflows         │ ──► Search for celebi-{project_name}
└─────────────────────────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
  Found      Not found
    │            │
    ▼            ▼
  Reuse    POST /api/workflows
 workflow   (minimal spec)
    │            │
    └──────┬─────┘
           ▼
┌─────────────────────────────┐
│  Walk project directory     │ ──► Skip ignored patterns
│  (os.walk with filtering)   │
└─────────────────────────────┘
          │
          ▼
┌─────────────────────────────┐
│  POST /api/workflows/{id}   │ ──► Upload files to workspace
│  /workspace/...             │
└─────────────────────────────┘
          │
          ▼
┌─────────────────────────────┐
│  Return Message with URL    │ ──► Success / error report
└─────────────────────────────┘
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| REANA server unreachable | Error message: "Cannot connect to REANA server at {url}" |
| Invalid access token | 401/403 → Error: "Invalid REANA access token" |
| Workflow exists (name collision) | Reuse existing workflow (idempotent) |
| Upload interrupted | Retry with exponential backoff (3 attempts) |
| File too large for single upload | Warn user, skip file |
| Project not initialized | Error: "No Celebi project found in current directory" |
| Missing auth credentials | Error: "Set REANA_ACCESS_TOKEN or use --token" |

---

## Interface Design

### CLI Command

```bash
# Recommended: environment variables
export REANA_SERVER_URL=https://reana.cern.ch
export REANA_ACCESS_TOKEN=xxxxx
chern book-reana

# Or explicit flags
chern book-reana --server https://reana.cern.ch --token xxxxx

# From a specific directory
chern book-reana --path /path/to/project
```

**Flags:**
| Flag | Default | Description |
|------|---------|-------------|
| `--server` | `REANA_SERVER_URL` env var | REANA server URL |
| `--token` | `REANA_ACCESS_TOKEN` env var | REANA access token |
| `--path` | Current directory | Path to Celebi project |

### Shell Command

Inside the `chern` interactive shell:
```bash
book-reana
```

Uses the current project context (no arguments needed).

---

## Testing Plan

### Unit Tests (`UnitTest/test_reana_booker.py`)

1. **Auth initialization** — verify headers are set correctly
2. **Workflow lookup** — mock `GET /api/workflows` returning existing workflow
3. **Workflow creation** — mock `POST /api/workflows` for new workflow
4. **File exclusion** — verify ignore patterns filter correctly
5. **Upload** — mock file upload endpoint
6. **Retry logic** — simulate upload failure and retry
7. **Error handling** — test each error scenario

### Integration Tests (optional, marked)

- Upload to a local/test REANA instance

---

## Open Questions / Future Work

1. Should we support `.celebi/bookignore` for project-specific exclusions?
2. Should we display upload progress for large projects?
3. Should we support deleting/replacing files in an existing REANA workflow workspace?

---

## References

- REANA REST API docs: https://reana.readthedocs.io/en/latest/reference/http-api.html
- Existing Celebi communicator pattern: `CelebiChrono/kernel/chern_communicator.py`
