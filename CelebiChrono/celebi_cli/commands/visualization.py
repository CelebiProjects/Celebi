"""Visualization commands for Celebi CLI."""

import sys
import click

from CelebiChrono.celebi_cli.utils import format_output


def _handle_result(result):
    """Handle result from shell function."""
    output = format_output(result)
    if output:
        print(output)


def _handle_error(error):
    """Handle error from shell function."""
    print(f"Error: {error}", file=sys.stderr)
    sys.exit(1)


@click.command(name="view")
@click.argument("browser", type=str, required=False, default="open")
def view_command(browser):
    """View impressions for current task in browser.

    Opens task execution impressions in a web browser for visualization.
    Impressions are graphical representations of task execution results,
    including plots, charts, and interactive visualizations.

    Args:
        browser: Browser command to use for opening URL (default: "open").

    Examples:
        view           # Open impressions in default browser
        view firefox   # Open impressions in Firefox
        view chrome    # Open impressions in Chrome
    """
    try:
        from CelebiChrono.interface.shell import view
        result = view(browser)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="viewurl")
def viewurl_command():
    """Get the impression URL for current task.

    Retrieves the URL where task execution impressions can be viewed.
    Returns empty string if current object is not a task or if no
    impressions are available.

    Returns:
        URL for viewing task impressions, or empty string if not available.
    """
    try:
        from CelebiChrono.interface.shell import viewurl
        result = viewurl()
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="imgcat")
@click.argument("filename", type=str, required=False)
def imgcat_command(filename):
    """Display image file inline in terminal from dite.

    Fetches an image file from the dite server and displays it inline
    in the terminal using the iTerm2 imgcat protocol. Supported by
    iTerm2, Claude Code, and other compatible terminals.

    If no filename is provided, lists available image files from the
    task's output on dite.

    Args:
        filename: Name of the image file to display (optional).

    Examples:
        celebi imgcat plot.png        # Display plot.png inline
        celebi imgcat                  # List available image files

    Note:
        - Current object must be a task with an impression
        - File must exist in the task's output on dite
        - Terminal must support imgcat escape sequences
        - Supports PNG, JPG, GIF, BMP, WebP formats
    """
    try:
        from CelebiChrono.interface.shell import imgcat
        result = imgcat(filename)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")


@click.command(name="draw-dag")
@click.argument("output_file", type=str, required=False, default="dag.pdf")
@click.option(
    "--exclude-algorithms", "-x",
    is_flag=True,
    default=False,
    help="Exclude algorithm objects from the graph"
)
def draw_dag_command(output_file, exclude_algorithms):
    """Draw project dependency DAG using Graphviz.

    Generates a visualization of the project dependency DAG and saves it
    to the Downloads folder. Supports PDF, SVG, and PNG output formats.

    Args:
        output_file: Output filename (default: "dag.pdf").
            Saved to ~/Downloads/ directory.
        exclude_algorithms: If set, excludes algorithm objects from the graph.

    Examples:
        celebi draw-dag                    # Creates ~/Downloads/dag.pdf
        celebi draw-dag mydag.svg          # Creates ~/Downloads/mydag.svg
        celebi draw-dag dag.png -x         # Creates PNG excluding algorithms

    Note:
        - Requires graphviz Python package and Graphviz binaries installed
        - Requires networkx package
        - Output is always saved to ~/Downloads/
        - Large graphs may take time to render
    """
    try:
        from CelebiChrono.interface.shell import draw_dag_graphviz
        result = draw_dag_graphviz(output_file, exclude_algorithms)
        _handle_result(result)
    except ImportError as e:
        _handle_error(f"Failed to import shell function: {e}")
    except Exception as e:
        _handle_error(f"Command failed: {e}")
