"""
Shell interface modules package.

Re-exports all functions from submodules for backward compatibility.
"""
# Re-export all functions from submodules
from .navigation import *
from .file_operations import *
from .object_creation import *
from .task_configuration import *
from .execution_management import *
from .communication import *
from .visualization import *
from .utilities import *

# Export MANAGER for backward compatibility
from ._manager import MANAGER
