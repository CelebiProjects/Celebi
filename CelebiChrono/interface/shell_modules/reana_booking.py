"""REANA booking functions for shell interface."""
import os

from ...utils.message import Message
from ...utils import csys
from ...kernel.reana_booker import ReanaBooker


def book_reana(server_url: str = "", access_token: str = "") -> Message:
    """Book the current project to REANA.

    Uploads the current Celebi project files to a REANA instance
    as a file catalog entry. Uses workflow name 'celebi-{project_name}'.

    Args:
        server_url: REANA server URL. If empty, uses REANA_SERVER_URL env var.
        access_token: REANA access token. If empty, uses REANA_ACCESS_TOKEN env var.

    Returns:
        Message: Booking result with workflow URL or error information.

    Examples:
        book_reana()  # Uses env vars
        book_reana("https://reana.cern.ch", "my-token")
    """
    message = Message()

    # Resolve credentials
    server_url = server_url or os.environ.get("REANA_SERVER_URL", "")
    access_token = access_token or os.environ.get("REANA_ACCESS_TOKEN", "")

    if not server_url:
        message.add("REANA server URL not set. Use --server or set REANA_SERVER_URL env var.\n", "error")
        return message
    if not access_token:
        message.add("REANA access token not set. Use --token or set REANA_ACCESS_TOKEN env var.\n", "error")
        return message

    # Get project info
    project_path = csys.project_path()
    if not project_path:
        message.add("Not inside a Celebi project.\n", "error")
        return message

    project_name = os.path.basename(os.path.normpath(project_path))

    # Book to REANA
    booker = ReanaBooker(server_url, access_token)
    try:
        result = booker.book_project(project_path, project_name)
        return result
    except Exception as e:
        message.add(f"Booking failed: {e}\n", "error")
        return message
