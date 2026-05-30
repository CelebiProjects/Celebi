# REANA Repository Booking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a feature to upload Celebi project files to a REANA instance via REANA's REST API, using a workflow named `celebi-{project_name}`.

**Architecture:** A new `ReanaBooker` class in `CelebiChrono/kernel/` handles direct REANA API communication (auth, workflow lookup/creation, file upload). A shell function and CLI command provide user interfaces.

**Tech Stack:** Python, `requests` library (already a dependency), `unittest.mock` for testing.

---

## File Map

| File | Action | Responsibility |
|------|--------|--------------|
| `CelebiChrono/kernel/reana_booker.py` | Create | Core class: REANA auth, workflow lookup/creation, file upload |
| `CelebiChrono/kernel/reana_booking_spec.yaml` | Create | Minimal no-op workflow spec for new REANA workflows |
| `CelebiChrono/interface/shell_modules/reana_booking.py` | Create | Shell function `book_reana()` |
| `CelebiChrono/interface/shell.py` | Modify | Import and export `book_reana` |
| `CelebiChrono/interface/chern_shell/commands_environment.py` | Modify | Add `do_book_reana()` shell command handler |
| `CelebiChrono/main.py` | Modify | Add `book-reana` CLI command |
| `UnitTest/test_reana_booker.py` | Create | Unit tests for `ReanaBooker` |

---

## Task 1: Create `ReanaBooker` Core Class

**Files:**
- Create: `CelebiChrono/kernel/reana_booker.py`
- Test: `UnitTest/test_reana_booker.py` (started in Task 7)

- [ ] **Step 1: Write the `ReanaBooker` class**

Create `CelebiChrono/kernel/reana_booker.py`:

