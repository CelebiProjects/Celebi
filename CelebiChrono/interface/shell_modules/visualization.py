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
        imgcat                    # List available output files

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
