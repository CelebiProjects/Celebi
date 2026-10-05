"""Application logging configuration for Celebi.

Celebi always writes operational logs to ``~/.celebi/logs/celebi.log`` so
read-only diagnostics can inspect failures after a command exits. Debug mode
adds verbose records to the same file without changing terminal output.
"""
import logging
from logging import getLogger
from logging.handlers import RotatingFileHandler
import os

_HANDLER_MARKER = "_celebi_managed_handler"
_LOG_FORMAT = "[%(asctime)s][%(levelname)s] %(message)s"
_TRUE_VALUES = {"1", "true", "yes", "on"}


def _debug_from_environment() -> bool:
    """Return whether CELEBI_DEBUG explicitly enables debug logging."""
    return os.environ.get("CELEBI_DEBUG", "").strip().lower() in _TRUE_VALUES


def _managed_handler(logger, kind):
    """Find a handler installed by this module."""
    return next(
        (
            handler for handler in logger.handlers
            if getattr(handler, _HANDLER_MARKER, None) == kind
        ),
        None,
    )


def setup_logging(debug: bool = False):
    """Configure Celebi's file logger and return it.

    Repeated calls are safe. A later debug request upgrades existing handlers
    without duplicating them; it is not downgraded when the interactive shell
    performs its own initialization.
    """
    from . import csys

    logger = getLogger("ChernLogger")
    debug_enabled = debug or _debug_from_environment()
    file_handler = _managed_handler(logger, "file")
    if file_handler is not None and file_handler.level == logging.DEBUG:
        debug_enabled = True

    log_dir = os.path.join(csys.local_config_dir(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "celebi.log")
    formatter = logging.Formatter(_LOG_FORMAT)

    if file_handler is None:
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
            delay=True,
        )
        setattr(file_handler, _HANDLER_MARKER, "file")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    file_handler.setLevel(logging.DEBUG if debug_enabled else logging.INFO)

    # Handler levels perform normal/debug filtering. The logger itself must
    # accept DEBUG records so a later --debug call can upgrade it.
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger


def setup_debug_logging():
    """Backward-compatible alias honoring ``CELEBI_DEBUG``."""
    return setup_logging()