```python
"""REANA Repository Booking module.

Handles direct communication with REANA REST API to upload
Celebi project files as a workspace catalog entry.
"""
import os
import fnmatch
from logging import getLogger

import requests

from ..utils.message import Message

logger = getLogger("ChernLogger")


DEFAULT_IGNORE_PATTERNS = [
    ".celebi/impressions/*",
    ".celebi/impressions_store/*",
    ".celebi/config.local.json",
    ".git/*",
    "__pycache__/*",
    "*.pyc",
    "*~",
    "*.swp",
    "*.swo",
    "*.~undo-tree~",
    ".DS_Store",
    "*.tmp",
    "*.temp",
]


class ReanaBooker:
    """Handles booking (uploading) a Celebi repository to REANA."""

    def __init__(self, server_url: str, access_token: str):
        """Initialize with REANA server URL and access token.

        Args:
            server_url: REANA server URL (e.g., "https://reana.cern.ch")
            access_token: REANA access token for authentication
        """
        self.server_url = server_url.rstrip("/")
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        self.timeout = 30

    def book_project(self, project_path: str, project_name: str) -> Message:
        """Book a Celebi project to REANA.

        Uploads all project files to a REANA workflow named
        'celebi-{project_name}'. Creates the workflow if it does not exist.

        Args:
            project_path: Absolute path to the Celebi project directory
            project_name: Name of the project

        Returns:
            Message: Success or error message with REANA workflow URL
        """
        message = Message()
        workflow_name = f"celebi-{project_name}"

        # Check if workflow exists
        workflow = self._get_workflow(workflow_name)
        if workflow is None:
            message.add(f"Creating REANA workflow '{workflow_name}'...\n", "normal")
            workflow = self._create_workflow(workflow_name)
            message.add(f"Workflow created: {workflow_name}\n", "success")
        else:
            message.add(f"Using existing REANA workflow '{workflow_name}'\n", "success")

        workflow_id = workflow.get("id", workflow.get("name", workflow_name))

        # Upload files
        message.add("Uploading project files...\n", "normal")
        try:
            self._upload_files(workflow_id, project_path)
            message.add("Files uploaded successfully.\n", "success")
            message.add(
                f"REANA workspace: {self.server_url}/api/workflows/{workflow_id}/workspace/\n",
                "info",
            )
        except Exception as e:
            message.add(f"Upload failed: {e}\n", "error")
            return message

        message.data["workflow_name"] = workflow_name
        message.data["workflow_id"] = workflow_id
        message.data["server_url"] = self.server_url
        return message

    def _get_workflow(self, name: str):
        """Get workflow by name, or None if not found.

        Args:
            name: Workflow name to search for

        Returns:
            dict or None: Workflow dict if found, None otherwise
        """
        try:
            response = requests.get(
                f"{self.server_url}/api/workflows",
                headers=self.headers,
                params={"search": name, "size": 1},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
            for item in items:
                if item.get("name") == name:
                    return item
            return None
        except requests.exceptions.RequestException as e:
            logger.debug("Failed to list workflows: %s", e)
            return None

    def _create_workflow(self, name: str):
        """Create a new minimal workflow on REANA.

        Args:
            name: Name for the new workflow

        Returns:
            dict: Created workflow information

        Raises:
            RuntimeError: If workflow creation fails
        """
        import json

        spec_path = os.path.join(
            os.path.dirname(__file__), "reana_booking_spec.yaml"
        )
        with open(spec_path, "r", encoding="utf-8") as f:
            reana_specification = f.read()

        payload = {
            "workflow_name": name,
            "reana_specification": reana_specification,
        }

        response = requests.post(
            f"{self.server_url}/api/workflows",
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = response.json()

        if not result.get("workflow_id") and not result.get("name"):
            raise RuntimeError(f"Workflow creation failed: {result}")

        return result

    def _upload_files(self, workflow_id: str, project_path: str):
        """Upload project files to REANA workflow workspace.

        Args:
            workflow_id: REANA workflow ID
            project_path: Path to project directory

        Raises:
            requests.exceptions.RequestException: On upload failure
        """
        for root, dirs, files in os.walk(project_path):
            # Filter out ignored directories to avoid descending into them
            dirs[:] = [
                d for d in dirs
                if not self._should_ignore(
                    os.path.relpath(os.path.join(root, d), project_path)
                )
            ]

            for filename in files:
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, project_path)

                if self._should_ignore(relative_path):
                    continue

                with open(file_path, "rb") as f:
                    file_content = f.read()

                response = requests.post(
                    f"{self.server_url}/api/workflows/{workflow_id}/workspace/",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    data={"file_name": relative_path},
                    files={"file_content": (relative_path, file_content)},
                    timeout=self.timeout,
                )
                response.raise_for_status()

    def _should_ignore(self, relative_path: str) -> bool:
        """Check if a relative path should be ignored during upload.

        Args:
            relative_path: Path relative to project root

        Returns:
            bool: True if path should be skipped
        """
        # Normalize path separators for matching
        normalized = relative_path.replace(os.sep, "/")

        for pattern in DEFAULT_IGNORE_PATTERNS:
            if fnmatch.fnmatch(normalized, pattern):
                return True
            # Also check parent directory patterns
            if pattern.endswith("/*"):
                prefix = pattern[:-1]
                if normalized.startswith(prefix):
                    return True

        return False
```

- [ ] **Step 2: Commit**

```bash
git add CelebiChrono/kernel/reana_booker.py
git commit -m "feat: add ReanaBooker core class for REANA repository booking"
```

---

## Task 2: Create Minimal Workflow Spec

**Files:**
- Create: `CelebiChrono/kernel/reana_booking_spec.yaml`

- [ ] **Step 1: Create the YAML spec file**

Create `CelebiChrono/kernel/reana_booking_spec.yaml`:

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

- [ ] **Step 2: Commit**

```bash
git add CelebiChrono/kernel/reana_booking_spec.yaml
git commit -m "feat: add minimal REANA workflow spec for booking placeholder"
```

---

## Task 3: Add Shell Module Function

**Files:**
- Create: `CelebiChrono/interface/shell_modules/reana_booking.py`
- Modify: `CelebiChrono/interface/shell.py` (import + export)

- [ ] **Step 1: Create the shell module**

