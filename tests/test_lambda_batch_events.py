"""Test the batch event handler for various kinds of error condition handling."""

from calcloud import io

from . import conftest

import batch_event_handler


def starting_metadata(overrides):
    """Fake the xdata associated with a brand new submission,  adding in `overrides` to tweak test cases."""
    d = conftest.Struct(io.get_default_metadata())
    d.job_id = "fake_job_id"
    d.update(overrides)
    return d


def setup_job(event_basename, **overrides):
    """Set up system as if batch job corresponding to `event_basename` event artifact has been submitted,
    first applying `overrides` to nominal xdata.
    """
    event = conftest.load_event(event_basename)
    overrides = overrides or {}
    ipppssoot = event.detail.container.command[1]
    comm = io.get_io_bundle()
    metadata = starting_metadata(overrides)
    comm.xdata.put(ipppssoot, metadata._to_dict())
    return event, comm, ipppssoot, conftest.Struct(metadata)


def test_batch_container_memory_error_retry(s3_client):
    """Batch kills the container due to memory shortage,  Python cut off at the knees."""

    event, comm, ipppssoot, starting_metadata = setup_job("batch-event-container-memory-error.yaml")

    batch_event_handler.lambda_handler(event, None)

    # what should be true now?  In metadata,  as messages
    ending_metadata = conftest.Struct(comm.xdata.get(ipppssoot))
    assert starting_metadata.memory_retries + 1 == ending_metadata.memory_retries
    assert starting_metadata.retries == ending_metadata.retries
    assert ending_metadata.terminated == False

    ending_messages = comm.messages.listl(f"all-{ipppssoot}")
    assert ending_messages == ["rescue-" + ipppssoot]


def test_batch_container_memory_error_exhausted(s3_client):
    """Batch kills the container due to memory shortage,  no retries left."""

    event, comm, ipppssoot, starting_metadata = setup_job("batch-event-container-memory-error.yaml", memory_retries=4)

    batch_event_handler.lambda_handler(event, None)

    ending_metadata = conftest.Struct(comm.xdata.get(ipppssoot))
    assert ending_metadata.memory_retries == 4
    assert starting_metadata.retries == ending_metadata.retries
    assert ending_metadata.terminated == False

    ending_messages = comm.messages.listl(f"all-{ipppssoot}")
    assert ending_messages == ["error-" + ipppssoot]


def test_batch_timeout_error(s3_client):
    """Batch reports job killed due to excessive runtime."""
    event, comm, ipppssoot, starting_metadata = setup_job("batch-event-timeout-error.yaml")

    batch_event_handler.lambda_handler(event, None)

    ending_metadata = conftest.Struct(comm.xdata.get(ipppssoot))
    assert ending_metadata.status_reason == "Job attempt duration exceeded timeout"
    assert ending_metadata.memory_retries == 0
    assert ending_metadata.retries == 0
    assert ending_metadata.exit_code == 137
    assert ending_metadata.exit_reason == "EXIT - unhandled exit code: 137"
    assert ending_metadata.terminated == False

    ending_messages = comm.messages.listl(f"all-{ipppssoot}")
    assert ending_messages == ["error-" + ipppssoot]


def test_batch_operator_cancelled(s3_client):
    """An operator cancelled the job.   Should not retry."""
    event, comm, ipppssoot, starting_metadata = setup_job("batch-event-operator-cancelled.yaml", terminated=True)

    batch_event_handler.lambda_handler(event, None)

    ending_metadata = conftest.Struct(comm.xdata.get(ipppssoot))
    assert ending_metadata.status_reason == "Operator cancelled"
    assert ending_metadata.memory_retries == 0
    assert ending_metadata.retries == 0
    assert ending_metadata.exit_code == 137
    assert ending_metadata.exit_reason == "EXIT - unhandled exit code: 137"
    assert ending_metadata.terminated == True

    ending_messages = comm.messages.listl(f"all-{ipppssoot}")
    assert ending_messages == ["terminated-" + ipppssoot]


def test_batch_python_memory_error(s3_client):
    """CALDP traps Python's MemoryError directly."""
    pass


def test_batch_os_memory_error(s3_client):
    """CALDP reports an OSError when running out of memory while launching a subprocess."""
    pass


def test_batch_log_memory_error(s3_client):
    """A subprocess of CALDP logs MemoryError,  exits with unrelated error status,  and CALDP re-categorizes as a memory error."""


def test_batch_generic_error_1(s3_client):
    """CALDP reports a generic error rather than one which is trapped and localized or categorized."""


def test_batch_stage2_error(s3_client):
    """CALDP reports a localized error."""


def test_batch_cannot_inspect_container(s3_client):
    """Batch returned CannotInspectContainer"""
