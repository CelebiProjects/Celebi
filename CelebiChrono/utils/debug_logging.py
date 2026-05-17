"""Debug logging configuration for Celebi.

Enable via CELEBI_DEBUG=1 environment variable or --debug CLI flag.
Logs are written to ~/.celebi/logs/celebi.log with timestamps.
"""
import os
import logging
from logging import getLogger

_LOGGING_CONFIGURED = False


def setup_debug_logging():
    """Configure ChernLogger. Idempotent - safe to call multiple times."""
    global _LOGGING_CONFIGURED  # pylint: disable=global-statement
    if _LOGGING_CONFIGURED:
        return

    logger = getLogger("ChernLogger")
    log_level = logging.DEBUG if os.environ.get("CELEBI_DEBUG") else logging.ERROR
    logger.setLevel(log_level)

    if log_level == logging.DEBUG:
        from . import csys
        log_dir = os.path.join(csys.local_config_dir(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "celebi.log")
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(
            logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
        )
        logger.addHandler(file_handler)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(
            logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
        )
        logger.addHandler(stream_handler)

    _LOGGING_CONFIGURED = True