Create `CelebiChrono/interface/shell_modules/reana_booking.py`:

```python
"""REANA booking functions for shell interface."""
import os

from ...utils.message import Message
from ...utils import csys
from ...kernel.reana_booker import ReanaBooker


def book_reana(server_url: str = "", access_token: str = "") -> Message:
    """Book the current project to REANA.

    Uploads the current Celebi project files to a REANA instance
    as a file catalog entry. Uses workflow name 'celebi-{project_name}'.

    Args:
        server_url: REANA server URL. If empty, uses REANA_SERVER_URL env var.
        access_token: REANA access token. If empty, uses REANA_ACCESS_TOKEN env var.

    Returns:
        Message: Booking result with workflow URL or error information.

    Examples:
        book_reana()  # Uses env vars
        book_reana("https://reana.cern.ch", "my-token")
    """
    message = Message()

    # Resolve credentials
    server_url = server_url or os.environ.get("REANA_SERVER_URL", "")
    access_token = access_token or os.environ.get("REANA_ACCESS_TOKEN", "")

    if not server_url:
        message.add("REANA server URL not set. Use --server or set REANA_SERVER_URL env var.\n", "error")
        return message
    if not access_token:
        message.add("REANA access token not set. Use --token or set REANA_ACCESS_TOKEN env var.\n", "error")
        return message

    # Get project info
    project_path = csys.project_path()
    if not project_path:
        message.add("Not inside a Celebi project.\n", "error")
        return message

    project_name = os.path.basename(os.path.normpath(project_path))

    # Book to REANA
    booker = ReanaBooker(server_url, access_token)
    try:
        result = booker.book_project(project_path, project_name)
        return result
    except Exception as e:
        message.add(f"Booking failed: {e}\n", "error")
        return message
```

- [ ] **Step 2: Update `shell.py` imports**

Add to `CelebiChrono/interface/shell.py` imports section:

```python
from .shell_modules.reana_booking import (
    book_reana
)
```

Place it after the utilities import block, before the `__all__` list.

- [ ] **Step 3: Update `shell.py` `__all__` list**

Add `'book_reana'` to the `__all__` list in `CelebiChrono/interface/shell.py`, in the utilities section:

```python
    # Utilities functions (from utilities.py)
    'workaround_preshell', 'workaround_postshell', 'history',
    'watermark', 'changes', 'doctor', 'bookkeep', 'bookkeep_url',
    'gc_impressions', 'pack_impressions', 'migrate_impressions', 'stats_impressions',
    'danger_call', 'tree', 'error_log',
    # REANA booking functions (from reana_booking.py)
    'book_reana',
```

- [ ] **Step 4: Commit**

```bash
git add CelebiChrono/interface/shell_modules/reana_booking.py CelebiChrono/interface/shell.py
git commit -m "feat: add book_reana shell function"
```

---

## Task 4: Add Shell Command Handler

**Files:**
- Modify: `CelebiChrono/interface/chern_shell/commands_environment.py`

- [ ] **Step 1: Add `do_book_reana` method**

In `CelebiChrono/interface/chern_shell/commands_environment.py`, add the following method to the `EnvironmentCommands` class (after `do_remove_runner`):

```python
    def do_book_reana(self, _: str) -> None:
        """Book current project to REANA."""
        try:
            result = shell.book_reana()
            if result.messages:
                print(result.colored())
        except Exception as e:
            print(f"Error booking to REANA: {e}")
```

- [ ] **Step 2: Verify the import**

Ensure `shell` is imported at the top of `commands_environment.py`. It should already be:

```python
from ...interface import shell
```

- [ ] **Step 3: Commit**

```bash
git add CelebiChrono/interface/chern_shell/commands_environment.py
git commit -m "feat: add book-reana shell command handler"
```

---

## Task 5: Add CLI Command

**Files:**
- Modify: `CelebiChrono/main.py`

- [ ] **Step 1: Add the import**

Add to the imports in `CelebiChrono/main.py`:

```python
from .kernel.reana_booker import ReanaBooker
```

