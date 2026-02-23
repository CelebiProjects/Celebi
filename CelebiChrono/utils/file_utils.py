"""
File operations utilities for CelebiChrono
"""
import os
import shutil
import tarfile
import hashlib
import subprocess
import uuid
import time
from pathlib import Path
from contextlib import contextmanager
from typing import Tuple, Iterator, List

from .path_utils import mkdir, exists, generate_uuid, strip_path_string


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


def walk(top) -> Iterator[Tuple[str, List[str], List[str]]]:
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
    target_dir = os.path.join("/tmp", prefix + generate_uuid())
    return target_dir


def create_temp_dir(name = "", prefix="chern_tmp_"):
    """ Create a temporary directory
    """
    if name:
        target_dir = os.path.join("/tmp", prefix + name)
        os.makedirs(target_dir, exist_ok=True)
        return target_dir
    temp_dir_uuid = os.path.join("/tmp", prefix + generate_uuid())
    os.makedirs(temp_dir_uuid, exist_ok=True)
    return temp_dir_uuid


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
    files_list = []
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
            files_list.append(rel)
    return files_list


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
