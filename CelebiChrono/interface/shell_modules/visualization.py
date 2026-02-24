"""
Visualization functions for shell interface.

Functions for viewing, creating, and tracing impressions.
"""
import subprocess

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
