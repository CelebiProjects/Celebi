"""Tests for formatting utilities."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from CelebiChrono.utils.format_utils import (
    format_uuid_short,
    format_node_display,
    format_edge_display
)


def test_format_uuid_short():
    """Test formatting UUID to short version."""
    assert format_uuid_short("abc123-def456-ghi789") == "abc123d"
    assert format_uuid_short("") == ""
    assert format_uuid_short("short") == "short"


def test_format_node_display():
    """Test formatting node display with type prefix."""
    assert format_node_display("abc123-def456-ghi789", "task") == "[TASK] abc123d"
    assert format_node_display("def456-ghi789-jkl012", "algorithm") == "[ALGO] def456g"
    assert format_node_display("ghi789-jkl012-mno345", "") == "ghi789j"
    assert format_node_display("abc123-def456-ghi789", "task", "mytask") == "[TASK] abc123d (mytask)"


def test_format_edge_display():
    """Test formatting edge display with arrow."""
    assert format_edge_display(
        "abc123-def456-ghi789", "def456-ghi789-jkl012",
        "task", "algorithm"
    ) == "[TASK] abc123d → [ALGO] def456g"
