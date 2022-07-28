"""test functionality of the rescue lambda
NOTE: since calcloud.lambda_submit.main catches timeout exceptions
while waiting for inputs, we have to use the contents of the error
message that is posted to catch that timeout"""

import pytest

from calcloud import io
from calcloud import batch

from . import conftest
from . import common

# sadly importing the rescue handler here breaks the lambda mocking needed
# when actually sumitting jobs. the lambda must be imported after the mock
# has been established (so within each testing function) - bhayden
# import rescue_handler

import broadcast_handler


def post_inputs_control(comm, ipppssoots, message_types):
    """posts a default metadata in control, an empry MemModelFeatures.txt,
    and an empty inputs tar.gz file for each dataset in ipppssoot"""
    for i, (ipst, m) in enumerate(zip(ipppssoots, message_types)):
        # put a generic metadata file
        d = io.get_default_metadata()
        comm.xdata.put(ipst, d)

        comm.control.put(f"{ipst}/{ipst}_MemModelFeatures.txt")
        comm.inputs.put(f"{ipst}.tar.gz")


def post_and_run_rescue_ipst(comm, ipppssoots, message_types, overrides={}):
    """for each item in ipppssoots,message_types, post a rescue
    message for anything explicitly marked as rescue-able in
    the lambda"""
    import rescue_handler

    for i, (ipst, m) in enumerate(zip(ipppssoots, message_types)):
        if m in rescue_handler.RESCUE_TYPES:
            comm.messages.put(f"rescue-{ipst}", overrides)
            assert_rescue_payload(comm, overrides)
            event = conftest.get_message_event(f"rescue-{ipst}")
            rescue_handler.lambda_handler(event, {})


def run_rescues_by_type(comm, ipppssoots, message_types, check_types=("rescue")):
    """runs any rescue messages already in message_types"""
    import rescue_handler

    for i, (ipst, m) in enumerate(zip(ipppssoots, message_types)):
        if m in check_types:
            comm.messages.put(f"rescue-{ipst}")
            event = conftest.get_message_event(f"rescue-{ipst}")
            rescue_handler.lambda_handler(event, {})


def post_and_run_rescue_all(comm, overrides={}):
    """posts a rescue-all and runs the lambda
    accepts a dictionary of overrides"""
    import rescue_handler

    comm.messages.put("rescue-all", overrides)
    event = conftest.get_message_event("rescue-all")
    rescue_handler.lambda_handler(event, {})


def run_broadcast(broadcast_message):
    event = conftest.get_message_event(broadcast_message)
    broadcast_handler.lambda_handler(event, {})


def get_batch_job_names(comm):
    jobs = batch.get_job_ids(collect_statuses=batch.JOB_STATUSES)
    names = []
    for j in jobs:
        names.append(batch.get_job_name(j))

    return names


def assert_rescue_payload(comm, payload_check={}):
    """checks that each rescue message includes the desired payload"""
    messages = comm.messages.listl()
    for m in messages:
        if m.startswith("rescue-"):
            payload = comm.messages.get(m)
            # print(m,payload)
            # only enter if not an empty dict
            if payload_check:
                for k in payload_check.keys():
                    assert payload[k] == payload_check[k]
            else:
                pass
                # assert payload == payload_check
    # assert False


def assert_submit_messages(comm, ipppssoots, message_types):
    """asserts that every job needing rescue has a submit message
    to be run after the rescue_handler lambda"""
    import rescue_handler

    messages = comm.messages.listl()
    for i, (ipst, m) in enumerate(zip(ipppssoots, message_types)):
        if m in rescue_handler.RESCUE_TYPES:
            assert f"submit-{ipst}" in messages


def assert_broadcast(comm, ipppssoots, message_types):
    """asserts that a broadcast message posted by the lambda
    has the correct messages in it needing rescue"""
    import rescue_handler

    # will raise AssertionError if broadcast doesn't exist
    broadcast = conftest.get_broadcast(comm)

    counter = 0
    for i, (ipst, msg) in enumerate(zip(ipppssoots, message_types)):
        if msg in rescue_handler.RESCUE_TYPES:
            counter += 1
            assert f"rescue-{ipst}" in broadcast["messages"]
    # if the counter matches and the above assert succeeded, then this one only
    # fails if there's an extra unwanted message in the broadcast
    assert counter == len(broadcast["messages"])


def assert_no_rescue_all(comm):
    messages = comm.messages.listl()
    assert "rescue-all" not in messages


def assert_job_names(comm, ipppssoots, message_types, names):
    """asserts that the list of job names matches the ipppssoots that
    should have needed rescued"""
    import rescue_handler

    counter = 0
    for i, (ipst, m) in enumerate(zip(ipppssoots, message_types)):
        if m in rescue_handler.RESCUE_TYPES:
            assert ipst in names
            counter += 1
    assert counter == len(names)


def assert_submit_timeout(comm, ipppssoots, message_types, check_types=("rescue")):
    """asserts that the messages in check_types now have error messages indicating
    a timeout waiting for inputs"""
    messages = comm.messages.listl()
    for i, (ipst, m) in enumerate(zip(ipppssoots, message_types)):
        if m in check_types:
            text_check = f"Wait for inputs for {ipst} timeout, aborting submission."
            assert f"error-{ipst}" in messages
            payload = comm.messages.get(f"error-{ipst}")
            assert text_check in payload["exception"]


def test_rescue_all_nodata(s3_client):
    """with no messages to rescue, broadcast raises an AssertionError
    and the clean-all message should be deleted"""
    import rescue_handler

    comm = io.get_io_bundle()

    # first we'll test the simple, no overrides case
    comm.messages.put("rescue-all")

    event = conftest.get_message_event("rescue-all")

    # nothing to rescue, so comm.messages.broadcast raises an AssertionError instead of posting an empty broadcast
    with pytest.raises(AssertionError):
        rescue_handler.lambda_handler(event, {})

    messages = comm.messages.listl()
    assert not len(messages)


