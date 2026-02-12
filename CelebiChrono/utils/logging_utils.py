"""
Centralized logging configuration for CelebiChrono.
"""
import logging

# Configure the root logger for Celebi
# This ensures consistent logging across all modules
def configure_logging(level=logging.INFO):
    """Configure logging for CelebiChrono."""
    logger = logging.getLogger("ChernLogger")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


# Pre-configured logger instance
_CHERN_LOGGER = configure_logging()


def get_chern_logger():
    """Return the centralized Chern logger instance."""
    return _CHERN_LOGGER


# For convenience, also export the standard logging module
# so modules can still import logging if needed
import logging as std_logging
__all__ = ['get_chern_logger', 'std_logging']