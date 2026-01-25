"""
Created by Mingrui Zhao @ 2017
define some classes and functions used throughout the project
"""
# pylint: disable=broad-exception-caught
# Load module
import os
import time
import shutil
import uuid
import hashlib
import tarfile
import subprocess
from typing import Any
from pathlib import Path

from contextlib import contextmanager
from colored import fg, attr

# Utility Functions


def generate_uuid() -> str:
    """ Generate a uuid
    """
    return uuid.uuid4().hex


def colorize(string: str, color: str) -> str:
    """ Make the string have color
    """
    if color == "warning":
        return "\033[31m" + string + "\033[m"
    if color == "debug":
        return "\033[31m" + string + "\033[m"
    if color == "comment":
        return fg("blue") + string + attr("reset")
    if color == "title0":
        return fg("red")+attr("bold")+string+attr("reset")
    return string


def color_print(string: str, color: str) -> None:
    """ Print the string with color
    """
    print(colorize(string, color))


def debug(*arg: Any) -> None:
    """ Print debug string
    """
    print(colorize("debug >> ", "debug"), end="")
    for s in arg:
        print(colorize(s, "debug"), end=" ")
    print("*")


# Path and Directory Functions
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

# def exists(path: str) -> bool:
#     """ Check if the path exists
#     """
#     if not os.path.exists(path):
#         return False
#
#     # Normalize the path
#     path = os.path.abspath(path)
#     # Split into components
#     parts = path.split(os.sep)
#
#     # Handle root (e.g., '' or '/')
#     if not parts[0]:
#         current_path = os.sep
#         parts = parts[1:]
#     else:
#         current_path = parts[0]
#
#     for part in parts:
#         try:
#             entries = os.listdir(current_path)
#         except Exception:
#             return False
#         if part not in entries:
#             return False
#         current_path = os.path.join(current_path, part)
#     return True


def mkdir(directory):
    """ Safely make directory
    """
    if not exists_case_insensitive(directory):
        os.makedirs(directory)


def symlink(src, dst):
    """ Safely create a symbolic link
    """
    directory = os.path.dirname(dst)
    mkdir(directory)
    if exists(dst):
        os.remove(dst)
    os.symlink(src, dst)


def list_dir(src):
    """ List the files in the directory
    """
    files = os.listdir(src)
    return files


def walk(top):
    """ Walk the directory
    """
    d = list_dir(top)
    dirs = []
    names = []
    for f in d:
        if f == ".celebi":
            continue
        if f.startswith("."):
            continue
        if f.endswith("~undo-tree~"):
            continue
        if os.path.isdir(os.path.join(top, f)):
            dirs.append(f)
        else:
            names.append(f)
    yield ".", dirs, names
    for f in dirs:
        for path, dirs, names in os.walk(os.path.join(top, f)):
            path = os.path.relpath(path, top)
            if f.startswith("."):
                continue
            yield (path, dirs, names)


def tree_excluded(path):
    """ Get the file tree
    """
    file_tree = []
    for dirpath, dirnames, filenames in walk(path):
        # Exclude README.md of path/README.md
        if dirpath == ".":
            if "README.md" in filenames:
                filenames.remove("README.md")
        file_tree.append([dirpath, sorted(dirnames), sorted(filenames)])
    return sorted(file_tree)


def sorted_tree(tree):
    """ Sort the tree
    """
    for _, dirnames, filenames in tree:
        dirnames.sort()
        filenames.sort()
    tree.sort()
    return tree


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


# File Operations
def copy(src, dst):
    """ Safely copy file
    """
    directory = os.path.dirname(dst)
    mkdir(directory)
    shutil.copy2(src, dst)


def rm_tree(src):
    """ Remove the directory
    """
    shutil.rmtree(src)


def copy_tree(src, dst):
    """ Copy the directory
    """
    shutil.copytree(src, dst)

def move_case_sensitive(src, dst):
    """Move a directory, handling case-only renames on macOS."""
    src = Path(src)
    dst = Path(dst)

    if not src.exists():
        raise FileNotFoundError(src)

    # Case-only rename on case-insensitive filesystem
    if src.resolve().parent == dst.resolve().parent and src.name.lower() == dst.name.lower():
        tmp = src.with_name(f".{src.name}.{uuid.uuid4().hex}.tmp")
        src.rename(tmp)
        tmp.rename(dst)
    else:
        shutil.move(str(src), str(dst))

