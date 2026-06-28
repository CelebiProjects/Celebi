# Object-level impressions history field Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Populate the object-level `impressions` list in `.celebi/config.local.json` with rich metadata on every successful `impress()`.

**Architecture:** Add a private helper to `ImpressionManagement` that builds an entry `{uuid, timestamp, descriptor}` and appends it to the existing local-config list; call it from `impress()` after the current impression UUID is updated. Keep the per-impression `parents` field untouched.

**Tech Stack:** Python 3, `datetime.datetime`, existing `TwoTierConfigFile` / `ConfigFile`, `unittest`

## Global Constraints

- Store the list in `.celebi/config.local.json`.
- Each entry contains `uuid`, `timestamp` (UTC ISO-8601 with timezone offset), and `descriptor`.
- Do not replace the per-impression `parents` field.
- No backfill; only record going forward.
- `clean_impressions()` resets the list to `[]`.
- History bookkeeping must never block `impress()`.

---

## File structure

- `CelebiChrono/kernel/vobj_impression.py` — add `_record_impression_history()` and wire it into `impress()`.
- `UnitTest/test_impression_history.py` — new focused test file covering basic recording, multiple impressions, clean reset, and corrupt-list recovery.

---

### Task 1: Implement `_record_impression_history` and basic recording

**Files:**
- Modify: `CelebiChrono/kernel/vobj_impression.py`
- Create: `UnitTest/test_impression_history.py`

**Interfaces:**
- Consumes: `VImpression` object with `.uuid` and `.get_descriptor()` methods.
- Produces: `ImpressionManagement._record_impression_history(impression)` private method.

- [ ] **Step 1: Write the failing test**

Create `UnitTest/test_impression_history.py`:

```python
"""Tests for the object-level impression history list."""
import os
import unittest
from datetime import datetime
from colored import Fore, Style
import CelebiChrono.kernel.vobject as vobj
from CelebiChrono.kernel.chern_cache import ChernCache
from CelebiChrono.utils import metadata
import prepare

CHERN_CACHE = ChernCache.instance()


class TestImpressionHistory(unittest.TestCase):
    """Test object-level impressions history recording."""

    def setUp(self):
        self.cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.cwd)

    def test_impress_records_history_entry(self):
        """A successful impress appends one entry to the local impressions list."""
        print(Fore.BLUE + "Testing impression history recording..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        try:
            obj_fitTask = vobj.VObject("FitTask")
            obj_fitTask.impress()

            local_config = metadata.ConfigFile(
                os.path.join(obj_fitTask.path, ".celebi", "config.local.json")
            )
            history = local_config.read_variable("impressions", [])
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["uuid"], str(obj_fitTask.impression()))

            # Timestamp is ISO-8601 with timezone offset and is parseable.
            ts = history[0]["timestamp"]
            parsed = datetime.fromisoformat(ts)
            self.assertIsNotNone(parsed.tzinfo)

            # Descriptor is non-empty (demo project falls back to object name).
            self.assertTrue(history[0]["descriptor"])
        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_genfit_new")
            CHERN_CACHE.__init__()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd UnitTest
python -m pytest test_impression_history.py::TestImpressionHistory::test_impress_records_history_entry -v
```

Expected: FAIL — `impressions` list is empty because `_record_impression_history` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Modify `CelebiChrono/kernel/vobj_impression.py`.

Add import near the top of the file (with the other imports):

```python
from datetime import datetime, timezone
```

Add a private method to `ImpressionManagement`:

```python
    def _record_impression_history(self, impression):
        """Append a record of the given impression to the object-level history list.

        The record is written to the object's local config (.celebi/config.local.json).
        Failures are logged and swallowed so that history bookkeeping never blocks
        impress().

        Args:
            impression: VImpression object that was just created.
        """
        try:
            descriptor = impression.get_descriptor()
        except Exception:  # pylint: disable=broad-except
            descriptor = ""

        try:
            timestamp = datetime.now(timezone.utc).isoformat()
        except Exception:  # pylint: disable=broad-except
            timestamp = ""

        try:
            history = self.config_file.read_variable("impressions", [])
            if not isinstance(history, list):
                history = []
            history.append({
                "uuid": impression.uuid,
                "timestamp": timestamp,
                "descriptor": descriptor,
            })
            self.config_file.write_variable("impressions", history)
        except Exception:  # pylint: disable=broad-except
            logger.debug(
                "Failed to record impression history for %s",
                impression.uuid,
                exc_info=True,
            )
```

In `impress()`, locate the line:

```python
self.config_file.write_variable("impression", impression.uuid)
```

Add immediately after it:

