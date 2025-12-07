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
# pylint: disable=too-many-locals,too-many-statements,import-error,no-member
import os
from ..interface.ChernManager import get_manager


MANAGER = get_manager()


class ChernShellVisualization:
    """Mixin class providing visualization methods for Chern Shell."""

    # pylint: disable=too-many-branches
    def do_draw_live_dag(self, arg):
        """Draw interactive DAG using Plotly."""
        import plotly.graph_objects as go
        import networkx as nx
        import numpy as np
        import pydot
        from collections import defaultdict
        from colorsys import hls_to_rgb, rgb_to_hls

        # Helper: Color Manipulation
        def lighten_color(hex_color, depth_factor):
            h = hex_color.lstrip('#')
            rgb = tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))
            hls = rgb_to_hls(*rgb)
            base_lightness = hls[1]
            new_lightness = max(
                0.15, min(0.9, base_lightness + 0.15 * (depth_factor % 5))
            )
            r, g, b = hls_to_rgb(hls[0], new_lightness, hls[2])
            return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

        # Colors
        base_color_map = {
            'red': '#FF4500',
            'blue': '#4169E1',
            'green': '#3CB371',
            'yellow': '#FFD700',
        }

        base_color_list = list(base_color_map.values())
        node_border_color = '#333'
        edge_color_default = '#D3D3D3'
        edge_hover_color = 'black'
        label_color = 'black'

        top_level_map = {}
        next_base_color_index = 0

        # Arguments
        args = arg.split()
        exclude_algorithms = "-x" in args
        show_permanent_labels = "-L" in args

        output_file = next(
            (a for a in args if not a.startswith("-")), "dag.html"
        )
        output_file = os.path.join(
            os.environ["HOME"], "Downloads", output_file
        )

        # Build Graph
        try:
            graph = MANAGER.c.build_dependency_dag(
                exclude_algorithms=exclude_algorithms
            )
        except Exception as e:
            print(f"Error building DAG: {e}")
            return

        if not graph.nodes:
            print("Graph is empty.")
            return

        print("Generating graph...")

        # Node Mapping + Color + Depth
        node_map = {}
        node_label_map = {}
        node_color_map = {}
        node_depth_map = {}

        for node in graph.nodes():

            if graph.nodes[node].get('node_type') == 'aggregate':
                simple_id = graph.nodes[node]['label']
                node_path = graph.nodes[node].get('aggregated_path', simple_id)
            else:
                simple_id = (
                    node.invariant_path() if hasattr(node, 'invariant_path')
                    else str(node)
                )
                node_path = simple_id
                if callable(node_path):
                    node_path = node_path()

            node_map[node] = simple_id
            node_label_map[simple_id] = simple_id

            path_segments = (
                node_path.replace("AGGREGATE:", "").strip("/").split('/')
            )
            top_level_group = path_segments[0] if path_segments else 'default'
            depth = len(path_segments) - 1
            node_depth_map[simple_id] = depth

            if top_level_group not in top_level_map:
                base_color = base_color_list[
                    next_base_color_index % len(base_color_list)
                ]
                top_level_map[top_level_group] = base_color
                next_base_color_index += 1
            else:
                base_color = top_level_map[top_level_group]

            final_color = lighten_color(base_color, depth)
            node_color_map[node] = final_color

        relabeled_graph = nx.relabel_nodes(graph, node_map)

        # TRUE RANKED GRAPHVIZ LAYOUT
        pydot_graph = nx.nx_pydot.to_pydot(relabeled_graph)

        rank_groups = {}
        for node_name, depth in node_depth_map.items():
            rank_groups.setdefault(depth, []).append(node_name)

        for depth, nodes in rank_groups.items():
            r = pydot.Subgraph(rank='same')
            for n in nodes:
                r.add_node(pydot.Node(n))
            pydot_graph.add_subgraph(r)

        pydot_graph.set_rankdir("TB")
        pydot_graph.set_nodesep("0.7")
        pydot_graph.set_ranksep("1.3")

        try:
            layout_graph = nx.nx_pydot.from_pydot(pydot_graph)
            pos_simple = nx.nx_pydot.graphviz_layout(layout_graph, prog="dot")
            pos = {
                original: pos_simple[node_map[original]]
                for original in graph.nodes()
            }
        except Exception as e:
            print(f"Warning: Graphviz failed, using spring layout ({e}).")
            pos = nx.spring_layout(graph, k=0.25, iterations=80)

        # LABEL COLLISION AVOIDANCE (VERTICAL JITTER)
        rank_bins = defaultdict(list)
        for node in graph.nodes():
            x, y = pos[node]
            rank_bins[round(y, 3)].append(node)

        max_jitter = 25.0  # Tune 10–25 if needed

        for _, nodes_in_same_rank in rank_bins.items():
            if len(nodes_in_same_rank) == 1:
                continue

            n = len(nodes_in_same_rank)
            offsets = np.linspace(-max_jitter, max_jitter, n)

            for node, dy in zip(nodes_in_same_rank, offsets):
                x, y = pos[node]
                pos[node] = (x, y + dy)

        # CURVED EDGES + BUNDLING + GHOST HOVER
        edge_traces = []
        arrow_annotations = []

        for u, v, data in graph.edges(data=True):
            if data.get('type') != 'dependency':
                continue

            edge_base_color = node_color_map.get(u, edge_color_default)
            x0, y0 = pos[u]
            x1, y1 = pos[v]

            source_label = node_label_map[node_map[u]]
            target_label = node_label_map[node_map[v]]
            hover_text = (
                f"Source: {source_label}<br>Target: {target_label}"
            )

            dy = y1 - y0
            cx = (x0 + x1) / 2
            cy = (y0 + y1) / 2 + 0.20 * abs(dy)
            bundle_offset = 0.18 * (hash(source_label) % 9 - 4)
            cx += bundle_offset

            t = np.linspace(0, 1, 25)
            curve_x = (1-t)**2 * x0 + 2*(1-t)*t*cx + t**2 * x1
            curve_y = (1-t)**2 * y0 + 2*(1-t)*t*cy + t**2 * y1

            ghost_hover_trace = go.Scatter(
                x=list(curve_x) + [None],
                y=list(curve_y) + [None],
                line={'width': 12, 'color': 'rgba(0,0,0,0)'},
                hoverinfo='text',
                hovertext=hover_text,
                mode='lines',
                opacity=0,
                hoverlabel={
                    'bgcolor': 'white',
                    'font': {'size': 10, 'color': edge_hover_color}
                }
            )
            edge_traces.append(ghost_hover_trace)

            visible_edge_trace = go.Scatter(
                x=list(curve_x) + [None],
                y=list(curve_y) + [None],
                line={'width': 2.5, 'color': edge_base_color},
                hoverinfo='none',
                mode='lines',
                opacity=0.85,
            )
            edge_traces.append(visible_edge_trace)

            arrow_annotations.append({
                'ax': curve_x[-3], 'ay': curve_y[-3],
                'x': curve_x[-1], 'y': curve_y[-1],
                'axref': 'x', 'ayref': 'y', 'xref': 'x', 'yref': 'y',
                'showarrow': True,
                'arrowhead': 2,
                'arrowsize': 2,
                'arrowwidth': 1,
                'arrowcolor': edge_base_color,
                'standoff': 10,
            })

        # Nodes + Labels
        node_x, node_y, node_text, node_colors = [], [], [], []
        permanent_annotations = []

        for node in graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_colors.append(node_color_map[node])

            # Visible label
            if graph.nodes[node].get('node_type') == 'aggregate':
                text_label = graph.nodes[node]['label']
            else:
                text_label = getattr(node, 'invariant_path', str(node))
                if callable(text_label):
                    text_label = text_label()

            # Predecessors & Successors
            preds = list(graph.predecessors(node))
            succs = list(graph.successors(node))

            def _fmt(n):
                v = getattr(n, 'invariant_path', str(n))
                return v() if callable(v) else str(v)

            preds_str = (
                ",<br> ".join(_fmt(p) for p in preds) if preds else "None"
            )
            succs_str = (
                ",<br> ".join(_fmt(s) for s in succs) if succs else "None"
            )

            hover_text = (
                f"<b>{text_label}</b><br>"
                f"<b>Predecessors:</b><br> {preds_str}<br>"
                f"<b>Successors:</b><br> {succs_str}"
            )

            node_text.append(hover_text)

            # Permanent annotation (static label on canvas)
            permanent_annotations.append({
                'x': x, 'y': y + 20,
                'xref': 'x', 'yref': 'y',
                'text': text_label,
                'showarrow': False,
                'font': {'size': 10, 'color': label_color},
                'xanchor': 'center', 'yanchor': 'bottom'
            })

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker={
                'showscale': False,
                'color': node_colors,
                'size': 20,
                'line_width': 2,
                'line_color': node_border_color
            },
        )

        # Final Figure
        layout = go.Layout(
            title={
                'text': f'Dependency DAG: {MANAGER.c.invariant_path()}',
                'font': {'size': 16}
            },
            showlegend=False,
            hovermode='closest',
            margin={'b': 20, 'l': 5, 'r': 5, 't': 40},
            xaxis={'showgrid': False, 'zeroline': False,
                   'showticklabels': False},
            yaxis={'showgrid': False, 'zeroline': False,
                   'showticklabels': False}
        )

        fig = go.Figure(data=edge_traces + [node_trace], layout=layout)

        annotations = arrow_annotations
        if show_permanent_labels:
            annotations.extend(permanent_annotations)

        fig.update_layout(annotations=annotations)

        # Output
        if "." not in output_file:
            output_file += ".html"

        print(f"Saving graph to {output_file}...")

        if output_file.endswith(('.png', '.jpeg', '.jpg', '.pdf', '.svg')):
            try:
                fig.write_image(output_file)
                print("Done.")
            except ValueError as e:
                print(f"Error saving image: {e}")
                print(
                    "To save as static image, install kaleido: "
                    "pip install -U kaleido"
                )
        else:
            fig.write_html(output_file)
            print(f"Done. Open '{output_file}' in your browser to view.")

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
