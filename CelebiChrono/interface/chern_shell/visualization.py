"""
Visualization Module for Chern Shell.

This module contains DAG (Directed Acyclic Graph) visualization methods
for displaying project dependencies and task relationships.

Note: This module requires optional dependencies:
- plotly: For interactive HTML visualizations (do_draw_live_dag)
- graphviz: For static PDF/SVG/PNG visualizations (do_draw_dag_graphviz)
- pydot: For graph layout algorithms
Install with: pip install plotly graphviz pydot
"""
# pylint: disable=broad-exception-caught
from ._manager import MANAGER


class ChernShellVisualization:
    """Mixin class providing visualization methods for Chern Shell."""

    def do_draw_dag_graphviz(self, arg):
        """Draw DAG using Graphviz (supports PDF, SVG, PNG)."""
        # Parse arguments
        args = arg.split()
        exclude_algorithms = "-x" in args

        output_file = next(
            (a for a in args if not a.startswith("-")), "dag.pdf"
        )

        # Import and call the shared function
        from ..shell_modules.visualization import draw_dag_graphviz
        result = draw_dag_graphviz(output_file, exclude_algorithms)

        # Print the result
        if result.messages:
            print(result.colored())

    def help_draw_dag(self):
        """Help message for draw-dag."""
        print('\n'.join([
            "draw-dag [-x]",
            "Generates and displays a dependency graph (DAG) "
            "starting from the current object.",
            "The graph shows the object's predecessors "
            "(dependencies) recursively.",
            "Options:",
            "  -x: Exclude objects whose type is 'algorithm' "
            "from the graph.",
            "",
            "Requires 'matplotlib' and optionally 'pydot' or "
            "'pygraphviz' for best layout.",
        ]))
