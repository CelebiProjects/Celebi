import click
import sys
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