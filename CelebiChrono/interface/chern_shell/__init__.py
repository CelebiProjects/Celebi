"""
chern_shell package - Interactive shell components for Chern.

Exports:
- ChernShellBase: Core shell functionality
- ChernShellCommands: Command handler aggregation
- ChernShellCompletions: Tab completion handlers
- ChernShellVisualization: DAG visualization methods
- ChernShell: Combined shell class
"""

from .base import ChernShellBase
from .commands import ChernShellCommands
from .completions import ChernShellCompletions
from .visualization import ChernShellVisualization
from .commands_execution import CommandsExecution

# Re-export for convenience
__all__ = [
    'ChernShellBase',
    'ChernShellCommands',
    'ChernShellCompletions',
    'ChernShellVisualization'
]