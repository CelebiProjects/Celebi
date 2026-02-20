""" The module for arc management of VObject

This is now a facade that combines functionality from specialized mixins.
"""
from logging import getLogger

from .vobj_core import Core
from .chern_cache import ChernCache

# Import the specialized mixins
from .vobj_arc_operations import ArcManagementOperations
from .vobj_arc_traversal import ArcManagementTraversal
from .vobj_arc_doctor import ArcManagementDoctor
from .vobj_arc_input import ArcManagementInput
from .vobj_arc_graph import ArcManagementGraph

CHERN_CACHE = ChernCache.instance()
logger = getLogger("ChernLogger")


class ArcManagement(
    ArcManagementOperations,
    ArcManagementTraversal,
    ArcManagementDoctor,
    ArcManagementInput,
    ArcManagementGraph,
    Core  # Core should be last in MRO
):
    """ The class for arc management of VObject

    This class now inherits functionality from specialized mixins:
    - ArcManagementOperations: Basic arc add/remove operations
    - ArcManagementTraversal: Predecessor/successor traversal methods
    - ArcManagementDoctor: Doctor methods for arc validation and repair
    - ArcManagementInput: Input management methods
    - ArcManagementGraph: Graph building methods for dependency visualization
    """
    # The class body is empty because all methods are inherited.
    # This maintains backward compatibility while splitting implementation.
