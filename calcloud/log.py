"""Standard logging with invocation-scoped dataset context."""

import contextlib
from contextvars import ContextVar
import datetime as dt
from functools import wraps
import json
import logging
import os

_LOGGER_NAME = "calcloud"
_NOISY_LAMBDA_LOGGERS = ("botocore.credentials",)
_dataset = ContextVar("dataset", default="unknown")


@contextlib.contextmanager
def dataset_context(dataset):
    """Temporarily tag logs, restoring the previous context even after an exception."""
    token = _dataset.set(dataset)
    try:
        yield
    finally:
        _dataset.reset(token)


def lambda_logging(dataset_from_event):
    """Scope dataset context to one invocation, including calls to shared helpers."""

    def decorate(handler):
        @wraps(handler)
        def wrapped(event, *args, **kwargs):
            with dataset_context("unknown"):
                with dataset_context(dataset_from_event(event)):
                    return handler(event, *args, **kwargs)

        return wrapped

    return decorate


class DatasetFilter(logging.Filter):
    """Enrich records without overriding explicitly supplied dataset fields."""

    def filter(self, record):
        if not getattr(record, "dataset", None):
            record.dataset = _dataset.get()
        return True


_dataset_filter = DatasetFilter()


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

        payload["dataset"] = getattr(record, "dataset", None) or _dataset.get()

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
    for handler in root.handlers:
        if _dataset_filter not in handler.filters:
            handler.addFilter(_dataset_filter)

    if _is_lambda_environment():
        formatter = JsonLogFormatter()
        for handler in root.handlers:
            handler.setFormatter(formatter)
        for logger_name in _NOISY_LAMBDA_LOGGERS:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

    logger = logging.getLogger(name)
    logger.setLevel(logging.NOTSET)
    if _dataset_filter not in logger.filters:
        logger.addFilter(_dataset_filter)
    return logger


@contextlib.contextmanager
def trap_exception(*args):
    """Log an exception message and continue instead of re-raising it."""
    logger = logging.getLogger(__name__)
    try:
        yield
    except Exception as exc:
        logger.info("Trapped exception %s was: %s", " ".join(args), exc)
