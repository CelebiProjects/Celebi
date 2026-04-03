"""
Visualization functions for shell interface.

Functions for viewing, creating, and tracing impressions.
"""
import os
from collections import defaultdict

from ...utils.message import Message
from ._manager import MANAGER


def view(browser: str = "open") -> Message:
    """View impressions for current task.

    Opens task execution impressions in a web browser for visualization.
    Impressions are graphical representations of task execution results,
    including plots, charts, and interactive visualizations.

    Args:
        browser (str, optional): Browser command to use for opening URL.
            Defaults to "open" (system default browser).

    Examples:
        view()           # Open impressions in default browser
        view firefox     # Open impressions in Firefox
        view chrome      # Open impressions in Chrome

    Returns:
        Message: Status message indicating success or error.

    Note:
        - Current object must be a task
        - Task must have generated impressions
        - Browser command must be available in system PATH
        - Uses system's subprocess to launch browser
    """
    import subprocess
    message = Message()
    is_task = MANAGER.current_object().is_task()
    if not is_task:
        message.add("Not able to view", "error")
        return message
    url = MANAGER.current_object().impview()
    subprocess.call([browser, url])
    message.add("Opened view in browser", "success")
    return message


def viewurl() -> Message:
    """Get the impression URL for current task.

    Retrieves the URL where task execution impressions can be viewed.
    Returns empty string if current object is not a task or if no
    impressions are available.

    Args:
        None: Function takes no parameters.

    Examples:
        url = viewurl()  # Get impression URL
        print(f"View at: {viewurl()}")  # Display URL

    Returns:
        Message: Message containing the URL, or error if not available.

    Note:
        - Current object must be a task
        - Task must have generated impressions
        - URL may be local file path or web address
        - Empty return indicates no impressions available
    """
    message = Message()
    is_task = MANAGER.current_object().is_task()
    if not is_task:
        message.add("Not able to get view url", "error")
        return message
    url = MANAGER.current_object().impview()
    message.add(url, "normal")
    message.data["url"] = url
    return message


def impress() -> Message:
    """Create impression for current task or algorithm.

    Generates a visualization snapshot (impression) of the current object's
    state. Impressions capture execution results, data visualizations, or
    configuration states for later review or sharing.

    Args:
        None: Function takes no parameters.

    Examples:
        impress()  # Create impression for current object

    Returns:
        Message: Confirmation message containing impression creation status,
        UUID of created impression, and any generation details.

    Note:
        - Current object must be a task or algorithm
        - Impression content depends on object type and state
        - Generated impressions can be viewed with `view()` or `viewurl()`
        - Each impression has a unique UUID for identification
    """
    message = Message()
    current_obj = MANAGER.current_object()
    current_obj.impress()
    impression = current_obj.impression()
    if impression is None:
        message.add("Impression command finished, but no impression is available.", "warning")
        return message
    message.add(f"Created impression [{impression.uuid}]", "success")
    message.data["impression"] = impression.uuid
    return message


def trace(impression: str) -> Message:
    """Trace back to the task or algorithm that generated the impression.

    Navigates to the original task or algorithm that created a specific
    impression. Useful for understanding the provenance of visualization
    data or debugging execution pipelines.

    Args:
        impression (str): UUID or identifier of the impression to trace.

    Examples:
        trace abc123-def456-ghi789
        trace impression_2024_01_15

    Returns:
        Message: Message containing DAG comparison details in human-readable
        format with short UUIDs (7 characters) and type prefixes:
        - [TASK], [ALGO], [DATA], [PROJ] for object types
        - Bulleted lists for added/removed nodes and edges
        - Formatted as "parent → child" for edge relationships

    Note:
        - Impression must exist in current project
        - Source object must still be accessible
        - Changes current working context to source object
        - Useful for debugging complex execution chains
        - Output includes detailed DAG differences with human-readable formatting
    """
    return MANAGER.current_object().trace(impression)