```python
self._record_impression_history(impression)
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd UnitTest
python -m pytest test_impression_history.py::TestImpressionHistory::test_impress_records_history_entry -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add CelebiChrono/kernel/vobj_impression.py UnitTest/test_impression_history.py
git commit -m "feat: record object-level impression history on impress

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Edge-case tests for history list

**Files:**
- Modify: `UnitTest/test_impression_history.py`

**Interfaces:**
- Consumes: `ImpressionManagement._record_impression_history()` behavior from Task 1.
- Produces: passing edge-case tests.

- [ ] **Step 1: Write the failing tests**

Append to `UnitTest/test_impression_history.py` inside `TestImpressionHistory`:

```python
    def test_multiple_impresses_append_chronologically(self):
        """Each impress appends a new entry; entries are ordered oldest-first."""
        print(Fore.BLUE + "Testing multiple impression history entries..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        try:
            obj_fitTask = vobj.VObject("FitTask")
            obj_fitTask.impress()
            first_uuid = str(obj_fitTask.impression())

            # Change the task so the next impress produces a different UUID.
            celebi_yaml = os.path.join(obj_fitTask.path, "celebi.yaml")
            with open(celebi_yaml, "a", encoding="utf-8") as f:
                f.write("# touch\n")

            obj_fitTask.impress()
            second_uuid = str(obj_fitTask.impression())
            self.assertNotEqual(first_uuid, second_uuid)

            local_config = metadata.ConfigFile(
                os.path.join(obj_fitTask.path, ".celebi", "config.local.json")
            )
            history = local_config.read_variable("impressions", [])
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0]["uuid"], first_uuid)
            self.assertEqual(history[1]["uuid"], second_uuid)

            self.assertLessEqual(
                datetime.fromisoformat(history[0]["timestamp"]),
                datetime.fromisoformat(history[1]["timestamp"]),
            )
        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_genfit_new")
            CHERN_CACHE.__init__()

    def test_clean_impressions_clears_history(self):
        """clean_impressions resets the object-level impressions list."""
        print(Fore.BLUE + "Testing clean impressions clears history..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        try:
            obj_fitTask = vobj.VObject("FitTask")
            obj_fitTask.impress()
            obj_fitTask.clean_impressions()

            local_config = metadata.ConfigFile(
                os.path.join(obj_fitTask.path, ".celebi", "config.local.json")
            )
            history = local_config.read_variable("impressions", [])
            self.assertEqual(history, [])
        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_genfit_new")
            CHERN_CACHE.__init__()

    def test_corrupt_history_list_is_reset(self):
        """A non-list value in impressions is replaced before appending."""
        print(Fore.BLUE + "Testing corrupt history list recovery..." + Style.RESET)
        prepare.create_chern_project("demo_genfit_new")
        os.chdir("demo_genfit_new")
        try:
            obj_fitTask = vobj.VObject("FitTask")
            local_config = metadata.ConfigFile(
                os.path.join(obj_fitTask.path, ".celebi", "config.local.json")
            )
            local_config.write_variable("impressions", "not-a-list")

            obj_fitTask.impress()
            history = local_config.read_variable("impressions", [])
            self.assertIsInstance(history, list)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["uuid"], str(obj_fitTask.impression()))
        finally:
            os.chdir("..")
            prepare.remove_chern_project("demo_genfit_new")
            CHERN_CACHE.__init__()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd UnitTest
python -m pytest test_impression_history.py -v
```

Expected: FAIL because the new test methods are not yet in the file.

- [ ] **Step 3: Add the tests (no implementation change needed)**

The implementation from Task 1 already handles corrupt lists and clean resets. Add the three test methods to `UnitTest/test_impression_history.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
cd UnitTest
python -m pytest test_impression_history.py -v
```

Expected: PASS (4 tests total).

- [ ] **Step 5: Commit**

```bash
git add UnitTest/test_impression_history.py
git commit -m "test: edge cases for object-level impression history

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Verify full test suite and lint

**Files:**
- None (verification only)

- [ ] **Step 1: Run unit tests**

Run:

```bash
cd UnitTest
python -m pytest -v
```

Expected: All tests pass, including the new ones.

- [ ] **Step 2: Run pylint on modified production file**

Run:

```bash
python -m pylint --rcfile=.pylintrc CelebiChrono/kernel/vobj_impression.py
```

Expected: No new warnings. (If `broad-except` warnings appear, ensure the `# pylint: disable=broad-except` comments are present.)

- [ ] **Step 3: Fix and commit any issues**

If lint or tests fail, fix them and commit:

```bash
git add <files>
git commit -m "fix: address review/lint issues for impression history

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Self-review

### Spec coverage

| Spec requirement | Task that implements it |
|------------------|-------------------------|
| Object-level `impressions` list in `.celebi/config.local.json` | Task 1 |
| Entry schema `{uuid, timestamp, descriptor}` | Task 1 |
| Timestamp is UTC ISO-8601 with timezone offset | Task 1 |
| Populate on every `impress()` | Task 1 |
| Keep per-impression `parents` unchanged | No code changes to `parents`; history() untouched |
| `clean_impressions()` resets list to `[]` | Already implemented; verified in Task 2 |
| No backfill | No migration code added |
| History bookkeeping must not block `impress()` | Task 1 (broad try/except with debug logging) |
| Corrupt non-list value recovery | Task 1 + Task 2 test |

### Placeholder scan

No `TBD`, `TODO`, "implement later", "add appropriate error handling", or "similar to Task N" patterns remain. Every step includes exact file paths, exact code, and exact commands.

### Type consistency

- `_record_impression_history(self, impression)` is a method on `ImpressionManagement`; it is called from `impress()` with the same `impression` variable used elsewhere in that method.
- `impression.uuid` is a string.
- `impression.get_descriptor()` returns a string.
- `history` is always a list of dicts before being written.
- Tests use `datetime.fromisoformat()` to parse the stored timestamp strings.

### Potential issue: re-impressing in the demo project

The `test_multiple_impresses_append_chronologically` test appends a comment to `celebi.yaml` to force a new impression UUID. This changes the file content, which changes the impression hash, and `is_impressed_fast()` will detect the change and allow `impress()` to proceed. The predecessor objects remain impressed, so dependency resolution succeeds.

### Potential issue: descriptor fallback

The demo project's `celebi.yaml` files do not contain a `descriptor` field, so `VImpression.get_descriptor()` falls back to the basename of `current_path` (e.g. `"FitTask"`). The test only asserts that the descriptor is non-empty, which is robust across demo data changes.
