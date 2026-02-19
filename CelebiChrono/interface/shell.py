"""
Shell interface module for Chern project management.

This module provides command-line interface functions for managing
projects, tasks, algorithms, and directories within the Chern system.
Maintains backward compatibility - forwards to modular implementation.
"""
# Forward all imports to modular implementation
from .shell_modules import *

# Explicitly import underscore-prefixed functions that aren't imported by *
# because they start with underscore
from .shell_modules.navigation import _cd_by_index, _cd_by_path
from .shell_modules.file_operations import _normalize_paths, _validate_copy_operation, _adjust_destination_path

# Explicitly export all functions for backward compatibility
# This ensures underscore-prefixed functions are also exported
__all__ = [
    # Navigation functions
    'cd_project', 'shell_cd_project', 'cd', '_cd_by_index', '_cd_by_path', 'navigate',
    # File operations functions
    '_normalize_paths', '_validate_copy_operation', '_adjust_destination_path',
    'mv', 'cp', 'ls', 'successors', 'short_ls', 'rm', 'rm_file', 'mv_file',
    'import_file', 'add_source', 'send',
    # Object creation functions (from object_creation.py)
    'mkalgorithm', 'mktask', 'mkdata', 'mkdir',
    # Task configuration functions (from task_configuration.py)
    'add_input', 'add_algorithm', 'add_parameter', 'add_parameter_subtask',
    'set_environment', 'set_memory_limit', 'rm_parameter', 'remove_input',
    'add_host', 'hosts', 'dite', 'set_dite',
    # Execution management functions (from execution_management.py)
    'jobs', 'status', 'runners', 'register_runner', 'remove_runner',
    'request_runner', 'search_impression', 'submit', 'purge',
    'purge_old_impressions', 'test',
    # Communication functions (from communication.py)
    'view', 'viewurl', 'impress', 'get_script_path', 'config', 'danger_call',
    'workaround_preshell', 'workaround_postshell', 'trace', 'history',
    'watermark', 'changes', 'doctor', 'collect', 'collect_outputs',
    'collect_logs', 'bookkeep', 'bookkeep_url',
    # Visualization functions (from visualization.py)
    'tree', 'error_log',
    # Utilities functions (from utilities.py)
    # Note: _manager is imported separately below
    # MANAGER export
    'MANAGER'
]

# Import MANAGER explicitly for backward compatibility
from .shell_modules._manager import MANAGER