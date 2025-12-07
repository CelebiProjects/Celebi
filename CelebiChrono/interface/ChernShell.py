# pylint: disable=invalid-name
"""
Chern Shell Interface Module.

This module provides an interactive command-line shell interface for managing
Chern projects, tasks, algorithms, and directories.

The shell functionality is organized into separate modules for maintainability:
- chern_shell_base: Core shell functionality and command parsing
- chern_shell_commands: All command handlers (do_* methods)
- chern_shell_completions: Tab completion handlers (complete_* methods)
- chern_shell_visualization: DAG visualization methods

Note: Broad exception handling is used throughout this module to ensure
the shell remains stable and provides user-friendly error messages.
This is a common pattern in interactive shells to prevent crashes.
"""
from .chern_shell_base import ChernShellBase
from .chern_shell_commands import ChernShellCommands
from .chern_shell_completions import ChernShellCompletions
from .chern_shell_visualization import ChernShellVisualization
from .ChernManager import get_manager


MANAGER = get_manager()
CURRENT_PROJECT_NAME = MANAGER.get_current_project()


class ChernShell(
    ChernShellBase,
    ChernShellCommands,
    ChernShellCompletions,
    ChernShellVisualization
):
    """Interactive command shell for Chern project management.

    This class combines all shell functionality through multiple inheritance:
    - ChernShellBase: Core shell setup, parsing, and completion framework
    - ChernShellCommands: All command implementations
    - ChernShellCompletions: Tab completion for commands
    - ChernShellVisualization: DAG drawing and visualization
    """

    def init(self) -> None:  # pylint: disable=arguments-differ
        """Initialize the shell with current project context."""
        super().init(MANAGER)
