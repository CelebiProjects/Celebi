"""Tests for the book-reana shell module."""
import inspect
from io import BytesIO

import requests

from CelebiChrono.interface.shell_modules import reana_booking
from CelebiChrono.utils.message import Message


def test_book_reana_has_upload_param_default_plots_logs():
    """book_reana defaults to plots+logs upload mode."""
    sig = inspect.signature(reana_booking.book_reana)
    assert "upload" in sig.parameters
    assert sig.parameters["upload"].default == "plots+logs"


def test_data_dict_includes_upload(monkeypatch):
    """The upload parameter is forwarded to the booking request data."""
    captured = {}

    def fake_sync(_yuki_url, _project_name, _tar_buf, data, message):
        """Fake sync."""
        captured.update(data)
        return message

    monkeypatch.setattr(reana_booking, "_book_reana_sync", fake_sync)
    monkeypatch.setattr(reana_booking, "_pack_project_to_tar", lambda _p: b"x")
    monkeypatch.setattr(reana_booking.os.path, "isdir", lambda _p: True)
    monkeypatch.setattr(reana_booking.csys, "project_path", lambda: "/tmp/proj")
    monkeypatch.setattr(reana_booking, "_get_yuki_server_url", lambda: "http://h:1")
    reana_booking.book_reana(project_path="/tmp/proj", upload="plots", stream=False)
    assert captured.get("upload") == "plots"


class _MockStreamResponse:
    """Fake requests.Response that yields NDJSON lines then raises."""

    def __init__(self, lines, raise_after):
        """Init."""
        self._lines = lines
        self._raise_after = raise_after
        self.status_code = 200

    def raise_for_status(self):
        """No-op for successful mock responses."""

    def iter_lines(self):
        """Yield pre-recorded lines, then raise the configured exception."""
        yield from self._lines
        raise self._raise_after


def test_streaming_reports_connection_lost_not_could_not_connect(monkeypatch, capsys):
    """If the connection drops after progress messages, say it was lost."""

    def mock_post(_url, **_kwargs):
        # Simulate Yuki streaming some progress, then the connection drops.
        """Mock post."""
        lines = [
            b'{"text": "Packing project files...\\n", "status": "normal"}',
            b'{"text": "Uploading stageout files...\\n", "status": "normal"}',
        ]
        return _MockStreamResponse(lines, requests.exceptions.ConnectionError("Connection reset"))

    monkeypatch.setattr(reana_booking.requests, "post", mock_post)

    message = Message()
    message.add("Packing project files...\n", "normal")
    tar_buf = BytesIO(b"fake tar")
    data = {"project_name": "B2D0Phi"}

    # pylint: disable=protected-access
    reana_booking._book_reana_streaming(
        "http://127.0.0.1:3315", "B2D0Phi", tar_buf, data, message
    )

    # Streaming mode prints directly; inspect stdout.
    captured = capsys.readouterr().out
    assert "lost" in captured.lower() or "dropped" in captured.lower()
    assert "Could not connect" not in captured


def test_streaming_initial_connection_failure_still_reports_could_not_connect(
    monkeypatch, capsys
):
    """If the very first POST fails, 'could not connect' is still accurate."""

    def mock_post(_url, **_kwargs):
        """Mock post."""
        raise requests.exceptions.ConnectionError("Connection refused")

    monkeypatch.setattr(reana_booking.requests, "post", mock_post)

    message = Message()
    tar_buf = BytesIO(b"fake tar")
    data = {"project_name": "B2D0Phi"}

    # pylint: disable=protected-access
    reana_booking._book_reana_streaming(
        "http://127.0.0.1:3315", "B2D0Phi", tar_buf, data, message
    )

    captured = capsys.readouterr().out
    assert "Could not connect" in captured