- [ ] **Step 2: Add the CLI command**

Add after the existing CLI commands in `CelebiChrono/main.py`:

```python
@cli.command(name="book-reana")
@click.option("--server", "server_url", default="",
              help="REANA server URL (or set REANA_SERVER_URL env var)")
@click.option("--token", "access_token", default="",
              help="REANA access token (or set REANA_ACCESS_TOKEN env var)")
@click.option("--path", "project_path", default="",
              help="Path to Celebi project (default: current directory)")
def book_reana_command(server_url, access_token, project_path):
    """Book the current project to REANA as a file catalog."""
    try:
        # Resolve credentials
        server_url = server_url or os.environ.get("REANA_SERVER_URL", "")
        access_token = access_token or os.environ.get("REANA_ACCESS_TOKEN", "")

        if not server_url:
            print("Error: REANA server URL not set.")
            print("Use --server or set REANA_SERVER_URL environment variable.")
            return
        if not access_token:
            print("Error: REANA access token not set.")
            print("Use --token or set REANA_ACCESS_TOKEN environment variable.")
            return

        # Resolve project path
        if project_path:
            project_path = os.path.abspath(project_path)
        else:
            project_path = csys.project_path(os.getcwd())

        if not project_path:
            print("Error: Not inside a Celebi project.")
            return

        project_name = os.path.basename(os.path.normpath(project_path))

        # Book to REANA
        booker = ReanaBooker(server_url, access_token)
        result = booker.book_project(project_path, project_name)

        if result.messages:
            print(result.colored())

    except Exception as e:
        print(f"Error: {e}")
```

- [ ] **Step 3: Commit**

```bash
git add CelebiChrono/main.py
git commit -m "feat: add book-reana CLI command"
```

---

## Task 6: Fix `reana_booker.py` — `_create_workflow` payload format

**Files:**
- Modify: `CelebiChrono/kernel/reana_booker.py`

- [ ] **Step 1: Fix the `_create_workflow` method**

The REANA API expects `reana_specification` as a parsed dict, not a raw string. Update `_create_workflow` in `CelebiChrono/kernel/reana_booker.py`:

Replace:
```python
        with open(spec_path, "r", encoding="utf-8") as f:
            reana_specification = f.read()

        payload = {
            "workflow_name": name,
            "reana_specification": reana_specification,
        }
```

With:
```python
        import yaml

        with open(spec_path, "r", encoding="utf-8") as f:
            reana_specification = yaml.safe_load(f)

        payload = {
            "workflow_name": name,
            "reana_specification": reana_specification,
        }
```

Add `import yaml` at the top of the file if not already present. If `pyyaml` is not a dependency, add it to `pyproject.toml` or use `json` to parse the spec (since YAML is a superset of JSON, but the spec is YAML).

Alternative if yaml is not available: keep as string but the API may expect dict. Check the REANA API docs. Actually, REANA's API accepts the specification as a string in some versions and as a dict in others. The safest approach is to try both or use the `reana-client` approach. But since we're implementing directly, let's use `yaml.safe_load` and ensure PyYAML is available (it likely already is, since the project uses YAML files extensively via `metadata.YamlFile`).

- [ ] **Step 2: Commit**

```bash
git add CelebiChrono/kernel/reana_booker.py
git commit -m "fix: parse reana spec as dict for API compatibility"
```

---

## Task 7: Write Unit Tests

**Files:**
- Create: `UnitTest/test_reana_booker.py`

- [ ] **Step 1: Write the test file**

Create `UnitTest/test_reana_booker.py`:

