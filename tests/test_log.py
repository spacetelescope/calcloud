import io
import json
import logging

from calcloud.log import JsonLogFormatter, configure_logging


def test_configure_logging_uses_json_formatter_in_lambda(monkeypatch):
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)

    try:
        root.handlers = [handler]
        monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "test-lambda")

        logger = configure_logging("test.lambda.logger")
        logger.info("hello %s", "world")

        payload = json.loads(stream.getvalue().strip())
        assert payload["level"] == "INFO"
        assert payload["logger"] == "test.lambda.logger"
        assert payload["message"] == "hello world"
        assert handler.formatter.__class__ is JsonLogFormatter
    finally:
        root.handlers = original_handlers
        root.setLevel(original_level)


def test_configure_logging_preserves_structured_dataset_fields_in_lambda(monkeypatch):
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)

    try:
        root.handlers = [handler]
        monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "test-lambda")

        logger = configure_logging("test.lambda.logger")
        logger.info("submitted", extra={"dataset": "acs_9es_06"})

        payload = json.loads(stream.getvalue().strip())
        assert payload["dataset"] == "acs_9es_06"
    finally:
        root.handlers = original_handlers
        root.setLevel(original_level)


def test_configure_logging_keeps_plain_formatter_outside_lambda(monkeypatch):
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))

    try:
        root.handlers = [handler]
        monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)

        logger = configure_logging("test.local.logger")
        logger.info("hello %s", "world")

        assert stream.getvalue().strip() == "INFO - hello world"
        assert handler.formatter._fmt == "%(levelname)s - %(message)s"
    finally:
        root.handlers = original_handlers
        root.setLevel(original_level)