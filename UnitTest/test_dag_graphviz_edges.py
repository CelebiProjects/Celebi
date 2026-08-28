"""Tests for edge selection in the graphviz DAG renderer."""
import unittest
from unittest.mock import MagicMock, patch

import networkx as nx
from colored import Fore, Style

import prepare  # noqa: F401  pylint: disable=unused-import
from CelebiChrono.interface.shell_modules import visualization

TARGET = "misID/plot_misID_para_task"


class _Node:
    """Minimal stand-in for a VObject sitting in a dependency graph."""

    def __init__(self, path):
        self._path = path

    def invariant_path(self):
        """Return the object's invariant path."""
        return self._path


def _diamond_graph():
    """Graph where a task reads one predecessor directly and via another.

    misID_para_task -> plot_misID_para_task            (alias before_misID)
    misID_para_task -> misID_cut_task -> plot_...      (alias after_misID)
    plot_misID_para -> plot_misID_para_task            (algorithm)

    The direct para -> plot edge is implied by the two-hop path, but it is
    a real input the task reads, so it must still be drawn.
    """
    para = _Node("misID/misID_para_task")
    cut = _Node("misID/misID_cut_task")
    plot = _Node(TARGET)
    algorithm = _Node("misID/plot_misID_para")

    graph = nx.DiGraph()
    for source, target in (
            (para, plot), (cut, plot), (algorithm, plot), (para, cut)
    ):
        graph.add_edge(source, target, weight=1.0, type="dependency")

    # Layout-only clique edge, as added by build_dependency_dag for siblings
    graph.add_edge(algorithm, para, weight=10.0, type="sibling",
                   style="dashed")
    return graph


class TestDagGraphvizEdges(unittest.TestCase):
    """Every declared dependency must reach the rendered graph."""

    def _render(self):
        """Render a stub graph and return the edges handed to graphviz."""
        current = MagicMock()
        current.invariant_path.return_value = TARGET
        current.build_dependency_dag.return_value = _diamond_graph()

        dot = MagicMock()
        with patch.object(visualization, "MANAGER") as manager, \
                patch("graphviz.Digraph", return_value=dot):
            manager.current_object.return_value = current
            visualization.draw_dag_graphviz("dag.pdf")

        return [
            (call.args[0], call.args[1])
            for call in dot.edge.call_args_list
        ]

    def test_draws_all_declared_predecessors(self):
        """A predecessor also reachable via a longer path is still drawn."""
        print(Fore.BLUE + "Testing DAG predecessor edges..." + Style.RESET)
        sources = sorted(u for u, v in self._render() if v == TARGET)
        self.assertEqual(
            sources,
            [
                "misID/misID_cut_task",
                "misID/misID_para_task",
                "misID/plot_misID_para",
            ],
        )

    def test_layout_sibling_edges_are_not_drawn(self):
        """Sibling clique edges exist for layout only and stay hidden."""
        print(Fore.BLUE + "Testing sibling edge exclusion..." + Style.RESET)
        self.assertNotIn(
            ("misID/plot_misID_para", "misID/misID_para_task"),
            self._render(),
        )


if __name__ == "__main__":
    unittest.main()
