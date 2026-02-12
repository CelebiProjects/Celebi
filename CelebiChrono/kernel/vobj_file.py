""" This module is used to manage the file system of the VObject

This is now a facade that combines functionality from specialized mixins.
"""
import os
import time
from os.path import join
from os.path import normpath
import shutil
from dataclasses import dataclass
from logging import getLogger
from typing import TYPE_CHECKING, Tuple, List
import difflib

from ..utils import csys
from ..utils.message import Message
from ..utils.csys import colorize_diff
from ..utils import metadata
from .vobj_core import Core
from .chern_cache import ChernCache
from .chern_communicator import ChernCommunicator

# Import the specialized mixins
from .vobj_file_display import FileManagementDisplay, LsParameters
from .vobj_file_operations import FileManagementOperations
from .vobj_file_status import FileManagementStatus

if TYPE_CHECKING:
    from .vobject import VObject

CHERN_CACHE = ChernCache.instance()
logger = getLogger("ChernLogger")

# Re-export LsParameters for backward compatibility
__all__ = ['FileManagement', 'LsParameters']


class FileManagement(
    FileManagementDisplay,
    FileManagementOperations,
    FileManagementStatus,
    Core  # Core should be last in MRO
):
    """ This class is used to manage the file system of the VObject

    This class now inherits functionality from specialized mixins:
    - FileManagementDisplay: Display and formatting methods
    - FileManagementOperations: File copy/move/remove operations
    - FileManagementStatus: Status and utility methods
    """
    # The class body is empty because all methods are inherited.
    # This maintains backward compatibility while splitting implementation.
    pass