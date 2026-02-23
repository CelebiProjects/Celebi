# Trace Output Readability Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve human readability of trace() method output with short UUIDs, type prefixes, and better formatting.

**Architecture:** Add formatting utilities to format UUIDs with type prefixes, update trace() method to use new formatting, maintain backward compatibility by keeping machine-readable data in Message objects.

**Tech Stack:** Python 3.10+, CelebiChrono codebase, existing Message class system

---

## Investigation Phase

### Task 1: Check current trace output format

**Files:**
- Read: `CelebiChrono/kernel/vobj_impression.py:299-475`

**Step 1: Examine current trace method structure**
Look at the trace() method to understand current output format and identify all print/message.add statements that need updating.

**Step 2: Check VImpression for object_type access**
Verify if VImpression can retrieve object_type from config.json.

**Step 3: Test current output**
Run a simple test to see current trace output format.

---

## Utility Functions Phase

### Task 2: Add object_type getter to VImpression

**Files:**
- Modify: `CelebiChrono/kernel/vimpression.py`
- Test: `UnitTest/test_vimpression.py` (if exists)

**Step 1: Write failing test for object_type() method**
```python
def test_vimpression_object_type():
    # Create mock impression with object_type in config
    impression = VImpression("test-uuid")
    # Mock config_file.read_variable to return "task"
    # Assert impression.object_type() == "task"
```

**Step 2: Run test to verify it fails**
Run: `pytest UnitTest/test_vimpression.py::test_vimpression_object_type -v`
Expected: FAIL with "AttributeError: 'VImpression' object has no attribute 'object_type'"

**Step 3: Add object_type() method to VImpression**
```python
def object_type(self) -> str:
    """Get the object type stored in the impression."""
    return self.config_file.read_variable("object_type", "")
```

**Step 4: Run test to verify it passes**
Run: `pytest UnitTest/test_vimpression.py::test_vimpression_object_type -v`
Expected: PASS

**Step 5: Commit**
```bash
git add CelebiChrono/kernel/vimpression.py UnitTest/test_vimpression.py
git commit -m "feat: add object_type() method to VImpression"
```

### Task 3: Create formatting utilities

**Files:**
- Create: `CelebiChrono/utils/format_utils.py`
- Test: `UnitTest/test_format_utils.py`

**Step 1: Write failing tests for formatting utilities**
```python
def test_format_uuid_short():
    assert format_uuid_short("abc123-def456-ghi789") == "abc123d"
    assert format_uuid_short("") == ""
    assert format_uuid_short("short") == "short"

def test_format_node_display():
    assert format_node_display("abc123-def456-ghi789", "task") == "[TASK] abc123d"
    assert format_node_display("def456-ghi789-jkl012", "algorithm") == "[ALGO] def456g"
    assert format_node_display("ghi789-jkl012-mno345", "") == "ghi789j"

def test_format_edge_display():
    assert format_edge_display(
        "abc123-def456-ghi789", "def456-ghi789-jkl012",
        "task", "algorithm"
    ) == "[TASK] abc123d → [ALGO] def456g"
```

**Step 2: Run tests to verify they fail**
Run: `pytest UnitTest/test_format_utils.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'CelebiChrono.utils.format_utils'"

**Step 3: Create format_utils.py with implementations**
```python
"""Formatting utilities for human-readable output."""

def format_uuid_short(uuid: str) -> str:
    """Return first 7 characters of UUID."""
    return uuid[:7] if uuid else ""

def format_node_display(uuid: str, obj_type: str = "") -> str:
    """Format node with type prefix and short UUID."""
    short = format_uuid_short(uuid)
    if obj_type:
        type_prefix = f"[{obj_type.upper()[:4]}] "  # TASK, ALGO, DATA, PROJ
        return f"{type_prefix}{short}"
    return short

def format_edge_display(parent_uuid: str, child_uuid: str,
                       parent_type: str = "", child_type: str = "") -> str:
    """Format edge as parent → child with type prefixes."""
    parent_fmt = format_node_display(parent_uuid, parent_type)
    child_fmt = format_node_display(child_uuid, child_type)
    return f"{parent_fmt} → {child_fmt}"