def imgcat(filename: str = None) -> Message:
    """Display image file inline in terminal from dite.

    Fetches an image file from the dite server and displays it inline
    in the terminal using the iTerm2 imgcat protocol. Supported by
    iTerm2, Claude Code, and other compatible terminals.

    Args:
        filename: Name of the image file to display. If not provided,
            lists available image files.

    Examples:
        imgcat plot.png           # Display plot.png inline
        imgcat                    # List available image files

    Returns:
        Message: Status message or inline image data.

    Note:
        - Current object must be a task with an impression
        - File must exist in the task's output on dite
        - Terminal must support imgcat escape sequences
        - Supports PNG, JPG, GIF, BMP, WebP formats
    """
    import sys

    message = Message()
    current_obj = MANAGER.current_object()

    if not current_obj.is_task():
        message.add("imgcat is only available for tasks\n", "error")
        return message

    # If no filename provided, list available files
    if filename is None:
        success, result = current_obj.list_output_files()
        if not success:
            message.add(f"Failed to list files: {result}\n", "error")
            return message

        # Filter for image files
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
        images = [f for f in result if f.lower().endswith(image_extensions)]

        if not images:
            message.add("No image files found in task outputs.\n", "warning")
            message.add(f"Available files: {', '.join(result)}\n", "info")
        else:
            message.add("Available image files:\n", "title0")
            for img in images:
                message.add(f"  - {img}\n")
            message.add("\nUse 'imgcat <filename>' to display an image.\n", "info")
        return message

    # Display the image
    success, msg, imgcat_output = current_obj.imgcat(filename)

    if not success:
        message.add(f"{msg}\n", "error")
        return message

    # Output the imgcat escape sequence directly to stdout
    # This must be raw bytes, not through the message system
    sys.stdout.buffer.write(imgcat_output.encode('utf-8'))
    sys.stdout.buffer.write(b'\n')
    sys.stdout.flush()

    message.add(f"Displayed: {filename}\n", "success")
    return message


def draw_dag_graphviz(output_file: str = "dag.pdf", exclude_algorithms: bool = False) -> Message:
    """Draw DAG using Graphviz (supports PDF, SVG, PNG).

    Generates a visualization of the project dependency DAG using Graphviz.
    The graph shows task dependencies with color-coded nodes based on
    directory depth and top-level grouping.

    Args:
        output_file: Output filename (default: "dag.pdf").
            Supported formats: pdf, svg, png.
            Saved to ~/Downloads/ directory.
        exclude_algorithms: If True, excludes algorithm objects from the graph.

    Examples:
        draw_dag_graphviz()                    # Creates ~/Downloads/dag.pdf
        draw_dag_graphviz("mydag.svg")         # Creates ~/Downloads/mydag.svg
        draw_dag_graphviz("dag.png", True)     # Creates PNG excluding algorithms

    Returns:
        Message: Status message indicating success or failure.

    Note:
        - Requires graphviz Python package and Graphviz binaries
        - Requires networkx and pydot packages
        - Large graphs may take time to render
        - Output is always saved to ~/Downloads/
    """
    # pylint: disable=import-outside-toplevel,too-many-locals
    import networkx as nx
    import graphviz
    from colorsys import hls_to_rgb, rgb_to_hls

    message = Message()

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

    # Output Setup
    output_file = os.path.join(
        os.environ.get("HOME", "."), "Downloads", output_file
    )
    output_format = output_file.split('.')[-1].lower()

    if output_format not in ['svg', 'png', 'pdf']:
        output_format = 'pdf'
        output_file = os.path.splitext(output_file)[0] + ".pdf"

    # Build graph
    try:
        current_obj = MANAGER.current_object()
        graph = current_obj.build_dependency_dag(
            exclude_algorithms=exclude_algorithms
        )
    except Exception as e:
        message.add(f"Error building DAG: {e}", "error")
        return message

    if not graph.nodes:
        message.add("Graph empty.", "warning")
        return message

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
        comment=f"Dependency DAG: {current_obj.invariant_path()}",
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
    message.add(
        f"Rendering to {output_file} ({output_format.upper()} format)...\n",
        "normal"
    )
    try:
        dot.render(
            os.path.splitext(output_file)[0],
            format=output_format,
            cleanup=True
        )
        message.add("Done.", "success")
    except Exception as e:
        message.add(
            "Save failed. Ensure Graphviz binaries are installed "
            f"and accessible on your system PATH. {e}",
            "error"
        )

    return message
