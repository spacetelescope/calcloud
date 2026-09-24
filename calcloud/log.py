"""Minimal project logging helpers built on Python's standard logging.

Lambda entrypoints configure standard `logging` loggers directly. This module
only keeps the shared configuration helper and the small exception-trapping
context manager that some call sites still use.
"""

import contextlib
import datetime as dt
import json
import logging
import os

_LOGGER_NAME = "calcloud"


class JsonLogFormatter(logging.Formatter):
    """Format log records as single-line JSON for log shippers."""

    def format(self, record):
        payload = {
            "timestamp": dt.datetime.fromtimestamp(record.created, tz=dt.timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        dataset = getattr(record, "dataset", None)
        if dataset is not None:
            payload["dataset"] = dataset

        aws_request_id = getattr(record, "aws_request_id", None)
        if aws_request_id is not None:
            payload["aws_request_id"] = aws_request_id

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)

        return json.dumps(payload, default=str)


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

    root.setLevel(level)

    if _is_lambda_environment():
        formatter = JsonLogFormatter()
        for handler in root.handlers:
            handler.setFormatter(formatter)

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