```

**Step 4: Run tests to verify they pass**
Run: `pytest UnitTest/test_format_utils.py -v`
Expected: PASS

**Step 5: Commit**
```bash
git add CelebiChrono/utils/format_utils.py UnitTest/test_format_utils.py
git commit -m "feat: add formatting utilities for trace output"
```

---

## Trace Method Updates Phase

### Task 4: Update node differences section

**Files:**
- Modify: `CelebiChrono/kernel/vobj_impression.py:380-386`

**Step 1: Examine current node differences code**
```python
message.add("\n=== DAG Node Differences ===", "title0")
message.add(f"Added nodes:   {added_nodes if added_nodes else '{}'}", "diff")
message.add(f"Removed nodes: {removed_nodes if removed_nodes else '{}'}", "diff")
```

**Step 2: Write updated version with formatting**
```python
from ..utils.format_utils import format_node_display

# Format node differences
message.add("\n=== DAG Node Differences ===", "title0")

if added_nodes:
    message.add(f"\nAdded nodes ({len(added_nodes)}):", "info")
    for node in sorted(added_nodes):
        obj_type = VImpression(node).object_type() if node else ""
        message.add(f"  • {format_node_display(node, obj_type)}", "diff")
else:
    message.add("\nAdded nodes: none", "info")

if removed_nodes:
    message.add(f"\nRemoved nodes ({len(removed_nodes)}):", "info")
    for node in sorted(removed_nodes):
        obj_type = VImpression(node).object_type() if node else ""
        message.add(f"  • {format_node_display(node, obj_type)}", "diff")
else:
    message.add("\nRemoved nodes: none", "info")
```

**Step 3: Test the changes**
Run: `python -m py_compile CelebiChrono/kernel/vobj_impression.py`
Expected: No syntax errors

**Step 4: Commit**
```bash
git add CelebiChrono/kernel/vobj_impression.py
git commit -m "feat: update node differences section with human-readable formatting"
```

### Task 5: Update edge differences section

**Files:**
- Modify: `CelebiChrono/kernel/vobj_impression.py:388-394`

**Step 1: Examine current edge differences code**
```python
message.add("\n=== DAG Edge Differences ===", "title0")
message.add(f"Added edges:   {added_edges if added_edges else '{}'}", "diff")
message.add(f"Removed edges: {removed_edges if removed_edges else '{}'}", "diff")
```

**Step 2: Write updated version with formatting**
```python
from ..utils.format_utils import format_edge_display

# Format edge differences
message.add("\n=== DAG Edge Differences ===", "title0")

if added_edges:
    message.add(f"\nAdded edges ({len(added_edges)}):", "info")
    for parent, child in sorted(added_edges):
        parent_type = VImpression(parent).object_type() if parent else ""
        child_type = VImpression(child).object_type() if child else ""
        message.add(f"  • {format_edge_display(parent, child, parent_type, child_type)}", "diff")
else:
    message.add("\nAdded edges: none", "info")

if removed_edges:
    message.add(f"\nRemoved edges ({len(removed_edges)}):", "info")
    for parent, child in sorted(removed_edges):
        parent_type = VImpression(parent).object_type() if parent else ""
        child_type = VImpression(child).object_type() if child else ""
        message.add(f"  • {format_edge_display(parent, child, parent_type, child_type)}", "diff")
else:
    message.add("\nRemoved edges: none", "info")
```

**Step 3: Test the changes**
Run: `python -m py_compile CelebiChrono/kernel/vobj_impression.py`
Expected: No syntax errors

**Step 4: Commit**
```bash
git add CelebiChrono/kernel/vobj_impression.py
git commit -m "feat: update edge differences section with human-readable formatting"
```

### Task 6: Update detailed diff section headers

**Files:**
- Modify: `CelebiChrono/kernel/vobj_impression.py:395-410`

**Step 1: Update section header**
Change from:
```python
message.add("\n=== Detailed Diff (removed parent → added child) ===", "title0")
```
To:
```python
message.add("\n=== Detailed Changes (Parent → Child) ===", "title0")
```

**Step 2: Update change detection message**
Change from:
```python
message.add(f"\n--- Change detected: {r} → {a}", "title1")
```
To:
```python
parent_type = VImpression(r).object_type() if r else ""
child_type = VImpression(a).object_type() if a else ""
message.add(f"\nChange: {format_edge_display(r, a, parent_type, child_type)}", "title1")
```

**Step 3: Test the changes**
Run: `python -m py_compile CelebiChrono/kernel/vobj_impression.py`
Expected: No syntax errors

**Step 4: Commit**
```bash
git add CelebiChrono/kernel/vobj_impression.py
git commit -m "feat: update detailed diff section with human-readable formatting"
```

### Task 7: Update file diff and edge change sections

**Files:**
- Modify: `CelebiChrono/kernel/vobj_impression.py:425-472`

**Step 1: Update file diff headers**
Change from:
```python
message.add(f"  Added files:   {added_files}", "diff")
message.add(f"  Removed files: {removed_files}", "diff")
```
To:
```python
if added_files:
    message.add(f"  Added files ({len(added_files)}):", "info")
    for file in sorted(added_files):
        message.add(f"    • {file}", "diff")
