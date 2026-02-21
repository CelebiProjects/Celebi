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
# pylint: disable=broad-exception-caught,import-outside-toplevel
# pylint: disable=too-many-locals,too-many-statements,no-member
import os
from ._manager import MANAGER


class ChernShellVisualization:
    """Mixin class providing visualization methods for Chern Shell."""

    def do_draw_dag_graphviz(self, arg):
        """Draw DAG using Graphviz (supports PDF, SVG, PNG)."""
        import networkx as nx
        from collections import defaultdict
        import graphviz
        from colorsys import hls_to_rgb, rgb_to_hls

        # Helper: Color Lighter based on Depth
        def lighten_color(hex_color, depth_factor):
            """Adjusts the lightness component of a color based on depth."""
            h = hex_color.lstrip('#')
            rgb = tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))
            hls = rgb_to_hls(*rgb)
            new_l = max(0.30, min(0.80, hls[1] + 0.10 * (depth_factor % 7)))
            r, g, b = hls_to_rgb(hls[0], new_l, hls[2])
            return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

        # Constants tuned for massive DAGs
        base_colors = [
            '#FF4500', '#4169E1', '#3CB371', '#FFD700', '#8A2BE2', '#FF69B4'
        ]
        node_shape = 'box'
        node_font_size = '10'
        edge_penwidth = '1.2'
        graph_dpi = '150'

        # Args and Output Setup
        args = arg.split()
        exclude_algorithms = "-x" in args

        output_file = next(
            (a for a in args if not a.startswith("-")), "dag.pdf"
        )
        output_file = os.path.join(
            os.environ.get("HOME", "."), "Downloads", output_file
        )
        output_format = output_file.split('.')[-1].lower()

        if output_format not in ['svg', 'png', 'pdf']:
            output_format = 'pdf'
            output_file = os.path.splitext(output_file)[0] + ".pdf"

        # Build graph
        try:
            graph = MANAGER.c.build_dependency_dag(
                exclude_algorithms=exclude_algorithms
            )
        except Exception as e:
            print(f"Error building DAG: {e}")
            return

        if not graph.nodes:
            print("Graph empty.")
            return

        # Node identity, depth, color, and Grouping
        node_map = {}
        node_depth = {}
        top_color_map = {}
        color_idx = 0
        layers = defaultdict(list)

        for n in graph.nodes():
            if graph.nodes[n].get('node_type') == 'aggregate':
                sid = str(graph.nodes[n]['label'])
                path = graph.nodes[n].get('aggregated_path', sid)
            else:
                v = getattr(n, 'invariant_path', str(n))
                sid = str(v() if callable(v) else v)
                path = sid

            node_map[n] = sid

            parts = str(path).replace("AGGREGATE:", "").strip("/").split('/')
            top = parts[0] if parts and parts[0] else "default"
            depth = max(0, len(parts) - 1)

            node_depth[n] = depth
            layers[depth].append(sid)

            if top not in top_color_map:
                top_color_map[top] = base_colors[
                    color_idx % len(base_colors)
                ]
                color_idx += 1

            graph.nodes[n]['color_fill'] = lighten_color(
                top_color_map[top], depth
            )
            graph.nodes[n]['label'] = sid

        # Transitive Reduction
        dependency_graph = nx.DiGraph(
            (u, v, data) for u, v, data in graph.edges(data=True)
            if data.get('type') == 'dependency'
        )
        dependency_graph.add_nodes_from(graph.nodes(data=True))

        try:
            relabeled_graph = nx.relabel_nodes(dependency_graph, node_map)
            reduced_graph = nx.transitive_reduction(relabeled_graph)
            inv = {v: k for k, v in node_map.items()}
            reduced_dependency_edges = [
                (inv[u], inv[v]) for u, v in reduced_graph.edges()
            ]
        except Exception:
            reduced_dependency_edges = [
                (u, v) for u, v, data in dependency_graph.edges(data=True)
            ]

        # GRAPHVIZ RENDERING SETUP
        dot = graphviz.Digraph(
            comment=f"Dependency DAG: {MANAGER.c.invariant_path()}",
            graph_attr={
                'rankdir': 'LR',
                'splines': 'true',
                'overlap': 'false',
                'bgcolor': 'white',
                'nodesep': '0.5',
                'ranksep': '0.9',
                'dpi': graph_dpi,
            },
            node_attr={
                'shape': node_shape,
                'style': 'filled',
                'fontname': 'Helvetica',
                'fontsize': node_font_size,
                'margin': '0.15',
            },
            edge_attr={
                'fontname': 'Helvetica',
                'fontsize': '8',
                'penwidth': edge_penwidth,
                'color': '#555555',
            }
        )

        # Add Nodes
        for n in graph.nodes():
            dot.node(
                node_map[n],
                label=graph.nodes[n]['label'],
                fillcolor=graph.nodes[n]['color_fill'],
                color='#333333',
                fontcolor='#111111'
            )

        # Add Filtered Dependency Edges
        for u, v in reduced_dependency_edges:
            u_id = node_map[u]
            v_id = node_map[v]

            source_color = graph.nodes[u]['color_fill']

            dot.edge(
                u_id, v_id,
                color=source_color,
                arrowhead='normal',
                penwidth=edge_penwidth
            )

        # Save
        print(
            f"Rendering to {output_file} ({output_format.upper()} format)..."
        )
        try:
            dot.render(
                os.path.splitext(output_file)[0],
                format=output_format,
                cleanup=True
            )
            print("Done.")
        except Exception as e:
            print(
                "Save failed. Ensure Graphviz binaries are installed "
                f"and accessible on your system PATH. {e}"
            )

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
