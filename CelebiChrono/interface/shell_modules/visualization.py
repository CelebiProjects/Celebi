"""
Visualization functions for shell interface.

Functions for viewing, creating, and tracing impressions.
"""
import subprocess

from ...utils.message import Message
from ._manager import MANAGER


def view(browser: str = "open") -> None:
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
        None: Function opens browser with impression visualization.

    Note:
        - Current object must be a task
        - Task must have generated impressions
        - Browser command must be available in system PATH
        - Uses system's subprocess to launch browser
    """
    is_task = MANAGER.current_object().is_task()
    if not is_task:
        print("Not able to view")
        return
    url = MANAGER.current_object().impview()
    subprocess.call([browser, url])


def viewurl() -> str:
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
        str: URL for viewing task impressions, or empty string if
        not available.

    Note:
        - Current object must be a task
        - Task must have generated impressions
        - URL may be local file path or web address
        - Empty return indicates no impressions available
    """
    is_task = MANAGER.current_object().is_task()
    if not is_task:
        print("Not able to get view url")
        return ""
    url = MANAGER.current_object().impview()
    return url


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
    message = MANAGER.current_object().impress()
    return message


def trace(impression: str) -> None:
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
        None: Function navigates to source object of impression.

    Note:
        - Impression must exist in current project
        - Source object must still be accessible
        - Changes current working context to source object
        - Useful for debugging complex execution chains
    """
    MANAGER.current_object().trace(impression)