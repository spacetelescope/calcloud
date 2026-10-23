import ast
from concurrent.futures import ThreadPoolExecutor
import io
import json
import logging
from pathlib import Path
from threading import Barrier

import pytest

from calcloud.log import JsonLogFormatter, configure_logging, dataset_context, lambda_logging, trap_exception


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
        assert payload["dataset"] == "unknown"
        assert handler.formatter.__class__ is JsonLogFormatter
    finally:
        root.handlers = original_handlers
        root.setLevel(original_level)


def test_lambda_handlers_establish_dataset_context():
    root = Path(__file__).resolve().parents[1]
    missing = []
    for path in (root / "lambda").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "lambda_handler":
                if not any(
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Name)
                    and decorator.func.id == "lambda_logging"
                    for decorator in node.decorator_list
                ):
                    missing.append(f"{path.relative_to(root)}:{node.lineno}")
    assert not missing, f"Lambda handlers without dataset context: {missing}"


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("messages/rescue-lezcg1010", "lezcg1010"),
        ("messages/placed-lezcg1010", "lezcg1010"),
        ("messages/processed-wfc3_cau_0c.trigger", "wfc3_cau_0c"),
        ("messages/processed-skycell-p0797x14y06.trigger", "skycell-p0797x14y06"),
        ("messages/clean-all", "all"),
        ("messages/clean-ingested", "all"),
        ("messages/broadcast-1234", "all"),
        ("messages/cancel-705d3803_ec5e_4492_a623_38f463f0f3a2", "unknown"),
        ("messages/processed-skycell%2Dp0797x14y06.trigger", "skycell-p0797x14y06"),
    ],
)
def test_s3_logging_dataset(key, expected, caplog):
    from calcloud import s3
    from . import conftest

    @lambda_logging(s3.event_dataset)
    def handler(event, context=None):
        return s3.parse_s3_event(event)

    caplog.set_level(logging.DEBUG, logger="calcloud")
    event = conftest.get_message_event(key.removeprefix("messages/"))
    assert s3.event_dataset(event) == expected
    bucket, tail = handler(event)
    assert bucket == f"s3://{conftest.BUCKET}"
    assert tail == "-".join(key.split("-")[1:])
    records = [record for record in caplog.records if record.name == "calcloud"]
    assert len(records) == 2
    assert all(record.dataset == expected for record in records)


def test_shared_helper_logging_dataset(s3_client, caplog):
    from calcloud import batch, io as cloud_io, job_features, model_ingest, s3
    from . import conftest

    dataset = "lezcg1010"
    configure_logging()
    caplog.set_level(logging.DEBUG, logger="calcloud")

    class BatchClient:
        def terminate_job(self, **kwargs):
            return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    with dataset_context(dataset):
        cloud_io.validate_control({})
        model_ingest.print_timestamp(0, "test", 0)
        bucket = model_ingest.s3.Bucket(conftest.BUCKET)
        assert job_features.get_s3_body_str_lines(bucket, "missing") is None
        missing_records = [record for record in caplog.records if record.getMessage() == "S3 object does not exist: missing"]
        assert len(missing_records) == 1
        assert missing_records[0].levelno == logging.INFO
        s3.put_object("test", f"s3://{conftest.BUCKET}/outputs/{dataset}/example.txt", client=s3_client)
        assert batch.terminate_job("job-id", "test", client=BatchClient())
        with trap_exception("test"):
            raise ValueError("expected")

    records = [record for record in caplog.records if record.name == "calcloud" or record.name.startswith("calcloud.")]
    assert len(records) == 7
    assert all(record.dataset == dataset for record in records)


@pytest.mark.parametrize("error", [RuntimeError, SystemExit])
def test_invocation_context_resets_after_success_and_failure(caplog, error):
    logger = configure_logging()

    @lambda_logging(lambda event: event["dataset"])
    def handler(event, context=None):
        logger.info("inside invocation")
        if event.get("fail"):
            raise error("test failure")
        return "ok"

    assert handler({"dataset": "lezcg1010"}) == "ok"
    logger.info("outside invocation")
    with pytest.raises(error):
        handler({"dataset": "wfc3_cau_0c", "fail": True})
    logger.info("after failure")
    with pytest.raises(KeyError):
        handler({})
    logger.info("after invalid event")
    assert handler({"dataset": "skycell-p0797x14y06"}) == "ok"

    records = [record for record in caplog.records if record.name == "calcloud"]
    assert [record.dataset for record in records] == [
        "lezcg1010",
        "unknown",
        "wfc3_cau_0c",
        "unknown",
        "unknown",
        "skycell-p0797x14y06",
    ]


def test_nested_context_restores_bulk_context(caplog):
    logger = configure_logging()
    with dataset_context("all"):
        logger.info("bulk")
        for dataset in ("lezcg1010", "wfc3_cau_0c"):
            with pytest.raises(ValueError):
                with dataset_context(dataset):
                    logger.info("dataset")
                    raise ValueError("expected")
            logger.info("bulk again")
    logger.info("finished")
    records = [record for record in caplog.records if record.name == "calcloud"]
    assert [record.dataset for record in records] == [
        "all",
        "lezcg1010",
        "all",
        "wfc3_cau_0c",
        "all",
        "unknown",
    ]


def test_dataset_context_isolated_between_threads(caplog):
    logger = configure_logging()
    barrier = Barrier(2)

    def work(dataset):
        with dataset_context(dataset):
            barrier.wait(timeout=10)
            logger.info(dataset)

    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(work, ("lezcg1010", "wfc3_cau_0c")))
    records = [record for record in caplog.records if record.name == "calcloud"]
    assert len(records) == 2
    assert all(record.dataset == record.getMessage() for record in records)


