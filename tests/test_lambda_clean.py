import copy
import pytest

from . import conftest

from calcloud import io

import clean_handler


def assert_empty_messages(comm):
    messages = comm.messages.listl()
    assert len(messages) == 0


def setup_diverse_messages(comm):
    """posts messages of most types from io.MESSAGE_TYPES
    ignores broadcast and clean message types"""
    assert_empty_messages(comm)

    # we'll make a message of each type for a unique list of ipppssoots
    message_types = copy.copy(io.MESSAGE_TYPES)
    # ... except for broadcast and clean
    message_types.remove("broadcast")
    message_types.remove("clean")

    # insert the messages
    ipppssoots = []
    for i, m in enumerate(message_types):
        ipst = f"ipppssoo{i}"
        ipppssoots.append(ipst)
        comm.messages.put(f"{m}-{ipst}")

    # read them back and assert they're there
    mess = comm.messages.listl()
    for i, m in enumerate(message_types):
        ipst = f"ipppssoo{i}"
        assert f"{m}-{ipst}" in mess

    return ipppssoots, message_types


def setup_ingest_messages(comm):
    """adds a few extra ingested messages to the diverse messages list"""
    ipppssoots, message_types = setup_diverse_messages(comm)
    n = len(ipppssoots)

    # insert the extra ingested messages
    for i in range(3):
        ipst = f"ipppssoo{i+n}"
        comm.messages.put(f"ingested-{ipst}")
        ipppssoots.append(ipst)
        message_types.append("ingested")

    # read all messages back and assert they match the lists
    mess = comm.messages.listl()
    for i, m in enumerate(message_types):
        ipst = f"ipppssoo{i}"
        assert f"{m}-{ipst}" in mess
    print(ipppssoots)
    print(message_types)
    return ipppssoots, message_types


def get_broadcast_payload(comm):
    """from a list of messages, find the one broadcast and pull it's payload"""
    # first find the broadcast
    mess = comm.messages.listl()
    found_broadcast = False
    for i, m in enumerate(mess):
        if "broadcast-" in m:
            found_broadcast = True
            break
    # error if the broadcast message wasn't posted
    assert found_broadcast

    # pull the payload
    broadcast_payload = comm.messages.get(mess[i])
    return broadcast_payload


def test_clean_all_empty(s3_client):
    """tests clean-all on an otherwise empty messages directory"""
    # ensure we have an empty messages directory
    comm = io.get_io_bundle()
    assert_empty_messages(comm)

    # place a clean-all message
    comm.messages.put("clean-all")
    mess = comm.messages.listl()
    assert "clean-all" in mess

    # check behavior of clean-all on empty messages prefix
    all_event = conftest.load_event("clean-event-all.yaml")
    with pytest.raises(AssertionError):
        # broadcast assert a non-empty list
        clean_handler.lambda_handler(all_event, {})
    mess = comm.messages.listl()
    # no more messages
    assert_empty_messages(comm)


def test_clean_all_ipsts(s3_client):
    """tests clean-all with ipppssoots present
    only tests that the proper broadcast message is sent.
    Actual cleaning is tested in a different unit test"""

    # ensure we have an empty messages directory
    comm = io.get_io_bundle()
    ipppssoots, _ = setup_diverse_messages(comm)

    # insert the clean-all
    comm.messages.put("clean-all")

    # run the lambda
    all_event = conftest.load_event("clean-event-all.yaml")
    clean_handler.lambda_handler(all_event, {})

    # make sure clean cleaned up after itself
    mess = comm.messages.listl()
    assert "clean-all" not in mess

    # there should now be a broadcast message with the clean messages as it's payload
    broadcast_payload = get_broadcast_payload(comm)
    # assert that each ipppssoot has a clean-ipppssoot message in the broadcast payload
    for ipst in ipppssoots:
        assert f"clean-{ipst}" in broadcast_payload["messages"]


def test_clean_ingested_empty(s3_client):
    """tests clean-ingested with an otherwise empty messages directory"""
    # ensure we have an empty messages directory
    comm = io.get_io_bundle()
    assert_empty_messages(comm)

    # place a clean-ingested message
    comm.messages.put("clean-ingested")
    mess = comm.messages.listl()
    assert "clean-ingested" in mess

    # check behavior of clean-all on empty messages prefix
    all_event = conftest.load_event("clean-event-ingested.yaml")
    with pytest.raises(AssertionError):
        # broadcast assert a non-empty list
        clean_handler.lambda_handler(all_event, {})
    mess = comm.messages.listl()
    # no more messages
    assert_empty_messages(comm)


def test_clean_ingested_ipsts(s3_client):
    """similar to test_clean_all_ipsts but only the ingested ipppssoot should get into the broadcast payload"""

    comm = io.get_io_bundle()
    ipppssoots, message_types = setup_ingest_messages(comm)

    # count the ingested for validation later
    ingested_ctr = sum("ingested" in mt for mt in message_types)

    # insert the clean-ingested
    comm.messages.put("clean-ingested")

    # run the lambda
    all_event = conftest.load_event("clean-event-ingested.yaml")
    clean_handler.lambda_handler(all_event, {})

    # there should now be a broadcast message with the clean messages as it's payload
    broadcast_payload = get_broadcast_payload(comm)
    # check the number in the payload matches the number of messages we posted
    payload_ctr = sum("clean" in mess for mess in broadcast_payload["messages"])
    assert payload_ctr == ingested_ctr
    # assert that only ingested ipppssoots are covered in the broadcast payload
    for i, ipst in enumerate(ipppssoots):
        if "ingested" in message_types[i]:
            assert f"clean-{ipst}" in broadcast_payload["messages"]
        else:
            # since we counted the messages and the payload, there can't be spurious messages in the broadcast payload
            assert f"clean-{ipst}" not in broadcast_payload["messages"]
