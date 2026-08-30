"""Tests for the Message class."""
import re

from CelebiChrono.utils.message import Message


def _clean(rendered):
    """Strip ANSI escape codes from a colored render."""
    return re.sub(r"\x1b\[[0-9;]*m", "", rendered)


def test_colored_entries_carry_their_own_newlines():
    """Entries with trailing newlines render without double-spacing."""
    message = Message()
    message.add("header\n")
    message.add("body\n")
    rendered = _clean(message.colored())
    assert "header\nbody\n" in rendered
    assert "header\n\nbody" not in rendered


def test_colored_concatenates_fragments():
    """Label/value fragments form one line; spacers stay blank lines."""
    message = Message()
    message.add("Environment: ", "title0")
    message.add("env_root_6.38.04")
    message.add("\n")
    rendered = _clean(message.colored())
    assert "Environment: env_root_6.38.04\n" in rendered
