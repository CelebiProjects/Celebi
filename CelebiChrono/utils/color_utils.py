"""
Color utilities for CelebiChrono
Combines color functionality from csys.py and pretty.py
"""
from typing import Any
from colored import fg, attr


def colorize(string: str, color: str = "") -> str:
    """Make the string have color.

    Supports both explicit color names and automatic detection.
    Color names:
    - "success": green
    - "normal": blue
    - "running": yellow
    - "warning": red ANSI
    - "debug": red ANSI
    - "comment": blue
    - "title0": red bold

    If color is empty string, automatically detect based on string content.
    """
    # Explicit color mapping
    colors = {
        "success": fg("green") + string + attr("reset"),
        "normal": fg("blue") + string + attr("reset"),
        "running": fg("yellow") + string + attr("reset"),
        "warning": "\033[31m" + string + "\033[m",
        "debug": "\033[31m" + string + "\033[m",
        "comment": fg("blue") + string + attr("reset"),
        "title0": fg("red") + attr("bold") + string + attr("reset")
    }

    if not color:
        # Automatic detection from pretty.py
        possible_status = {
            "success": ["success", "done", "pass", "connected",
                        "ok", "good", "ready", "coda",
                        "succeed", "validated", "archived", "finished",
                        "true"],
            "normal": ["normal", "info", "new", "raw", "empty", "prelude",
                       "orchestrating", "in movement", "undecided"],
            "running": ["running", "start", "pending", "queued", "waiting"],
            "warning": ["warning", "error", "fail", "failed", "wrong",
                        "incorrect", "bad", "unsuccessful", "false"],
            "debug": ["debug"],
        }
        for key, value in possible_status.items():
            if string.lower() in value:
                color = key
                break
            # if remove the bracket []:
            if string.lower()[1:-1] in value:
                color = key
                break

    return colors.get(color, string)  # Default to 'string' if color not found


def color_print(string: str, color: str) -> None:
    """Print the string with color"""
    print(colorize(string, color))


def debug(*arg: Any) -> None:
    """Print debug string"""
    print(colorize("debug >> ", "debug"), end="")
    for s in arg:
        print(colorize(s, "debug"), end=" ")
    print("*")


def colorize_diff(diff_lines):
    """Get the diff with color"""
    # ANSI color codes for terminal output
    _red = "\033[31m"
    _green = "\033[32m"
    _cyan = "\033[36m"
    _bold = "\033[1m"
    _reset = "\033[0m"

    out = []
    for line in diff_lines:
        if line.startswith("---") or line.startswith("+++"):
            out.append(_bold + _cyan + line.rstrip() + _reset)
        elif line.startswith("@@"):
            out.append(_cyan + line.rstrip() + _reset)
        elif line.startswith("-"):
            out.append(_red + line.rstrip() + _reset)
        elif line.startswith("+"):
            out.append(_green + line.rstrip() + _reset)
        else:
            out.append(line.rstrip())

    return "\n".join(out)
