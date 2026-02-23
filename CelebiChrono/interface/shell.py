"""
Shell interface module for Chern project management.

This module provides command-line interface functions for managing
projects, tasks, algorithms, and directories within the Chern system.
Maintains backward compatibility - forwards to modular implementation.
"""
# Explicit imports from shell_modules to avoid wildcard import warnings
from .shell_modules.navigation import (
    cd_project, shell_cd_project, cd, _cd_by_index, _cd_by_path, navigate
)
from .shell_modules.file_operations import (
    _normalize_paths, _validate_copy_operation, _adjust_destination_path,
    mv, cp, ls, predecessors, successors, short_ls, rm, rm_file, mv_file,
    import_file, add_source, send
)
from .shell_modules.object_creation import (
    mkalgorithm, mktask, mkdata, mkdir
)
from .shell_modules.task_configuration import (
    add_input, add_algorithm, add_parameter, add_parameter_subtask,
    set_environment, set_memory_limit, rm_parameter, remove_input,
    jobs, status, get_script_path, config
)
from .shell_modules.execution_management import (
    submit, purge, purge_old_impressions, test,
    collect, collect_outputs, collect_logs
)
from .shell_modules.communication import (
    dite, set_dite, add_host, hosts, runners, register_runner,
    remove_runner, request_runner, search_impression
)
from .shell_modules.visualization import (
    view, viewurl, impress, trace
)
from .shell_modules.utilities import (
    workaround_preshell, workaround_postshell, history,
    watermark, changes, doctor, bookkeep, bookkeep_url,
    tree, error_log, danger_call,
    git_merge, git_validate, git_status, git_enable,
    git_disable, git_hooks
)

# Explicitly export all functions for backward compatibility
# This ensures underscore-prefixed functions are also exported
__all__ = [
    # Navigation functions
    'cd_project', 'shell_cd_project', 'cd', '_cd_by_index', '_cd_by_path', 'navigate',
    # File operations functions
    '_normalize_paths', '_validate_copy_operation', '_adjust_destination_path',
    'mv', 'cp', 'ls', 'predecessors', 'successors', 'short_ls', 'rm', 'rm_file', 'mv_file',
    'import_file', 'add_source', 'send',
    # Object creation functions (from object_creation.py)
    'mkalgorithm', 'mktask', 'mkdata', 'mkdir',
    # Task configuration functions (from task_configuration.py)
    'add_input', 'add_algorithm', 'add_parameter', 'add_parameter_subtask',
    'set_environment', 'set_memory_limit', 'rm_parameter', 'remove_input',
    'jobs', 'status', 'get_script_path', 'config',
    # Execution management functions (from execution_management.py)
    'submit', 'purge', 'purge_old_impressions', 'test',
    'collect', 'collect_outputs', 'collect_logs',
    # Communication functions (from communication.py)
    'dite', 'set_dite', 'add_host', 'hosts', 'runners', 'register_runner',
    'remove_runner', 'request_runner', 'search_impression',
    # Visualization functions (from visualization.py)
    'view', 'viewurl', 'impress', 'trace',
    # Utilities functions (from utilities.py)
    'workaround_preshell', 'workaround_postshell', 'history',
    'watermark', 'changes', 'doctor', 'bookkeep', 'bookkeep_url',
    'danger_call', 'tree', 'error_log',
    # Git integration functions (from utilities.py)
    'git_merge', 'git_validate', 'git_status', 'git_enable',
    'git_disable', 'git_hooks',
    # MANAGER export
    'MANAGER'
]

# Import MANAGER explicitly for backward compatibility
from .shell_modules._manager import MANAGER
