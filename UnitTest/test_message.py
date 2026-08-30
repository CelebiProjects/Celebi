"""Tests for the Message class."""
from CelebiChrono.utils.message import Message


def test_colored_joins_lines_with_newlines():
    """Multi-line messages render one line per entry."""
    message = Message()
    message.add("first line")
    message.add("second line", "warning")
    rendered = message.colored()
    assert "first line\n" in rendered
    assert "second line" in rendered


def test_colored_collapses_trailing_newlines():
    """Entries that already end with a newline must not double-space."""
    message = Message()
    message.add("header\n")
    message.add("body\n")
    rendered = message.colored()
    assert "header\nbody" in rendered
    assert "\n\n" not in rendered