def move(src, dst):
    """ Move the directory
    """
    move_case_sensitive(src, dst)


def make_archive(filename, dir_name):
    """ Make the tar.gz file
    """
    with tarfile.open(filename+".tar.gz", "w:gz") as tar:
        tar.add(
            dir_name,
            arcname=os.path.basename(dir_name)
        )


def unpack_archive(filename, dir_name):
    """ Unpack the tar.gz file
    """
    shutil.unpack_archive(filename, dir_name, "tar")


def remove_cache(file_path):
    """ Remove the python cache file *.pyc *.pyo *.__pycache
    file_path = somewhere/somename.py
            or  somename.py
    """
    file_path = strip_path_string(file_path)
    if exists(file_path+"c"):
        os.remove(file_path+"c")
    if exists(file_path+"o"):
        os.remove(file_path+"o")
    index = file_path.rfind("/")
    if index == -1:
        try:
            shutil.rmtree("__pycache__")
        except OSError:
            pass
    else:
        try:
            shutil.rmtree(file_path[:index] + "/__pycache__")
        except OSError:
            pass

def temp_dir(name = "", prefix="chern_tmp_"):
    """ Get the temporary directory
    """
    if name:
        return os.path.join("/tmp", prefix + name)
    temp_dir = os.path.join("/tmp", prefix + generate_uuid())
    return temp_dir

def create_temp_dir(name = "", prefix="chern_tmp_"):
    """ Create a temporary directory
    """
    if name:
        temp_dir = os.path.join("/tmp", prefix + name)
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    temp_dir_uuid = os.path.join("/tmp", prefix + generate_uuid())
    os.makedirs(temp_dir_uuid, exist_ok=True)
    return temp_dir_uuid


# Checksum Functions
# def md5sum(filename, block_size=65536):
#     """ Get the md5sum of the file
#     """
#     md5 = hashlib.md5()
#     with open(filename, 'rb') as file:
#         for block in iter(lambda: file.read(block_size), b''):
#             md5.update(block)
#     return md5.hexdigest()
#
#
# def dir_md5(directory_path):
#     """ Get the md5sum of the directory
#     """
#     md5_hash = hashlib.md5()
#
#     for root, dirs, files in os.walk(directory_path):
#         # pylint: disable=unused-variable
#         for file in files:
#             file_path = os.path.join(root, file)
#             file_hash = md5sum(file_path)
#             md5_hash.update(file_hash.encode('utf-8'))
#
#     return md5_hash.hexdigest()

def md5sum(file_path):
    """ Get the md5sum of the file
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def dir_md5(directory_path):
    """Get the md5sum of the directory."""
    md5_hash = hashlib.md5()
    for root, dirs, files in os.walk(directory_path):
        dirs.sort()
        files.sort()
        for file in files:
            file_path = os.path.join(root, file)
            file_hash = md5sum(file_path)
            md5_hash.update(file_hash.encode("utf-8"))

    return md5_hash.hexdigest()

def colorize_diff(diff_lines):
    """ Get the diff with color
    """
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

def update_time(consult_id):
    """ update the time and consult_id
    """
    now = time.time()
    if consult_id:
        now = consult_id
    else:
        consult_id = now
    return now, consult_id

def get_files_in_directory(root, exclude=()):
    """ Get all files in the directory recursively, excluding specified paths
    """
    files = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            file_excluded = False
            for excl in exclude:
                if os.path.normpath(os.path.join(dirpath, f)).startswith(
                    os.path.normpath(os.path.join(root, excl))
                ):
                    file_excluded = True
                    break
            if file_excluded:
                continue
            rel = os.path.relpath(os.path.join(dirpath, f), root)
            files.append(rel)
    return files

@contextmanager
def open_subprocess(command):
    """ Open a subprocess
    """
    process = subprocess.Popen(command, shell=True)
    try:
        # Yield the process to the 'with' block
        yield process
    finally:
        # Ensure the subprocess is finished and cleaned up
        process.wait()
