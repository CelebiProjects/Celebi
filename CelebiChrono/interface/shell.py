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
    import_file, add_source, upload_data, transfer
)
from .shell_modules.replace_operations import replace as _replace
from .shell_modules.object_creation import (
    mkalgorithm, mktask, mkdata, mkdatalist, create_lhcb_ap_list, mkdir,
    attach_data, register_ssh_data, verify_data
)
from .shell_modules.task_configuration import (
    add_input, add_algorithm, add_parameter, add_parameter_subtask,
    set_environment, set_memory_limit, set_descriptor, rm_parameter, remove_input,
    jobs, status, get_script_path, config, add_apd_token, user_config
)
from .shell_modules.execution_management import (
    submit, submit_objects, purge, purge_old_impressions, test,
    collect, collect_outputs, collect_logs, engine_logs, refresh_filelists
)
from .shell_modules.communication import (
    dite, set_dite, add_host, hosts, runners, register_runner, update_runner,
    remove_runner, request_runner, search_impression, test_runner,
    runner_envs, purge_ssh_runner_cache, cache_results, whereabouts,
    sync_live, purge_stale_cache, purge_stale_workflows, kill_workflow
)
from .shell_modules.visualization import (
    view, viewurl, impress, impress_objects, trace, imgcat, draw_dag_graphviz
)
from .shell_modules.reana_booking import (
    book_reana, register_booking_server, check_booking_server
)
from .shell_modules.utilities import (
    workaround_preshell, workaround_postshell, history,
    watermark, changes, doctor, bookkeep, bookkeep_url,
    gc_impressions, pack_impressions, migrate_impressions, stats_impressions,
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
    'import_file', 'add_source', 'upload_data', 'transfer', 'replace',
    # Object creation functions (from object_creation.py)
    'mkalgorithm', 'mktask', 'mkdata', 'mkdatalist', 'create_lhcb_ap_list', 'mkdir', 'attach_data',
    'register_ssh_data',
    'verify_data',
    # Task configuration functions (from task_configuration.py)
    'add_input', 'add_algorithm', 'add_parameter', 'add_parameter_subtask',
    'set_environment', 'set_memory_limit', 'set_descriptor', 'rm_parameter', 'remove_input',
    'jobs', 'status', 'get_script_path', 'config', 'add_apd_token', 'user_config',
    # Execution management functions (from execution_management.py)
    'submit', 'submit_objects', 'purge', 'purge_old_impressions', 'test',
    'collect', 'collect_outputs', 'collect_logs', 'engine_logs',
    'refresh_filelists',
    # Communication functions (from communication.py)
    'dite', 'set_dite', 'add_host', 'hosts', 'runners', 'register_runner', 'update_runner',
    'remove_runner', 'request_runner', 'search_impression', 'test_runner',
    'runner_envs', 'purge_ssh_runner_cache', 'cache_results', 'whereabouts',
    # Visualization functions (from visualization.py)
    'view', 'viewurl', 'impress', 'impress_objects', 'trace', 'imgcat', 'draw_dag_graphviz',
    # Utilities functions (from utilities.py)
    'workaround_preshell', 'workaround_postshell', 'history',
    'watermark', 'changes', 'doctor', 'bookkeep', 'bookkeep_url',
    'gc_impressions', 'pack_impressions', 'migrate_impressions', 'stats_impressions',
    'danger_call', 'tree', 'error_log',
    # REANA booking functions (from reana_booking.py)
    'book_reana', 'register_booking_server', 'check_booking_server',
    # Git integration functions (from utilities.py)
    'git_merge', 'git_validate', 'git_status', 'git_enable',
    'git_disable', 'git_hooks',
    # MANAGER export
    'MANAGER'
]

# Import MANAGER explicitly for backward compatibility
from .shell_modules._manager import MANAGER


def replace(a: str, b: str, dry_run: bool = False):
    """Replace A with B in the names, inputs, and aliases of the current object.

    Args:
        a: The search string.
        b: The replacement string.
        dry_run: Whether to only report the planned actions.
    """
    return _replace(a, b, MANAGER.current_object(), dry_run)