def test_rescue_all_no_override(s3_client):
    """with actual messages, rescue-all should post a broadcast message containing
    the rescue messages for the messages in rescue_handler.RESCUE_TYPES.
    And as usual, should delete the rescue-all message"""

    import rescue_handler

    comm = io.get_io_bundle()

    # sets up a list of messages of nearly all types, with a few extra error- messages
    ipppssoots, message_types = common.setup_error_messages(comm)

    # post the rescue-all, get a rescue-all event, and run the lambda
    post_and_run_rescue_all(comm)

    # make sure the lambda deleted the rescue-all
    assert_no_rescue_all(comm)

    # and posted the correct broadcast
    assert_broadcast(comm, ipppssoots, message_types)


def test_rescue_all_w_override(s3_client):
    """with actual messages, rescue-all should post a broadcast message containing
    the rescue messages for the messages in rescue_handler.RESCUE_TYPES.
    And as usual, should delete the rescue-all message"""

    import rescue_handler

    comm = io.get_io_bundle()

    # payload to put in each rescue message
    timeout_scale_override = {"timeout_scale": 1.5, "memBin": 1}
    # sets up a list of messages of nearly all types, with a few extra error- messages
    ipppssoots, message_types = common.setup_error_messages(comm, overrides=timeout_scale_override)

    # post the rescue-all, get a rescue-all event, and run the lambda
    post_and_run_rescue_all(comm, overrides=timeout_scale_override)

    # make sure the lambda deleted the rescue-all and posted the broadcast
    assert_no_rescue_all(comm)

    # will raise AssertionError if broadcast doesn't exist
    broadcast_message = conftest.find_broadcast_message(comm)
    # broadcast = conftest.get_broadcast(comm)

    # first the basic check that the broadcast message had the right contents
    assert_broadcast(comm, ipppssoots, message_types)

    # actually broadcast the messages so we can inspect the overrides
    run_broadcast(broadcast_message)

    # now check the contents of each rescue message
    assert_rescue_payload(comm, timeout_scale_override)


def test_rescue_ipst_timeout(s3_client, batch_client, iam_client):
    """does not post the inputs and memory features files, so the job submit should timeout"""
    import rescue_handler

    # grab the usual io bundle
    comm = io.get_io_bundle()

    # sets up a list of messages of nearly all types, with a few extra error- messages
    ipppssoots, message_types = common.setup_error_messages(comm)

    # run the lambda for the rescue message that's naturally in the list above
    run_rescues_by_type(comm, ipppssoots, message_types)

    # asserts an error message in messages, and the exception text in the payload
    assert_submit_timeout(comm, ipppssoots, message_types)


def test_rescue_ipst_no_override(s3_client, batch_client, iam_client, lambda_client, dynamodb_client):
    """run the actual job submits without any overrides in place"""
    import rescue_handler

    comm = io.get_io_bundle()

    # setup Batch
    conftest.setup_batch(iam_client, batch_client, busybox_sleep_timer=5)

    # sets up a list of messages of nearly all types, with a few extra error- messages
    ipppssoots, message_types = common.setup_error_messages(comm)

    # inputs and control must be in place
    post_inputs_control(comm, ipppssoots, message_types)

    # dynamodb must be in place
    conftest.setup_dynamodb(dynamodb_client)

    # mock of the job predict lambda must be in place
    conftest.create_mock_lambda(lambda_client, iam_client)

    # run the lambda for the rescue message that's naturally in the list above
    # this will submit the jobs, but they'll fail because the busybox
    # image won't have caldp-process in it
    post_and_run_rescue_ipst(comm, ipppssoots, message_types)

    # assert that every job needing a rescue now has a submit- message
    assert_submit_messages(comm, ipppssoots, message_types)

    # get the jobs from Batch and store the job names
    names = get_batch_job_names(comm)

    # assert that the names of the jobs from Batch match the ones needing rescue
    assert_job_names(comm, ipppssoots, message_types, names)


def test_rescue_ipst_w_override(s3_client, batch_client, iam_client, lambda_client, dynamodb_client):
    """does not post the inputs and memory features files, so the job submit should timeout"""
    import rescue_handler

    comm = io.get_io_bundle()

    # setup Batch
    conftest.setup_batch(iam_client, batch_client, busybox_sleep_timer=5)

    # sets up a list of messages of nearly all types, with a few extra error- messages
    # payload to put in each rescue message
    timeout_scale_override = {"timeout_scale": 1.5}
    # this object is only for the setup_error_messages function
    ipppssoots, message_types = common.setup_error_messages(comm, overrides=timeout_scale_override)

    # inputs and control must be in place
    post_inputs_control(comm, ipppssoots, message_types)

    # dynamodb must be in place
    conftest.setup_dynamodb(dynamodb_client)

    # mock of the job predict lambda must be in place
    conftest.create_mock_lambda(lambda_client, iam_client)

    # run the lambda for the rescue message that's naturally in the list above
    # this will submit the jobs, but they'll fail because the busybox
    # image won't have caldp-process in it
    # note: checking the payload is done within this call
    post_and_run_rescue_ipst(comm, ipppssoots, message_types, overrides=timeout_scale_override)

    # assert that every job needing a rescue now has a submit- message
    assert_submit_messages(comm, ipppssoots, message_types)

    # get the jobs from Batch and store the job names
    names = get_batch_job_names(comm)

    # assert that the names of the jobs from Batch match the ones needing rescue
    assert_job_names(comm, ipppssoots, message_types, names)
