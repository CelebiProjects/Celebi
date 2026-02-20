"""
Path utilities for CelebiChrono
"""
import os
import uuid


def generate_uuid() -> str:
    """ Generate a uuid
    """
    return uuid.uuid4().hex


def abspath(path: str) -> str:
    """ Get the absolute path of the path
    """
    return os.path.abspath(path)


def strip_path_string(path_string: str) -> str:
    """ Remove the "/" in the end of the string
    and the " " in the begin and the end of the string.
    replace the "." in the string to "/"
    """
    path_string = path_string.strip(" ")
    path_string = path_string.rstrip("/")
    return path_string


def special_path_string(path_string: str) -> str:
    """ Replace the path string . -> /
    rather than the following cases
    .
    ..
    path/./../
    """
    if path_string.startswith("."):
        return path_string
    if path_string.find("/.") != -1:
        return path_string
    return path_string.replace(".", "/")


def refine_path(path: str, home: str) -> str:
    """ Refine the path
    """
    if path.startswith("~") or path.startswith("/"):
        path = home + path[1:]
    else:
        path = os.path.abspath(path)
    return path


def exists_case_sensitive(path: str) -> bool:
    """
    Checks if a path exists with strict case sensitivity,
    even on case-insensitive file systems.
    """
    if not os.path.exists(path):
        # print(f"Path: {path} does not exist at all.")
        return False

    path = os.path.abspath(path)
    current = os.path.abspath(os.sep)
    parts = path.split(os.sep)[1:] # Skip the root for Unix

    # print("parts is ", parts)
    # print("current is", current)
    for part in parts:
        if not part:
            continue # Handle double slashes
        if part not in os.listdir(current):
            return False
        current = os.path.join(current, part)

    return True


def exists_case_insensitive(path: str) -> bool:
    """
    Checks if a path exists, ignoring case.
    Works on both case-sensitive (Linux) and case-insensitive (Windows) systems.
    """
    path = os.path.normpath(path)
    parts = path.split(os.sep)

    # Handle the starting point (Root on Unix, Drive on Windows, or Current Dir)
    if path.startswith(os.sep):
        current = os.sep
        parts = parts[1:]
    elif len(parts[0]) > 1 and parts[0][1] == ':': # Windows Drive (e.g., C:)
        current = parts[0] + os.sep
        parts = parts[1:]
    else:
        current = '.'

    for part in parts:
        if not part:
            continue  # Skip empty parts from double slashes

        try:
            # List all items in the current directory
            entries = os.listdir(current)
        except OSError:
            # Folder might not exist or permission denied
            return False

        # Look for a case-insensitive match
        match = next((e for e in entries if e.lower() == part.lower()), None)

        if match is None:
            return False

        # Move deeper into the path using the ACTUAL casing found on disk
        current = os.path.join(current, match)

    return True


def exists(path: str) -> bool:
    """ Check the exists of path
    """
    return exists_case_sensitive(path)


def mkdir(directory):
    """ Safely make directory
    """
    if not exists_case_insensitive(directory):
        os.makedirs(directory)


def project_path(path=None):
    """ Get the project path by searching for project.json
    """
    if not path:
        path = os.getcwd()
    if not exists(path):
        return ""
    while path != "/":
        if exists(path+"/.celebi/project.json"):
            return abspath(path)
        path = abspath(path+"/..")
    return ""


def dir_mtime(path):
    """ Get the latest modified time of the directory
    """
    mtime = os.path.getmtime(path)
    if path.endswith(".celebi"):
        mtime = -1
    if not os.path.isdir(path):
        return mtime
    for sub_dir in os.listdir(path):
        if sub_dir == ".git":
            continue
        if sub_dir == "impressions":
            continue
        mtime = max(mtime, dir_mtime(os.path.join(path, sub_dir)))
    return mtime


def daemon_path():
    """ Get the daemon path
    """
    path = os.environ["HOME"] + "/.celebi/daemon"
    mkdir(path)
    return path


def local_config_path():
    """ Get the local config path
    """
    return os.environ["HOME"] + "/.celebi/config.json"


def local_config_dir():
    """ Get the local config directory
    """
    return os.environ["HOME"] + "/.celebi"
