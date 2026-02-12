"""
Created by Mingrui Zhao @ 2017
define some classes and functions used throughout the project

This module is now a facade that re-exports functions from specialized submodules.
"""
# pylint: disable=broad-exception-caught

# Re-export all functions from specialized modules
from .color_utils import (
    colorize,
    color_print,
    debug,
    colorize_diff,
)

from .path_utils import (
    generate_uuid,
    abspath,
    strip_path_string,
    special_path_string,
    refine_path,
    exists_case_sensitive,
    exists_case_insensitive,
    exists,
    mkdir,
    project_path,
    dir_mtime,
    daemon_path,
    local_config_path,
    local_config_dir,
)

from .file_utils import (
    symlink,
    list_dir,
    walk,
    tree_excluded,
    sorted_tree,
    copy,
    rm_tree,
    copy_tree,
    move_case_sensitive,
    move,
    make_archive,
    unpack_archive,
    remove_cache,
    temp_dir,
    create_temp_dir,
    md5sum,
    dir_md5,
    update_time,
    get_files_in_directory,
    open_subprocess,
)

# For backward compatibility, also import the original module-level imports
# that might be used by external code
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

__all__ = [
    # color utilities
    'colorize',
    'color_print',
    'debug',
    'colorize_diff',
    # path utilities
    'generate_uuid',
    'abspath',
    'strip_path_string',
    'special_path_string',
    'refine_path',
    'exists_case_sensitive',
    'exists_case_insensitive',
    'exists',
    'mkdir',
    'project_path',
    'dir_mtime',
    'daemon_path',
    'local_config_path',
    'local_config_dir',
    # file utilities
    'symlink',
    'list_dir',
    'walk',
    'tree_excluded',
    'sorted_tree',
    'copy',
    'rm_tree',
    'copy_tree',
    'move_case_sensitive',
    'move',
    'make_archive',
    'unpack_archive',
    'remove_cache',
    'temp_dir',
    'create_temp_dir',
    'md5sum',
    'dir_md5',
    'update_time',
    'get_files_in_directory',
    'open_subprocess',
]