def test_bulk_cleanup_logs_all(s3_client, caplog):
    from calcloud import io as cloud_io

    configure_logging()
    caplog.set_level(logging.DEBUG, logger="calcloud")
    with dataset_context("all"):
        cloud_io.get_io_bundle().clean(["lezcg1010", "wfc3_cau_0c"])
    records = [record for record in caplog.records if record.name == "calcloud"]
    assert records
    assert all(record.dataset == "all" for record in records)


def test_rescue_logging_dataset(s3_client, monkeypatch, caplog):
    from calcloud import io as cloud_io, lambda_submit
    from . import conftest
    import rescue_handler

    dataset = "lezcg1010"
    comm = cloud_io.get_io_bundle()
    comm.messages.put(f"rescue-{dataset}")
    comm.inputs.put(f"{dataset}.tar.gz")
    comm.control.put(f"{dataset}/{dataset}_MemModelFeatures.txt")
    monkeypatch.setattr(lambda_submit.plan, "get_plan", lambda *args: "test plan")
    monkeypatch.setattr(lambda_submit.submit, "submit_job", lambda plan: {"jobId": "test-job"})
    caplog.clear()
    rescue_handler.lambda_handler(conftest.get_message_event(f"rescue-{dataset}"), None)
    records = [record for record in caplog.records if record.name == "calcloud"]
    assert any(record.getMessage() == f"Rescuing {dataset}" for record in records)
    assert any("Validating control metadata" in record.getMessage() for record in records)
    assert any("Submitted job for" in record.getMessage() for record in records)
    assert all(record.dataset == dataset for record in records)


@pytest.mark.parametrize("lookup_fails", [False, True])
def test_cancellation_scopes_resolved_dataset(s3_client, monkeypatch, caplog, lookup_fails):
    from calcloud import batch, io as cloud_io
    from . import conftest
    import delete_handler

    configure_logging()
    job_id = "705d3803_ec5e_4492_a623_38f463f0f3a2"
    dataset = "lezcg1010"
    comm = cloud_io.get_io_bundle()
    comm.messages.put(f"cancel-{job_id}")
    terminated = []

    def get_job_name(job_id):
        if lookup_fails:
            raise RuntimeError("lookup failed")
        return dataset

    class BatchClient:
        def terminate_job(self, **kwargs):
            terminated.append(kwargs["jobId"])
            return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    monkeypatch.setattr(batch, "get_job_name", get_job_name)
    monkeypatch.setattr(batch, "get_default_client", lambda: BatchClient())
    caplog.clear()
    delete_handler.lambda_handler(conftest.get_message_event(f"cancel-{job_id}"), None)

    assert terminated == [job_id.replace("_", "-")]
    records = [record for record in caplog.records if record.name.startswith("calcloud")]
    assert records
    assert records[0].dataset == "unknown"
    termination_records = [record for record in records if record.getMessage().startswith("terminate response:")]
    assert termination_records
    assert all(record.dataset == ("unknown" if lookup_fails else dataset) for record in termination_records)
    if not lookup_fails:
        assert comm.xdata.get(dataset)["terminated"] is True
        assert comm.messages.listl(f"terminated-{dataset}") == [f"terminated-{dataset}"]


def test_blackboard_logs_all(s3_client, monkeypatch, caplog):
    import scrape_batch

    configure_logging()
    caplog.set_level(logging.DEBUG, logger="calcloud")
    monkeypatch.setenv("JOBQUEUES", "test-queue")
    datasets = ["lezcg1010", "wfc3_cau_0c"]

    def list_jobs(queue, status, **kwargs):
        return [{"jobSummaryList": [{"jobId": dataset, "jobName": dataset} for dataset in datasets]}]

    monkeypatch.setattr(scrape_batch.batch, "_list_jobs_iterator", list_jobs)
    scrape_batch.lambda_handler({}, None)
    records = [record for record in caplog.records if record.name == "calcloud"]
    summaries = [record for record in records if record.getMessage().startswith("handling")]
    individual = [record for record in records if isinstance(record.msg, dict)]
    assert summaries
    assert {record.msg["jobName"] for record in individual} == set(datasets)
    assert all(record.dataset == "all" for record in records)


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
        with dataset_context("lezcg1010"):
            logger.info("submitted", extra={"dataset": "acs_9es_06"})

        payload = json.loads(stream.getvalue().strip())
        assert payload["dataset"] == "acs_9es_06"
    finally:
        root.handlers = original_handlers
        root.setLevel(original_level)


def test_dataset_filter_enriches_child_and_third_party_logs(caplog):
    logger = configure_logging()
    configure_logging()
    with dataset_context("lezcg1010"):
        logging.getLogger("calcloud.child").info("child")
        logging.getLogger("third.party").info("external")
        logger.info("override", extra={"dataset": "wfc3_cau_0c"})
    records = [record for record in caplog.records if record.getMessage() in ("child", "external", "override")]
    assert [record.dataset for record in records] == ["lezcg1010", "lezcg1010", "wfc3_cau_0c"]
    assert len(logger.filters) == 1


def test_json_formatter_uses_context_without_filter():
    record = logging.LogRecord("third.party", logging.INFO, __file__, 0, "test", (), None)
    with dataset_context("lezcg1010"):
        payload = json.loads(JsonLogFormatter().format(record))
    assert payload["dataset"] == "lezcg1010"


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
