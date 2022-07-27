"""test functionality of the rescue lambda
NOTE: since calcloud.lambda_submit.main catches timeout exceptions
while waiting for inputs, we have to use the contents of the error
message that is posted to catch that timeout"""

import pytest

from calcloud import io

from . import conftest
from . import common

# sadly importing the rescue handler here breaks the lambda mocking needed
# when actually sumitting jobs. the lambda must be imported after the mock
# has been established (so within each testing function) - bhayden
# import rescue_handler

import broadcast_handler


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
    comm.messages.put("rescue-all")
    event = conftest.get_message_event("rescue-all")
    rescue_handler.lambda_handler(event, {})

    # make sure the lambda deleted the rescue-all and posted the broadcast
    messages = comm.messages.listl()
    assert "rescue-all" not in messages

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


def test_rescue_all_w_override(s3_client):
    """with actual messages, rescue-all should post a broadcast message containing
    the rescue messages for the messages in rescue_handler.RESCUE_TYPES.
    And as usual, should delete the rescue-all message"""

    import rescue_handler

    comm = io.get_io_bundle()

    # payload to put in each rescue message
    timeout_scale_override = "timeout_scale: 1.5"
    rescue_overrides = {"rescue": timeout_scale_override}
    # sets up a list of messages of nearly all types, with a few extra error- messages
    ipppssoots, message_types = common.setup_error_messages(comm, overrides=rescue_overrides)

    # post the rescue-all, get a rescue-all event, and run the lambda
    comm.messages.put("rescue-all", timeout_scale_override)
    event = conftest.get_message_event("rescue-all")
    rescue_handler.lambda_handler(event, {})

    # # make sure the lambda deleted the rescue-all and posted the broadcast
    messages = comm.messages.listl()
    assert "rescue-all" not in messages

    # will raise AssertionError if broadcast doesn't exist
    broadcast_message = conftest.find_broadcast_message(comm)
    broadcast = conftest.get_broadcast(comm)

    # actually broadcast the messages so we can inspect the overrides
    event = conftest.get_message_event(broadcast_message)
    broadcast_handler.lambda_handler(event, {})

    # first the basic check that the broadcast message had the right contents
    counter = 0
    for i, (ipst, msg) in enumerate(zip(ipppssoots, message_types)):
        if msg in rescue_handler.RESCUE_TYPES:
            counter += 1
            assert f"rescue-{ipst}" in broadcast["messages"]
    # if the counter matches and the above assert succeeded, then this one only
    # fails if there's an extra unwanted message in the broadcast
    assert counter == len(broadcast["messages"])

    # now check the contents of each rescue message
    messages = comm.messages.listl()
    for m in messages:
        if m.startswith("rescue-"):
            payload = comm.messages.get(m)
            assert payload == timeout_scale_override


def test_rescue_ipst_timeout(s3_client, batch_client, iam_client):
    """does not post the inputs and memory features files, so the job submit should timeout"""
    import rescue_handler

    # grab the usual io bundle
    comm = io.get_io_bundle()

    # sets up a list of messages of nearly all types, with a few extra error- messages
    ipppssoots, message_types = common.setup_error_messages(comm)

    # run the lambda for the rescue message that's naturally in the list above
    for i, (ipst, m) in enumerate(zip(ipppssoots, message_types)):
        if m == "rescue":
            comm.messages.put(f"rescue-{ipst}")
            event = conftest.get_message_event(f"rescue-{ipst}")
            rescue_handler.lambda_handler(event, {})

    messages = comm.messages.listl()

    for i, (ipst, m) in enumerate(zip(ipppssoots, message_types)):
        if m == "rescue":
            text_check = f"Wait for inputs for {ipst} timeout, aborting submission."
            assert f"error-{ipst}" in messages
            payload = comm.messages.get(f"error-{ipst}")
            assert text_check in payload["exception"]


def test_rescue_ipst_no_override(s3_client, batch_client, iam_client, lambda_client):
    """does not post the inputs and memory features files, so the job submit should timeout"""
    import rescue_handler

    # garb the usual io bundle and setup the batch processing env
    comm = io.get_io_bundle()
    # conftest.setup_batch(iam_client, batch_client, busybox_sleep_timer=5)

    # sets up a list of messages of nearly all types, with a few extra error- messages
    ipppssoots, message_types = common.setup_error_messages(comm)

    # inputs and control must be in place
    for i, (ipst, m) in enumerate(zip(ipppssoots, message_types)):
        # put a generic metadata file
        d = io.get_default_metadata()
        comm.xdata.put(ipst, d)

        comm.control.put(f"{ipst}/{ipst}_MemModelFeatures.txt")
        comm.inputs.put(f"{ipst}.tar.gz")

    conftest.create_mock_lambda(lambda_client, iam_client)
    # assert False

    # run the lambda for the rescue message that's naturally in the list above
    for i, (ipst, m) in enumerate(zip(ipppssoots, message_types)):
        if m in rescue_handler.RESCUE_TYPES:
            comm.messages.put(f"rescue-{ipst}")
            event = conftest.get_message_event(f"rescue-{ipst}")
            rescue_handler.lambda_handler(event, {})

    messages = comm.messages.listl()

    print(messages)

    # UNFINISHED
    # assert False
