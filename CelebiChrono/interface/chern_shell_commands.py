"""
Command Handlers Module for Chern Shell.

This module aggregates all command handler mixins from separate
focused modules. The original large file has been split into:

- commands_basic: Basic operations (ls, status, display, cat, collect)
- commands_navigation: Navigation (cd, cd_project, ls_projects)
- commands_file: File/directory management (mkdir, mv, cp, rm, import, export)
- commands_task: Task creation and configuration
- commands_environment: Environment settings and job execution
- commands_documentation: Documentation, help, and impressions
- commands_advanced: Advanced developer tools and debugging
"""
from .commands_basic import BasicCommands
from .commands_navigation import NavigationCommands
from .commands_file import FileCommands
from .commands_task import TaskCommands
from .commands_environment import EnvironmentCommands
from .commands_documentation import DocumentationCommands
from .commands_advanced import AdvancedCommands


class ChernShellCommands(
    BasicCommands,
    NavigationCommands,
    FileCommands,
    TaskCommands,
    EnvironmentCommands,
    DocumentationCommands,
    AdvancedCommands
):
    """
    Aggregated mixin class combining all command handlers.

    This class inherits from all command handler mixins to provide
    a single entry point for the ChernShell main class.
    """
