"""This module exists because importing calcloud into conftest.py causes doctests to run and fail, 
and I don't know why. But it doesn't happen with this module."""

import copy

from calcloud import io


def assert_empty_messages(comm):
    messages = comm.messages.listl()
    assert len(messages) == 0


def setup_diverse_messages(comm, overrides={}):
    """posts messages of most types from io.MESSAGE_TYPES
    ignores broadcast and clean message types
    note (bhayden): I tried putting this function into conftest
    but importing calcloud.io caused pytest to run all of the doctests
    and fail miserably.
    For overrides, it's a dictionary of message_type: override
    for example: overrides={rescue: 'timeout_scale: 1.5'}"""
    assert_empty_messages(comm)

    # we'll make a message of each type for a unique list of ipppssoots
    message_types = copy.copy(io.MESSAGE_TYPES)
    # ... except for broadcast and clean
    message_types.remove("broadcast")
    message_types.remove("clean")

    # insert the messages
    ipppssoots = []
    for i, m in enumerate(message_types):
        ipst = f"ipppss{str(i).zfill(2)}t"
        ipppssoots.append(ipst)
        if m in overrides.keys():
            comm.messages.put(f"{m}-{ipst}", overrides[m])
        else:
            comm.messages.put(f"{m}-{ipst}")

    # read them back and assert they're there
    mess = comm.messages.listl()
    for i, m in enumerate(message_types):
        ipst = f"ipppss{str(i).zfill(2)}t"
        assert f"{m}-{ipst}" in mess

    return ipppssoots, message_types


def setup_ingest_messages(comm, overrides={}):
    """adds a few extra ingested messages to the diverse messages list"""
    ipppssoots, message_types = setup_diverse_messages(comm, overrides)
    n = len(ipppssoots)

    # insert the extra ingested messages
    for i in range(3):
        ipst = f"ipppss{str(i+n).zfill(2)}t"
        comm.messages.put(f"ingested-{ipst}")
        ipppssoots.append(ipst)
        message_types.append("ingested")

    # read all messages back and assert they match the lists
    mess = comm.messages.listl()
    for i, m in enumerate(message_types):
        ipst = f"ipppss{str(i).zfill(2)}t"
        assert f"{m}-{ipst}" in mess
    return ipppssoots, message_types


def setup_error_messages(comm, overrides={}):
    """adds a few extra error messages to the diverse messages list"""
    ipppssoots, message_types = setup_diverse_messages(comm, overrides)
    n = len(ipppssoots)

    # insert the extra error messages
    for i in range(3):
        ipst = f"ipppss{str(i+n).zfill(2)}t"
        comm.messages.put(f"error-{ipst}")
        ipppssoots.append(ipst)
        message_types.append("error")

    # read all messages back and assert they match the lists
    mess = comm.messages.listl()
    for i, m in enumerate(message_types):
        ipst = f"ipppss{str(i).zfill(2)}t"
        assert f"{m}-{ipst}" in mess
    return ipppssoots, message_types
