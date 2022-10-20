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
    """
    assert_empty_messages(comm)

    # we'll make a message of each type for a unique list of datasets
    message_types = copy.copy(io.MESSAGE_TYPES)
    # ... except for broadcast and clean
    message_types.remove("broadcast")
    message_types.remove("clean")

    # insert the messages
    datasets = []
    for i, m in enumerate(message_types):
        dataset = f"ipppss{str(i).zfill(2)}t"
        datasets.append(dataset)
        comm.messages.put(f"{m}-{dataset}", payload=overrides)

    # read them back and assert they're there
    mess = comm.messages.listl()
    for i, m in enumerate(message_types):
        dataset = f"ipppss{str(i).zfill(2)}t"
        assert f"{m}-{dataset}" in mess

    return datasets, message_types


def setup_ingest_messages(comm, overrides={}):
    """adds a few extra ingested messages to the diverse messages list"""
    datasets, message_types = setup_diverse_messages(comm, overrides)
    n = len(datasets)

    # insert the extra ingested messages
    for i in range(3):
        dataset = f"ipppss{str(i+n).zfill(2)}t"
        comm.messages.put(f"ingested-{dataset}", payload=overrides)
        datasets.append(dataset)
        message_types.append("ingested")

    # read all messages back and assert they match the lists
    mess = comm.messages.listl()
    for i, m in enumerate(message_types):
        dataset = f"ipppss{str(i).zfill(2)}t"
        assert f"{m}-{dataset}" in mess
    return datasets, message_types


def setup_error_messages(comm, overrides={}):
    """adds a few extra error messages to the diverse messages list"""
    datasets, message_types = setup_diverse_messages(comm, overrides=overrides)
    n = len(datasets)

    # insert the extra error messages
    for i in range(3):
        dataset = f"ipppss{str(i+n).zfill(2)}t"
        comm.messages.put(f"error-{dataset}", payload=overrides)
        datasets.append(dataset)
        message_types.append("error")
        print("error", dataset, comm.messages.get(f"{'error'}-{dataset}"))

    # read all messages back and assert they match the lists
    mess = comm.messages.listl()
    for i, m in enumerate(message_types):
        dataset = f"ipppss{str(i).zfill(2)}t"
        assert f"{m}-{dataset}" in mess
    return datasets, message_types
