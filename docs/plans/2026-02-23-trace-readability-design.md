# Trace Output Readability Improvements

## Overview
Improve the human readability of the `trace()` method output in the Celebi data analysis management toolkit. The current output uses full UUIDs and Python set notation which is difficult for humans to parse quickly.

## Problem Statement
The `trace()` method in `CelebiChrono/kernel/vobj_impression.py` produces output that is:
1. **Hard to read**: Full UUIDs like `abc123-def456-ghi789` are visually noisy
2. **Uses machine notation**: Python set syntax `{uuid}` and `{(uuid1 -> uuid2)}` is not user-friendly
3. **Lacks context**: UUIDs alone don't indicate what type of object they represent (task, algorithm, data, project)
4. **Inconsistent formatting**: Different sections have varying formatting styles

## Design Goals
1. **Human-readable output**: Optimize for CLI/shell users reading in terminal
2. **Short identifiers**: Use abbreviated UUIDs (first 7 characters)
3. **Type context**: Add object type prefixes (`[TASK]`, `[ALGO]`, `[DATA]`, `[PROJ]`)
4. **Consistent formatting**: Use bullet points, clear headers, and consistent spacing
5. **Preserve data**: Keep machine-readable information in Message objects for programmatic use

## Detailed Design

### 1. UUID Formatting
- All UUIDs will use short format: First 7 characters using existing `short_uuid()` method
- Add type prefixes based on object type: `[TASK]`, `[ALGO]`, `[DATA]`, `[PROJ]`
- **Example**: `[TASK] abc123d` instead of `abc123-def456-ghi789`

### 2. Node Differences Section
**Current output:**
```
=== DAG Node Differences ===
Added nodes:   {uuid3}
Removed nodes: {uuid7}
```

**Improved output:**
```
=== DAG Node Differences ===

Added nodes (1):
  • [TASK] abc123d

Removed nodes (1):
  • [ALGO] def456g
```

### 3. Edge Differences Section
**Current output:**
```
=== DAG Edge Differences ===
Added edges:   {(uuid3 -> uuid1)}
Removed edges: {(uuid7 -> uuid2)}
```

**Improved output:**
```
=== DAG Edge Differences ===

Added edges (1):
  • [TASK] abc123d → [DATA] ghi789j

Removed edges (1):
  • [ALGO] def456g → [TASK] klm012n
```

### 4. Detailed Diff Section
**Current output:**
```
=== Detailed Diff (removed parent → added child) ===

--- Change detected: uuid7 → uuid3
```

**Improved output:**
```
=== Detailed Changes (Parent → Child) ===

Change: [ALGO] def456g → [TASK] abc123d
```

### 5. Technical Implementation

#### 5.1 Helper Functions
Create formatting utilities in a new module or add to existing utils:
```python
def format_uuid_short(uuid: str) -> str:
    """Return first 7 characters of UUID."""
    return uuid[:7] if uuid else ""

def format_node_display(uuid: str, obj_type: str = "") -> str:
    """Format node with type prefix and short UUID."""
    short = format_uuid_short(uuid)
    type_prefix = f"[{obj_type.upper()}] " if obj_type else ""
    return f"{type_prefix}{short}"

def format_edge_display(parent_uuid: str, child_uuid: str,
                       parent_type: str = "", child_type: str = "") -> str:
    """Format edge as parent → child with type prefixes."""
    parent_fmt = format_node_display(parent_uuid, parent_type)
    child_fmt = format_node_display(child_uuid, child_type)
    return f"{parent_fmt} → {child_fmt}"
```

#### 5.2 Object Type Detection
Need to determine if we can get object type from UUID/impression:
- Check if `VImpression` stores object type information
- If not, may need to read impression metadata or config.json
- Consider adding `get_object_type(uuid)` helper

#### 5.3 Trace Method Updates
Update `trace()` method in `vobj_impression.py`:
1. Replace direct UUID printing with formatted displays
2. Use bullet points (`•`) instead of set notation
3. Add counts for added/removed items
4. Maintain consistent section headers and spacing

#### 5.4 Backward Compatibility
- Keep machine-readable data in Message objects
- Consider adding `--verbose` flag for full UUIDs
- Ensure existing scripts can still parse output if needed

## Implementation Steps
1. **Investigate object type retrieval**: Check how to get type from UUID
2. **Create formatting utilities**: Add helper functions to appropriate module
3. **Update trace() method**: Implement new formatting in vobj_impression.py
4. **Test with sample data**: Verify output looks correct
5. **Update documentation**: Ensure help text reflects new format

## Risks and Mitigations
- **Risk**: Object type may not be retrievable from UUID alone
  - **Mitigation**: Fall back to UUID-only display if type unavailable
- **Risk**: Formatting changes break existing parsing scripts
  - **Mitigation**: Keep machine-readable data in Message object attributes
- **Risk**: Terminal width issues with formatted output
  - **Mitigation**: Use simple formatting that works on standard terminals

## Success Criteria
1. Trace output uses short UUIDs (7 chars) with type prefixes
2. Output uses human-friendly formatting (bullet points, clear headers)
3. All original information is preserved
4. No regression in functionality
5. Output is easier for humans to read and understand

## Approved By
- User approval received on 2026-02-23