if removed_files:
    message.add(f"  Removed files ({len(removed_files)}):", "info")
    for file in sorted(removed_files):
        message.add(f"    • {file}", "diff")
```

**Step 2: Update edge change messages**
Change from:
```python
message.add(f"  Changed incoming edges to {a}:", "info")
message.add(f"    Added from:   {edge_diff_a if edge_diff_a else '{}'}", "diff")
message.add(f"    Removed from: {edge_diff_r if edge_diff_r else '{}'}", "diff")
```
To:
```python
message.add(f"  Changed incoming edges to {format_node_display(a, child_type)}:", "info")
if edge_diff_a:
    message.add(f"    Added from ({len(edge_diff_a)}):", "info")
    for parent in sorted(edge_diff_a):
        parent_type = VImpression(parent).object_type() if parent else ""
        message.add(f"      • {format_node_display(parent, parent_type)}", "diff")
if edge_diff_r:
    message.add(f"    Removed from ({len(edge_diff_r)}):", "info")
    for parent in sorted(edge_diff_r):
        parent_type = VImpression(parent).object_type() if parent else ""
        message.add(f"      • {format_node_display(parent, parent_type)}", "diff")
```

**Step 3: Test the changes**
Run: `python -m py_compile CelebiChrono/kernel/vobj_impression.py`
Expected: No syntax errors

**Step 4: Commit**
```bash
git add CelebiChrono/kernel/vobj_impression.py
git commit -m "feat: update file diff and edge change sections with human-readable formatting"
```

---

## Cleanup Phase

### Task 8: Remove stray print statements

**Files:**
- Modify: `CelebiChrono/kernel/vobj_impression.py`

**Step 1: Find and remove all print statements in trace()**
Search for lines with `print(` in the trace() method and remove them.

**Step 2: Verify no print statements remain**
Run: `grep -n "print(" CelebiChrono/kernel/vobj_impression.py`
Expected: Only commented print statements or none in trace() method

**Step 3: Test compilation**
Run: `python -m py_compile CelebiChrono/kernel/vobj_impression.py`
Expected: No syntax errors

**Step 4: Commit**
```bash
git add CelebiChrono/kernel/vobj_impression.py
git commit -m "cleanup: remove stray print statements from trace() method"
```

### Task 9: Run comprehensive tests

**Files:**
- Test: All relevant test files

**Step 1: Run unit tests**
Run: `python -m pytest UnitTest/ -v`
Expected: All tests pass (except known failures unrelated to trace)

**Step 2: Test trace method directly**
Create a simple test script to verify trace() returns Message object with new formatting.

**Step 3: Verify imports work**
Run: `python -c "from CelebiChrono.kernel.vobj_impression import ImpressionManagement; from CelebiChrono.utils.format_utils import format_node_display; print('Imports successful')"`
Expected: "Imports successful"

**Step 4: Commit any test updates**
```bash
git add UnitTest/
git commit -m "test: update tests for trace readability improvements"
```

---

## Documentation Phase

### Task 10: Update documentation

**Files:**
- Modify: `CelebiChrono/interface/shell_modules/visualization.py` (docstring)
- Check: `CelebiChrono/celebi_cli/commands/communication.py` (docstring)

**Step 1: Update trace function docstring**
Update the docstring in visualization.py to reflect new output format.

**Step 2: Verify CLI command documentation**
Check if CLI command docstring needs updating.

**Step 3: Commit documentation updates**
```bash
git add CelebiChrono/interface/shell_modules/visualization.py CelebiChrono/celebi_cli/commands/communication.py
git commit -m "docs: update trace command documentation for new output format"
```

---

## Final Verification

### Task 11: Final integration test

**Step 1: Create integration test script**
Create a test that simulates trace output with sample data.

**Step 2: Verify output format**
Check that output matches expected human-readable format.

**Step 3: Run full test suite**
Run: `python -m pytest UnitTest/ -v`
Expected: All tests pass

**Step 4: Final commit**
```bash
git add .
git commit -m "feat: complete trace output readability improvements"
```

---

**Plan complete and saved to `docs/plans/2026-02-23-trace-readability-implementation.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**