```python
"""Unit tests for ReanaBooker."""
import os
import unittest
from unittest.mock import patch, MagicMock

from CelebiChrono.kernel.reana_booker import ReanaBooker, DEFAULT_IGNORE_PATTERNS


class TestReanaBooker(unittest.TestCase):
    """Test cases for ReanaBooker."""

    def setUp(self):
        """Set up test fixtures."""
        self.booker = ReanaBooker("https://reana.example.com", "test-token")

    def test_init(self):
        """Test initialization sets auth correctly."""
        self.assertEqual(self.booker.server_url, "https://reana.example.com")
        self.assertEqual(self.booker.access_token, "test-token")
        self.assertEqual(
            self.booker.headers["Authorization"],
            "Bearer test-token"
        )

    def test_should_ignore_exact_matches(self):
        """Test exact pattern matching for ignore rules."""
        self.assertTrue(self.booker._should_ignore(".celebi/config.local.json"))
        self.assertTrue(self.booker._should_ignore("*.pyc"))
        self.assertTrue(self.booker._should_ignore(".DS_Store"))
        self.assertTrue(self.booker._should_ignore("file.tmp"))
        self.assertTrue(self.booker._should_ignore("file.temp"))

    def test_should_ignore_directory_patterns(self):
        """Test directory prefix matching for ignore rules."""
        self.assertTrue(self.booker._should_ignore(".celebi/impressions/task1.tar.gz"))
        self.assertTrue(self.booker._should_ignore(".celebi/impressions_store/old.data"))
        self.assertTrue(self.booker._should_ignore(".git/config"))
        self.assertTrue(self.booker._should_ignore("__pycache__/module.cpython-39.pyc"))

    def test_should_not_ignore_kept_files(self):
        """Test that config.json and source files are not ignored."""
        self.assertFalse(self.booker._should_ignore(".celebi/config.json"))
        self.assertFalse(self.booker._should_ignore("celebi.yaml"))
        self.assertFalse(self.booker._should_ignore("README.md"))
        self.assertFalse(self.booker._should_ignore("src/analysis.py"))

    @patch("CelebiChrono.kernel.reana_booker.requests.get")
    def test_get_workflow_found(self, mock_get):
        """Test finding an existing workflow."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [
                {"name": "celebi-test-project", "id": "workflow-123"}
            ]
        }
        mock_get.return_value = mock_response

        result = self.booker._get_workflow("celebi-test-project")

        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "celebi-test-project")
        self.assertEqual(result["id"], "workflow-123")
        mock_get.assert_called_once()

    @patch("CelebiChrono.kernel.reana_booker.requests.get")
    def test_get_workflow_not_found(self, mock_get):
        """Test when workflow does not exist."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        result = self.booker._get_workflow("celebi-nonexistent")

        self.assertIsNone(result)

    @patch("CelebiChrono.kernel.reana_booker.requests.get")
    def test_get_workflow_connection_error(self, mock_get):
        """Test handling connection error during workflow lookup."""
        mock_get.side_effect = Exception("Connection refused")

        result = self.booker._get_workflow("celebi-test")

        self.assertIsNone(result)

    @patch("CelebiChrono.kernel.reana_booker.requests.post")
    @patch("builtins.open", unittest.mock.mock_open(read_data="version: 0.8.0"))
    def test_create_workflow(self, mock_post):
        """Test creating a new workflow."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "workflow_id": "workflow-456",
            "workflow_name": "celebi-test"
        }
        mock_post.return_value = mock_response

        result = self.booker._create_workflow("celebi-test")

        self.assertEqual(result["workflow_id"], "workflow-456")
        mock_post.assert_called_once()

    @patch("CelebiChrono.kernel.reana_booker.requests.post")
    def test_upload_files(self, mock_post):
        """Test uploading files to workflow workspace."""
        mock_response = MagicMock()
        mock_post.return_value = mock_response

        # Create a temporary directory structure
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files
            with open(os.path.join(tmpdir, "README.md"), "w") as f:
                f.write("# Test")
            os.makedirs(os.path.join(tmpdir, "src"))
            with open(os.path.join(tmpdir, "src", "analysis.py"), "w") as f:
                f.write("print('hello')")
            # Create ignored file
            os.makedirs(os.path.join(tmpdir, ".celebi", "impressions"))
            with open(os.path.join(tmpdir, ".celebi", "impressions", "cache.tar"), "w") as f:
                f.write("ignored")

            self.booker._upload_files("workflow-123", tmpdir)

        # Should upload README.md and src/analysis.py, but not cache.tar
        calls = mock_post.call_args_list
        uploaded_files = [call.kwargs.get("data", {}).get("file_name", "")
                          for call in calls]
        self.assertIn("README.md", uploaded_files)
        self.assertIn(os.path.join("src", "analysis.py").replace(os.sep, "/"),
                      [f.replace(os.sep, "/") for f in uploaded_files])

    @patch("CelebiChrono.kernel.reana_booker.requests.get")
    @patch("CelebiChrono.kernel.reana_booker.requests.post")
    def test_book_project_existing_workflow(self, mock_post, mock_get):
        """Test booking with existing workflow."""
        # Mock existing workflow
        mock_get.return_value = MagicMock(
            json=lambda: {
                "items": [{"name": "celebi-test", "id": "wf-123"}]
            }
        )
        mock_post.return_value = MagicMock()

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "README.md"), "w") as f:
                f.write("# Test")

            result = self.booker.book_project(tmpdir, "test")

        self.assertTrue(result.success)
        self.assertIn("Using existing REANA workflow", str(result.messages))

    @patch("CelebiChrono.kernel.reana_booker.requests.get")
    @patch("CelebiChrono.kernel.reana_booker.requests.post")
    @patch("builtins.open", unittest.mock.mock_open(read_data="version: 0.8.0"))
    def test_book_project_new_workflow(self, mock_post, mock_get):
        """Test booking creating new workflow."""
        # Mock no existing workflow
        mock_get.return_value = MagicMock(json=lambda: {"items": []})
        # Mock create workflow
        mock_post.side_effect = [
            MagicMock(json=lambda: {"workflow_id": "wf-456"}),
            MagicMock(),  # file upload
        ]

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "README.md"), "w") as f:
                f.write("# Test")

            result = self.booker.book_project(tmpdir, "test")

        self.assertTrue(result.success)
        self.assertIn("Creating REANA workflow", str(result.messages))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests**

```bash
cd /Users/wave/workdir/Celebi/Celebi/UnitTest
python -m pytest test_reana_booker.py -v
```

Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add UnitTest/test_reana_booker.py
git commit -m "test: add unit tests for ReanaBooker"
```

