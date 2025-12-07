"""
Created by Mingrui Zhao @ 2017
define some classes and functions used throughout the project
"""
# Load module
from colored import fg, attr

def colorize(string: str, color: str = "") -> str:
    """Make the string have color"""
    colors = {
        "success": fg("green") + string + attr("reset"),
        "normal": fg("blue") + string + attr("reset"),
        "running": fg("yellow") + string + attr("reset"),
        "warning": "\033[31m" + string + "\033[m",
        "debug": "\033[31m" + string + "\033[m",
        "comment": fg("blue") + string + attr("reset"),
        "title0": fg("red") + attr("bold") + string + attr("reset")
    }
    if color == "":
        possible_status = {
            "success": ["success", "done", "pass", "connected", "ok", "good",
                        "succeed", "validated", "archived", "finished",
                        "true"],
            "normal": ["normal", "info", "new", "raw", "empty"],
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

def color_print(string, color):
    """Print the string with color"""
    print(colorize(string, color))
