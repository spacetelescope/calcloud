"""Test the batch event handler for various kinds of error condition handling."""

from calcloud import io

from . import conftest

import batch_event_handler


# --------------------------------------------------------------------------------------


def starting_metadata(overrides):
    """Fake the xdata associated with a brand new submission,  adding in `overrides` to tweak test cases."""
    d = io.get_default_metadata()
    d["job_id"] = "fake_job_id"
    d.update(overrides)
    return d


def setup_job(event_basename, **overrides):
    """Set up system as if batch job corresponding to `event_basename` event artifact has been submitted,
    first applying `overrides` to nominal xdata.
    """
    event = conftest.load_event(event_basename)
    overrides = overrides or {}
    ipppssoot = event["detail"]["container"]["command"][1]
    comm = io.get_io_bundle()
    metadata = starting_metadata(overrides)
    comm.xdata.put(ipppssoot, metadata)
    return event, comm, ipppssoot, metadata


def assert_final_message(msg_type, event_basename, **overrides):
    """Run a test on event file event_basename overriding values in the event using **overrides.
    Verify that the event handler generates a message of `msg_type` for the appropriate ipppssoot.
    Return the starting and ending xdata (job metadata) dictionaries.
    """
    event, comm, ipppssoot, starting = setup_job(event_basename, **overrides)
    batch_event_handler.lambda_handler(event, None)
    ending = comm.xdata.get(ipppssoot)
    assert comm.messages.listl(f"all-{ipppssoot}") == [f"{msg_type}-{ipppssoot}"]
    return starting, ending


def assert_rescue(event_basename, **overrides):
    """Verify that the failure event generates only a rescue message."""
    return assert_final_message("rescue", event_basename, **overrides)


def assert_error(event_basename, **overrides):
    """Verify that the failyre event generates only an error message."""
    return assert_final_message("error", event_basename, **overrides)


def assert_terminated(event_basename, **overrides):
    """Verify that the failure event generates only a terminated message."""
    return assert_final_message("terminated", event_basename, **overrides)


def assert_rescue_ladder(event_basename, **overrides):
    starting, ending = assert_rescue(event_basename, **overrides)
    assert starting["memory_retries"] + 1 == ending["memory_retries"]
    assert starting["retries"] == ending["retries"]


def assert_rescue_no_ladder(event_basename, **overrides):
    starting, ending = assert_rescue(event_basename, **overrides)
    assert starting["memory_retries"] == ending["memory_retries"]
    assert starting["retries"] + 1 == ending["retries"]


def memory_error_handler(event_basename):
    assert_rescue_ladder(event_basename)
    assert_error(event_basename, memory_retries=4)
    assert_error(event_basename, terminated=True)


def error_w_retry(event_basename):
    assert_rescue_no_ladder(event_basename)
    assert_error(event_basename, retries=4)
    assert_error(event_basename, terminated=True)


def error_wo_retry(event_basename):
    assert_error(event_basename)
    assert_error(event_basename, retries=4)
    assert_error(event_basename, terminated=True)


# --------------------------------------------------------------------------------------


def test_batch_timeout_error(s3_client):
    """Batch reports job killed due to excessive runtime.  No retry"""
    error_wo_retry("batch-event-timeout-error.yaml")


def test_batch_operator_cancelled(s3_client):
    """An operator cancelled the job.   Should not retry."""
    assert_terminated("batch-event-operator-cancelled.yaml")


def test_batch_caldp_memory_error(s3_client):
    """CALDP traps Python's MemoryError directly."""
    memory_error_handler("batch-event-caldp-memory-error.yaml")


def test_batch_os_memory_error(s3_client):
    """CALDP reports an OSError when running out of memory while launching a subprocess."""
    memory_error_handler("batch-event-os-memory-error.yaml")


def test_batch_log_memory_error(s3_client):
    """A subprocess of CALDP logs MemoryError,  exits with unrelated error status,  and CALDP re-categorizes as a memory error."""
    memory_error_handler("batch-event-log-memory-error.yaml")


def test_batch_generic_error_1(s3_client):
    """CALDP reports a generic / localized error."""
    error_wo_retry("batch-event-generic-error.yaml")


def test_batch_docker_timeout_error(s3_client):
    """Batch took too long doing Docker start or create."""
    error_w_retry("batch-event-docker-timeout-error.yaml")


def test_batch_cannot_inspect_container(s3_client):
    """Batch returned CannotInspectContainer"""
    error_w_retry("batch-event-cannot-inspect-error.yaml")