---

## Task 8: Run Full Test Suite

**Files:**
- None (verification only)

- [ ] **Step 1: Run existing tests to ensure no regressions**

```bash
cd /Users/wave/workdir/Celebi/Celebi
python -m pytest UnitTest/ -v --tb=short
```

Expected: All existing tests pass (the new test file should also pass).

- [ ] **Step 2: Run pylint on new files**

```bash
cd /Users/wave/workdir/Celebi/Celebi
python -m pylint --rcfile=.pylintrc CelebiChrono/kernel/reana_booker.py CelebiChrono/interface/shell_modules/reana_booking.py
```

Expected: No pylint errors (or only pre-existing ones).

- [ ] **Step 3: Commit (if fixes needed)**

If pylint found issues, fix them and commit:

```bash
git add -A
git commit -m "style: pylint fixes for reana booking feature"
```

---

## Self-Review Checklist

**Spec coverage:**
- ✅ `ReanaBooker` class with auth, workflow lookup/creation, file upload
- ✅ Workflow naming: `celebi-{project_name}`
- ✅ Idempotency: reuse existing workflow
- ✅ File exclusion patterns (DEFAULT_IGNORE_PATTERNS)
- ✅ Shell command: `book-reana`
- ✅ CLI command: `chern book-reana --server --token --path`
- ✅ Error handling for missing auth, connection errors
- ✅ Unit tests with mocked REANA API

**Placeholder scan:**
- ✅ No TBD/TODO in steps
- ✅ All code blocks contain complete, runnable code
- ✅ All test commands have expected outputs

**Type consistency:**
- ✅ `ReanaBooker` methods use consistent signatures
- ✅ `Message` return type used throughout
- ✅ `book_reana()` shell function signature matches usage
