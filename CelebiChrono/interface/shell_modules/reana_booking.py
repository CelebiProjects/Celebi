"""REANA booking functions for shell interface."""
import io
import os
import tarfile
from logging import getLogger

import requests

from ...utils.message import Message
from ...utils import csys
from ...utils import metadata

logger = getLogger("ChernLogger")


def _get_yuki_server_url() -> str:
    """Read Yuki server URL from project hosts config.

    The server URL is stored in the project's .celebi/hosts.json
    (same as ChernCommunicator.serverurl).
    """
    project_path = csys.project_path()
    if project_path:
        hosts_path = os.path.join(project_path, ".celebi", "hosts.json")
        if os.path.exists(hosts_path):
            config_file = metadata.ConfigFile(hosts_path)
            return config_file.read_variable("serverurl", "localhost:5000")
    return "localhost:5000"


def _pack_project_to_tar(project_path: str) -> io.BytesIO:
    """Pack project directory into an in-memory tar.gz archive.

    Args:
        project_path: Path to the project directory.

    Returns:
        io.BytesIO: The tar.gz archive in memory.
    """
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for root, dirs, files in os.walk(project_path):
            # Skip hidden dirs like .git, .celebi/impressions
            dirs[:] = [
                d for d in dirs
                if not d.startswith(".") or d == ".celebi"
            ]
            for filename in files:
                file_path = os.path.join(root, filename)
                arcname = os.path.relpath(file_path, project_path)
                tar.add(file_path, arcname=arcname)
    buf.seek(0)
    return buf


