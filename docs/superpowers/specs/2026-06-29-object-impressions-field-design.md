# Object-level `impressions` history field

**Date:** 2026-06-29
**Status:** Approved design, pending implementation plan
**Repos affected:** `Celebi` (`CelebiChrono`)

## Problem

Celebi tracks an object’s current impression via the `impression` field in `.celebi/config.local.json`, and each impression stores its own lineage in the per-impression `parents` field. However, there is no object-level record of *all* impression versions that have existed for that object. The object-level `impressions` (plural) field exists in the config schema but is only reset to `[]` by `clean_impressions()` and is otherwise unused.

## Goals

1. Populate the object-level `impressions` list in `.celebi/config.local.json` every time `impress()` succeeds.
2. Each entry records enough metadata to identify the impression later: UUID, timestamp, and descriptor.
3. Keep the existing per-impression `parents` field intact so `history()` continues to work without changes.
4. Make the list easy for future commands to consume (e.g. `list-impressions`, provenance queries, a future `history()` rewrite).

## Non-goals

- No new CLI or API surface is added now; the list is write-only until a future feature needs it.
- No automatic backfill of existing projects. Objects start recording history on their next `impress()`.
- No replacement of the per-impression `parents` field.
- No changes to impression storage backends (legacy directories or CAS refs).

## Background: current architecture (verified during exploration)

- `VObject` core (`CelebiChrono/kernel/vobj_core.py:32`) uses a `TwoTierConfigFile` pointing at `.celebi/config.json`. Writes via `write_variable()` go to `.celebi/config.local.json`.
- `ImpressionManagement.impress()` (`CelebiChrono/kernel/vobj_impression.py:25`) creates a new `VImpression`, calls `update_uuid()` and `create()`, then writes the current impression UUID to the object config (`config_file.write_variable("impression", impression.uuid)`).
- `VImpression.create()` (`CelebiChrono/kernel/vimpression.py:272`) writes impression metadata (`object_type`, `tree`, `dependencies`, `current_path`, `alias_to_impression`, `parents`, `storage_backend`, `root_tree`) to the impression’s own `.celebi/impressions/<uuid>/config.json` and to the CAS ref at `.celebi/impressions_store/refs/impressions/<uuid>.json`.
- `VImpression.parents()` reads the `parents` list from impression metadata. `ImpressionManagement.history()` (`vobj_impression.py:640`) uses this chain to print the object’s impression history.
- `ImpressionManagement.clean_impressions()` (`vobj_impression.py:184`) currently resets `impressions` to `[]`, along with `impression`, `output_md5s`, and `output_md5`.
- `VImpression.get_descriptor()` (`vimpression.py:213`) returns a human-readable descriptor from the impression contents (`celebi.yaml`) or falls back to the basename of `current_path`.

## Design

### Section 1 — Schema

The object-level `impressions` field lives in `.celebi/config.local.json`. It is a JSON list of entries, stored chronologically (oldest first, newest last):

```json
[
  {
    "uuid": "a7b794cfffdcdf3e5f4fdb2fbd517d06",
    "timestamp": "2026-06-29T12:34:56.789012+00:00",
    "descriptor": "fit task v3"
  }
]
```

- `uuid` — impression UUID string.
- `timestamp` — UTC ISO-8601 string with timezone offset, generated when `impress()` succeeds.
- `descriptor` — value returned by `VImpression.get_descriptor()` for that impression.

### Section 2 — Write behavior

A new private helper `_record_impression_history(impression)` is added to `ImpressionManagement` in `CelebiChrono/kernel/vobj_impression.py`.

It is called from `impress()` immediately after `impression.create(self)` succeeds and the current `impression` field has been updated:

```python
impression = VImpression()
impression.update_uuid(self)
impression.create(self)
self.config_file.write_variable("impression", impression.uuid)
self._record_impression_history(impression)
```

The helper:

1. Reads the existing `impressions` list from `self.config_file.read_variable("impressions", [])`.
2. Normalizes a non-list value to `[]`.
3. Builds an entry `{"uuid": impression.uuid, "timestamp": <iso-8601>, "descriptor": impression.get_descriptor()}`.
4. Appends the entry.
5. Writes the updated list back via `self.config_file.write_variable("impressions", new_list)`.

`clean_impressions()` continues to reset `impressions` to `[]` alongside the existing clears.

### Section 3 — Read behavior / consumers

For this change, no code reads the object-level `impressions` list. The existing `history()` method continues to use the per-impression `parents` chain.

The list is intentionally written for future commands. Future consumers must treat a missing or empty list as “no history recorded yet.”

### Section 4 — Migration / backfill policy

- **No automatic backfill.** Existing projects keep an empty `impressions` list until the next `impress()`.
- **No changes to `ConfigMigrator`.** The field did not exist in the old single-file config format.
- **Forward compatibility:** Future readers must handle missing or empty lists gracefully.

### Section 5 — Error handling

- If `VImpression.get_descriptor()` fails or returns an empty string, store `""` rather than failing `impress()`.
- If the existing `impressions` value is not a list, reset to `[]` before appending.
- Timestamp generation uses `datetime.now(timezone.utc).isoformat()`. Any unexpected failure in history bookkeeping must not block `impress()`.

## Testing

Add unit tests in `UnitTest/test_vobject.py` or a new `UnitTest/test_impression_history.py`:

1. **Basic append:** After `impress()`, the object’s local config contains one `impressions` entry with matching `uuid`, a valid ISO-8601 `timestamp`, and the expected `descriptor`.
2. **Multiple impressions:** After `impress()` twice, the list has two entries in chronological order.
3. **`clean_impressions` resets list:** After `clean_impressions()`, `impressions` is `[]`.
4. **No backfill:** On an existing impressed object, the list remains unchanged if no new `impress()` occurs.
5. **Descriptor fallback:** If descriptor lookup returns empty, the entry stores `""` and `impress()` still succeeds.
6. **Corrupt list recovery:** If `impressions` is set to a non-list value, the next `impress()` resets it to `[]` and appends correctly.

## Files affected

- `CelebiChrono/kernel/vobj_impression.py` — add `_record_impression_history()` and wire it into `impress()`; ensure `clean_impressions()` resets the list.
- `UnitTest/test_vobject.py` (or new `UnitTest/test_impression_history.py`) — add tests.
