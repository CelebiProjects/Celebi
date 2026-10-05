"""Tests for Celebi application logging used by diagnostic agents."""
# pylint: disable=redefined-outer-name
from io import StringIO
import logging
from pathlib import Path
from unittest import mock

import pytest
import requests

from CelebiChrono.kernel.chern_communicator import ChernCommunicator
from CelebiChrono import main as main_module
from CelebiChrono.celebi_cli import cli as cli_module
from CelebiChrono.utils import csys
from CelebiChrono.utils import debug_logging


def _remove_managed_handlers():
    """Remove handlers installed by debug_logging so tests stay isolated."""
    logger = logging.getLogger("ChernLogger")
    for handler in list(logger.handlers):
        if getattr(handler, debug_logging._HANDLER_MARKER, None):  # pylint: disable=protected-access
            logger.removeHandler(handler)
            handler.close()


@pytest.fixture(autouse=True)
def logging_directory(monkeypatch, tmp_path):
    """Route application logs into each test's temporary directory."""
    _remove_managed_handlers()
    monkeypatch.setattr(csys, "local_config_dir", lambda: str(tmp_path))
    monkeypatch.delenv("CELEBI_DEBUG", raising=False)
    yield tmp_path
    _remove_managed_handlers()


def test_default_logging_writes_info_but_not_debug(logging_directory):
    """Normal commands create the persistent log without noisy debug records."""
    logger = debug_logging.setup_logging()
    logger.info("default info record")
    logger.debug("hidden debug record")
    for handler in logger.handlers:
        handler.flush()

    content = (Path(logging_directory) / "logs" / "celebi.log").read_text(
        encoding="utf-8"
    )
    assert "default info record" in content
    assert "hidden debug record" not in content


def test_false_environment_value_does_not_enable_debug(monkeypatch):
    """CELEBI_DEBUG=0 must not behave like an enabled flag."""
    monkeypatch.setenv("CELEBI_DEBUG", "0")
    logger = debug_logging.setup_logging()
    managed = [
        handler for handler in logger.handlers
        if getattr(handler, debug_logging._HANDLER_MARKER, None)  # pylint: disable=protected-access
    ]
    assert len(managed) == 1
    assert managed[0].level == logging.INFO


def test_repeated_initialization_upgrades_without_duplicate_handlers(capsys):
    """Interactive-shell initialization can safely follow CLI initialization."""
    logger = debug_logging.setup_logging()
    debug_logging.setup_logging(debug=True)
    debug_logging.setup_logging()

    managed = [
        handler for handler in logger.handlers
        if getattr(handler, debug_logging._HANDLER_MARKER, None)  # pylint: disable=protected-access
    ]
    assert len(managed) == 1
    handler_kinds = {
        getattr(handler, debug_logging._HANDLER_MARKER)  # pylint: disable=protected-access
        for handler in managed
    }
    assert handler_kinds == {"file"}
    assert all(handler.level == logging.DEBUG for handler in managed)
    logger.debug("file-only debug record")
    assert not capsys.readouterr().err


def test_all_command_entry_points_initialize_logging():
    """Both Click front ends and the git front end use the shared setup."""
    context = mock.MagicMock(invoked_subcommand="projects")
    with mock.patch.object(cli_module, "setup_logging") as cli_setup:
        cli_module.cli.callback(debug=True)
    cli_setup.assert_called_once_with(debug=True)

    with mock.patch.object(main_module, "setup_logging") as main_setup, \
            mock.patch.object(main_module, "is_first_time", return_value=False):
        main_module.cli.callback.__wrapped__(context, True, None)
    main_setup.assert_called_once_with(debug=True)

    with mock.patch.object(main_module, "setup_logging") as git_setup:
        main_module.git_cli.callback(debug=True)
    git_setup.assert_called_once_with(debug=True)


def _communicator():
    communicator = ChernCommunicator.__new__(ChernCommunicator)
    communicator.project_uuid = "project-1"
    return communicator


def _capture_chern_logger():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger("ChernLogger")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger, handler, stream


def test_http_request_log_contains_status_latency_and_safe_context():
    """Successful requests expose fields consumed by the performance agent."""
    communicator = _communicator()
    logger, handler, stream = _capture_chern_logger()
    response = mock.MagicMock(status_code=200)

    try:
        with mock.patch(
            "CelebiChrono.kernel.chern_communicator.requests.post",
            return_value=response,
        ):
            communicator._request(  # pylint: disable=protected-access
                "POST",
                "http://localhost:3315/execute?token=secret-query",
                "execute",
                data={"token": "secret-body"},
                timeout=10,
                log_context={"runner": "local"},
            )
    finally:
        logger.removeHandler(handler)

    output = stream.getvalue()
    assert "event=http_request" in output
    assert "operation=execute" in output
    assert "endpoint=/execute" in output
    assert "status=200" in output
    assert "latency=" in output
    assert "runner=local" in output
    assert "secret-query" not in output
    assert "secret-body" not in output


def test_http_timeout_is_logged_and_reraised():
    """Timeout evidence is retained without changing communicator semantics."""
    communicator = _communicator()
    logger, handler, stream = _capture_chern_logger()

    try:
        with mock.patch(
            "CelebiChrono.kernel.chern_communicator.requests.get",
            side_effect=requests.Timeout("request timed out"),
        ), pytest.raises(requests.Timeout):
            communicator._request(  # pylint: disable=protected-access
                "GET", "http://localhost:3315/status/project-1/imp-1", "status",
                timeout=10,
                log_context={"impression_uuid": "imp-1"},
            )
    finally:
        logger.removeHandler(handler)

    output = stream.getvalue()
    assert "event=http_request_error" in output
    assert "timeout=true" in output
    assert "error_type=Timeout" in output
    assert "impression_uuid=imp-1" in output
