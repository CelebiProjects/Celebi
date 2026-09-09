"""Listing notes use the client's timezone, including date and DST changes."""
import os
import time

import pytest

from CelebiChrono.kernel.vtask import VTask


@pytest.mark.parametrize("zone,stamp,expected", [
    ("Asia/Shanghai", "2026-09-07T14:00+00:00", "2026-09-07 22:00 +0800"),
    ("Asia/Shanghai", "2026-09-07T20:00+00:00", "2026-09-08 04:00 +0800"),
    ("America/New_York", "2026-07-07T14:00+00:00", "2026-07-07 10:00 -0400"),
    ("America/New_York", "2026-01-07T14:00+00:00", "2026-01-07 09:00 -0500"),
])
def test_listing_time_uses_client_timezone(zone, stamp, expected):
    if not hasattr(time, "tzset"):
        pytest.skip("tzset unavailable")
    previous = os.environ.get("TZ")
    try:
        os.environ["TZ"] = zone
        time.tzset()
        note = {"listing_time": stamp,
                "message": f"no stageout files on the runner (listing from {stamp})"}
        assert VTask._format_listing_note(note) == (
            f"no stageout files on the runner (listing from {expected})")
    finally:
        if previous is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = previous
        time.tzset()


@pytest.mark.parametrize("stamp", [None, "invalid", "2026-09-07 14:00"])
def test_unusable_timestamp_keeps_message(stamp):
    note = {"message": "legacy note", "listing_time": stamp}
    assert VTask._format_listing_note(note) == "legacy note"