def register_booking_server(
    server_url: str = "",
    access_token: str = ""
) -> Message:
    """Register REANA server URL and access token with Yuki.

    Sends the credentials to Yuki, which stores them in its config
    (~/.Yuki/config.json) for future booking requests.

    Args:
        server_url: REANA server URL. If empty, uses REANA_SERVER_URL env var.
        access_token: REANA access token. If empty, uses REANA_ACCESS_TOKEN env var.

    Returns:
        Message: Registration result.
    """
    message = Message()

    # Resolve credentials
    server_url = server_url or os.environ.get("REANA_SERVER_URL", "")
    access_token = access_token or os.environ.get("REANA_ACCESS_TOKEN", "")

    if not server_url:
        message.add(
            "REANA server URL not set. Use --server or set REANA_SERVER_URL env var.\n",
            "error"
        )
        return message
    if not access_token:
        message.add(
            "REANA access token not set. Use --token or set REANA_ACCESS_TOKEN env var.\n",
            "error"
        )
        return message

    # Get Yuki server URL
    yuki_url = _get_yuki_server_url()
    if not yuki_url.startswith("http"):
        yuki_url = f"http://{yuki_url}"

    # Send credentials to Yuki
    try:
        response = requests.post(
            f"{yuki_url}/register-booking-server",
            json={
                "server_url": server_url,
                "access_token": access_token,
            },
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("success"):
            message.add(
                f"Booking server registered with Yuki ({yuki_url}).\n",
                "success"
            )
            message.add(
                f"  Server: {server_url}\n"
                "  Future 'book-reana' calls will use these stored credentials.\n",
                "info"
            )
        else:
            error_msg = result.get("error", "Unknown error")
            message.add(f"Failed to register booking server: {error_msg}\n", "error")

    except requests.exceptions.ConnectionError:
        message.add(
            f"Could not connect to Yuki server at {yuki_url}.\n"
            "Make sure Yuki is running or update the server URL with 'add-host'.\n",
            "error"
        )
    except requests.exceptions.Timeout:
        message.add("Request to Yuki server timed out.\n", "error")
    except Exception as e:
        message.add(f"Registration failed: {e}\n", "error")

    return message


def check_booking_server() -> Message:
    """Check the registered booking server URL and status.

    Queries Yuki for the stored booking server credentials
    and pings the REANA server to verify connectivity.

    Returns:
        Message: Status information about the booking server.
    """
    message = Message()

    # Get Yuki server URL
    yuki_url = _get_yuki_server_url()
    if not yuki_url.startswith("http"):
        yuki_url = f"http://{yuki_url}"

    try:
        response = requests.get(
            f"{yuki_url}/booking-server",
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("error"):
            message.add(f"Error: {result['error']}\n", "error")
            return message

        if not result.get("registered"):
            message.add("No booking server registered with Yuki.\n", "warning")
            message.add(
                "Use 'register-booking-server --server URL --token TOKEN' to register one.\n",
                "info"
            )
            return message

        # Display registered server info
        message.add("Booking server status:\n", "success")
        message.add(f"  Yuki server: {yuki_url}\n", "normal")
        message.add(f"  REANA URL:   {result.get('server_url', 'N/A')}\n", "normal")

        token_status = result.get("token_status", "unknown")
        if token_status == "set":
            masked = result.get("masked_token", "***")
            message.add(f"  Token:       {masked} (set)\n", "normal")
        else:
            message.add(f"  Token:       {token_status}\n", "warning")

        ping_status = result.get("ping_status", "unknown")
        if ping_status == "ok":
            message.add(f"  Ping:        OK\n", "success")
        else:
            message.add(f"  Ping:        {ping_status}\n", "error")

    except requests.exceptions.ConnectionError:
        message.add(
            f"Could not connect to Yuki server at {yuki_url}.\n"
            "Make sure Yuki is running or update the server URL with 'add-host'.\n",
            "error"
        )
    except requests.exceptions.Timeout:
        message.add("Request to Yuki server timed out.\n", "error")
    except Exception as e:
        message.add(f"Failed to check booking server: {e}\n", "error")

    return message


def _book_reana_sync(
    yuki_url: str,
    project_name: str,
    tar_buf,
    data: dict,
    message: Message,
) -> Message:
    """Fallback synchronous booking to Yuki (non-streaming)."""
    try:
        files = {
            "project_tar": ("project.tar.gz", tar_buf, "application/gzip"),
        }
        response = requests.post(
            f"{yuki_url}/book-reana",
            data=data,
            files=files,
            timeout=300,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("success"):
            for msg in result.get("messages", []):
                message.add(msg.get("text", ""), msg.get("status", "normal"))
            message.data.update(
                {k: v for k, v in result.items() if k not in ("success", "messages")}
            )
        else:
            for msg in result.get("messages", []):
                message.add(msg.get("text", ""), msg.get("status", "normal"))
            if not result.get("messages"):
                error_text = result.get("error", "Booking failed on Yuki server.")
                message.add(f"{error_text}\n", "error")

    except requests.exceptions.ConnectionError:
        message.add(
            f"Could not connect to Yuki server at {yuki_url}.\n"
            "Make sure Yuki is running or update the server URL with 'add-host'.\n",
            "error"
        )
    except requests.exceptions.Timeout:
        message.add("Request to Yuki server timed out.\n", "error")
    except Exception as e:
        message.add(f"Booking failed: {e}\n", "error")

    return message


def _book_reana_streaming(
    yuki_url: str,
    project_name: str,
    tar_buf,
    data: dict,
    message: Message,
) -> Message:
    """Stream booking progress from Yuki via NDJSON.

    Prints each progress message as it arrives from the server.
    Falls back to synchronous mode if the streaming endpoint is
    unavailable. All output is handled internally; callers should
    not print the returned message in streaming mode.
    """
    import json
    from CelebiChrono.utils.pretty import colorize

    files = {
        "project_tar": ("project.tar.gz", tar_buf, "application/gzip"),
    }

    def _flush_message(msg: Message) -> None:
        """Print all accumulated messages and clear the list."""
        if msg.messages:
            print(msg.colored(), end="", flush=True)
            msg.messages = []

    try:
        # Print any pre-existing messages (e.g. "Packing...", "Sending...")
        # before the server-side streaming starts.
        _flush_message(message)

        response = requests.post(
            f"{yuki_url}/book-reana-stream",
            data=data,
            files=files,
            stream=True,
            timeout=300,
        )

        # If streaming endpoint doesn't exist, fall back to sync
        if response.status_code == 404:
            message.add(
                "Streaming endpoint not available, falling back to sync mode.\n",
                "warning"
            )
            # Reset tar_buf read pointer for reuse
            tar_buf.seek(0)
            result = _book_reana_sync(yuki_url, project_name, tar_buf, data, message)
            _flush_message(result)
            return result

        response.raise_for_status()

        # Stream NDJSON lines
        line_count = 0
        for line in response.iter_lines():
            if not line:
                continue
            line_count += 1
            try:
                chunk = json.loads(line.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Non-JSON line — may be an HTML error page or old response format
                if line_count == 1:
                    preview = line[:200].decode("utf-8", errors="replace")
                    message.add(
                        f"Unexpected response from server (not NDJSON): {preview}\n",
                        "error"
                    )
                    _flush_message(message)
                continue

            if chunk.get("done"):
                # Final message with result data
                message.data.update(chunk.get("data", {}))
                if not chunk.get("success"):
                    error_text = chunk.get("error", "Booking failed on Yuki server.")
                    message.add(f"{error_text}\n", "error")
                    # Print traceback for debugging if present
                    tb = chunk.get("traceback", "")
                    if tb:
                        import sys
                        print("\n--- Server traceback ---", file=sys.stderr)
                        print(tb, file=sys.stderr)
                        print("--- End traceback ---\n", file=sys.stderr)
                break

            text = chunk.get("text", "")
            status = chunk.get("status", "normal")
            # Print immediately for live feedback (don't accumulate —
            # already shown)
            print(colorize(text, status), end="", flush=True)

        if line_count == 0:
            message.add(
                "Server returned empty stream. "
                "The Yuki server may need to be restarted to load the new endpoint.\n",
                "warning"
            )
            _flush_message(message)

    except requests.exceptions.ConnectionError:
        message.add(
            f"Could not connect to Yuki server at {yuki_url}.\n"
            "Make sure Yuki is running or update the server URL with 'add-host'.\n",
            "error"
        )
        _flush_message(message)
    except requests.exceptions.Timeout:
        message.add("Request to Yuki server timed out.\n", "error")
        _flush_message(message)
    except Exception as e:
        message.add(f"Booking failed: {e}\n", "error")
        _flush_message(message)

    # Flush any remaining messages (e.g. error from final 'done' chunk)
    # before returning.
    _flush_message(message)
    return message


def book_reana(
    server_url: str = "",
    access_token: str = "",
    verify_ssl: bool = True,
    project_path: str = "",
    stageout: bool = False,
    stream: bool = True,
) -> Message:
    """Book the current project to REANA via Yuki.

    Packages the current Celebi project into a tar.gz, sends it to the
    Yuki server, which then uploads the files to a REANA instance.

    By default, uses streaming mode to show progress live. Falls back
    to synchronous mode if the streaming endpoint is unavailable.

    If server_url and access_token are not provided, Yuki will use
    credentials previously registered via register_booking_server().

    Args:
        server_url: REANA server URL. If empty, uses REANA_SERVER_URL env var
            or Yuki-stored credentials.
        access_token: REANA access token. If empty, uses REANA_ACCESS_TOKEN env var
            or Yuki-stored credentials.
        verify_ssl: Whether to verify SSL certificates.
        project_path: Path to the project directory. If empty, uses current directory.
        stageout: If True, also upload stageout files from Yuki storage to
            [reana_workspace]/impression_data/[impression_id]/stageout.
        stream: If True, use streaming mode for live progress. If False,
            wait for all output and print at the end.

    Returns:
        Message: Booking result with workflow URL or error information.
    """
    message = Message()

    # Resolve credentials (optional — Yuki can use stored credentials)
    server_url = server_url or os.environ.get("REANA_SERVER_URL", "")
    access_token = access_token or os.environ.get("REANA_ACCESS_TOKEN", "")

    # Get project info
    if project_path:
        project_path = os.path.abspath(project_path)
        if not os.path.isdir(project_path):
            message.add(f"Invalid project path: {project_path}\n", "error")
            return message
    else:
        project_path = csys.project_path()
        if not project_path:
            message.add("Not inside a Celebi project.\n", "error")
            return message

    project_name = os.path.basename(os.path.normpath(project_path))

    # Get Yuki server URL
    yuki_url = _get_yuki_server_url()
    if not yuki_url.startswith("http"):
        yuki_url = f"http://{yuki_url}"

    # Pack project into tar.gz
    message.add("Packing project files...\n", "normal")
    try:
        tar_buf = _pack_project_to_tar(project_path)
        message.add("Project packed.\n", "normal")
    except Exception as e:
        message.add(f"Failed to pack project: {e}\n", "error")
        return message

    # Prepare request data
    data = {
        "project_name": project_name,
        "verify_ssl": "true" if verify_ssl else "false",
        "stageout": "true" if stageout else "false",
    }
    # Only include credentials if explicitly provided
    if server_url:
        data["server_url"] = server_url
    if access_token:
        data["access_token"] = access_token

    # Send to Yuki
    message.add(f"Sending project to Yuki ({yuki_url})...\n", "normal")

    if stream:
        return _book_reana_streaming(yuki_url, project_name, tar_buf, data, message)
    else:
        return _book_reana_sync(yuki_url, project_name, tar_buf, data, message)
