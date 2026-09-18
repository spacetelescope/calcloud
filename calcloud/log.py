"""Minimal project logging helpers built on Python's standard logging.

Lambda entrypoints configure standard `logging` loggers directly. This module
only keeps the shared configuration helper and the small exception-trapping
context manager that some call sites still use.
"""

import contextlib
import logging
import os

_LOGGER_NAME = "calcloud"


def _is_lambda_environment():
    return "AWS_LAMBDA_FUNCTION_NAME" in os.environ


def configure_logging(name=_LOGGER_NAME, level=None):
    """Configure standard Python logging and return a logger.

    In Lambda we let the runtime's handlers do the work. Outside Lambda, if no
    handlers exist yet, install a default stream handler.
    """
    if level is None:
        level_name = os.environ.get("CALCLOUD_LOG_LEVEL", "INFO")
        level = getattr(logging, str(level_name).upper(), logging.INFO)

    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=level, format="%(levelname)s - %(message)s")
    else:
        root.setLevel(level)

    if _is_lambda_environment() and not root.handlers:
        logging.basicConfig(level=level, format="%(levelname)s - %(message)s")

    logger = logging.getLogger(name)
    logger.setLevel(logging.NOTSET)
    return logger


@contextlib.contextmanager
def trap_exception(*args):
    """Log an exception message and continue instead of re-raising it."""
    logger = logging.getLogger(__name__)
    try:
        yield
    except Exception as exc:
        logger.info("Trapped exception %s was: %s", " ".join(args), exc)
