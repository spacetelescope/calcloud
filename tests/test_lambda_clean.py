import copy
import os

import pytest

from . import conftest
from . import common

from calcloud import io
from calcloud import s3

import clean_handler


def assert_all_artifacts(comm, datasets):
    """checks that all inputs/outputs/messages (ingested only) and control files exit only for the list of datasets provided"""
    # control
    xdata = comm.xdata.listl()
    assert sorted(xdata) == sorted(datasets)

    # messages
    expected_messages = [f"ingested-{dataset}" for dataset in datasets]
    actual_messages = comm.messages.listl()
    assert sorted(actual_messages) == sorted(expected_messages)

    # inputs
    expected_inputs = [f"{dataset}.tar.gz" for dataset in datasets]
    actual_inputs = comm.inputs.listl()
    assert sorted(actual_inputs) == sorted(expected_inputs)

    # outputs
    actual_outputs = comm.outputs.listl()
    expected_outputs = []
    for dataset in datasets:
        expected_outputs.append(f"{dataset}/{dataset}.tar.gz")
        expected_outputs.append(f"{dataset}/{dataset}.txt")
    assert sorted(actual_outputs) == sorted(expected_outputs)


def test_clean_all_empty(s3_client):
    """tests clean-all on an otherwise empty messages directory"""
    # ensure we have an empty messages directory
    comm = io.get_io_bundle()
    common.assert_empty_messages(comm)

    # place a clean-all message
    comm.messages.put("clean-all")
    mess = comm.messages.listl()
    assert "clean-all" in mess

    # check behavior of clean-all on empty messages prefix
    all_event = conftest.get_message_event("clean-all")
    with pytest.raises(AssertionError):
        # broadcast assert a non-empty list
        clean_handler.lambda_handler(all_event, {})
    mess = comm.messages.listl()
    # no more messages
    common.assert_empty_messages(comm)


def test_clean_all_datasets(s3_client):
    """tests clean-all with datasets present
    only tests that the proper broadcast message is sent.
    Actual cleaning is tested in a different unit test"""

    # ensure we have an empty messages directory
    comm = io.get_io_bundle()
    datasets, _ = common.setup_diverse_messages(comm)

    # insert the clean-all
    comm.messages.put("clean-all")

    # run the lambda
    all_event = conftest.get_message_event("clean-all")
    clean_handler.lambda_handler(all_event, {})

    # make sure clean cleaned up after itself
    mess = comm.messages.listl()
    assert "clean-all" not in mess

    # there should now be a broadcast message with the clean messages as it's payload
    broadcast = conftest.get_broadcast(comm)
    # assert that each dataset has a clean-dataset message in the broadcast payload
    for dataset in datasets:
        assert f"clean-{dataset}" in broadcast["messages"]


def test_clean_ingested_empty(s3_client):
    """tests clean-ingested with an otherwise empty messages directory"""
    # ensure we have an empty messages directory
    comm = io.get_io_bundle()
    common.assert_empty_messages(comm)

    # place a clean-ingested message
    comm.messages.put("clean-ingested")
    mess = comm.messages.listl()
    assert "clean-ingested" in mess

    # check behavior of clean-all on empty messages prefix
    all_event = conftest.get_message_event("clean-ingested")
    with pytest.raises(AssertionError):
        # broadcast assert a non-empty list
        clean_handler.lambda_handler(all_event, {})
    mess = comm.messages.listl()
    # no more messages
    common.assert_empty_messages(comm)


def test_clean_ingested_datasets(s3_client):
    """similar to test_clean_all_datasets but only the ingested dataset should get into the broadcast payload"""

    comm = io.get_io_bundle()
    datasets, message_types = common.setup_ingest_messages(comm)

    # count the ingested for validation later
    ingested_ctr = sum("ingested" in mt for mt in message_types)

    # insert the clean-ingested
    comm.messages.put("clean-ingested")

    # run the lambda
    all_event = conftest.get_message_event("clean-ingested")
    clean_handler.lambda_handler(all_event, {})

    # there should now be a broadcast message with the clean messages as it's payload
    broadcast = conftest.get_broadcast(comm)
    # check the number in the payload matches the number of messages we posted
    payload_ctr = sum("clean" in mess for mess in broadcast["messages"])
    assert payload_ctr == ingested_ctr
    # assert that only ingested datasets are covered in the broadcast payload
    for i, dataset in enumerate(datasets):
        if "ingested" in message_types[i]:
            assert f"clean-{dataset}" in broadcast["messages"]
        else:
            # since we counted the messages and the payload, there can't be spurious messages in the broadcast payload
            assert f"clean-{dataset}" not in broadcast["messages"]


def test_clean_single_dataset(s3_client):
    """in the end, via broadcasting each dataset to be cleaned must reach this test case individually"""

    comm = io.get_io_bundle()

    # place control, inputs, outputs, and messages objects for each dataset
    datasets = ["ipppssoo1", "ipppssoo2"]

    # setup the artifacts that need to be cleaned
    d = io.get_default_metadata()
    for i, dataset in enumerate(datasets):
        # control metadata object
        d["job_id"] = i
        comm.xdata.put(dataset, d)

        # empty inputs/outputs
        inputs_s3_path = f"s3://{os.environ['BUCKET']}/inputs/{dataset}.tar.gz"
        outputs_s3_tar = f"s3://{os.environ['BUCKET']}/outputs/{dataset}/{dataset}.tar.gz"
        outputs_s3_log = f"s3://{os.environ['BUCKET']}/outputs/{dataset}/{dataset}.txt"
        s = ""

        s3.put_object(s, inputs_s3_path, client=s3_client)
        s3.put_object(s, outputs_s3_tar, client=s3_client)
        s3.put_object(s, outputs_s3_log, client=s3_client)

        # messages
        comm.messages.put(f"ingested-{dataset}")

    # make sure the setup was all successful
    assert_all_artifacts(comm, datasets)
    # this list will be used in assert_all_artifacts
    assertion_datasets = copy.copy(datasets)
    # run the lambda on each dataset, verifying the state of the bucket after each call
    for dataset in datasets:
        dataset_event = conftest.get_message_event(f"clean-{dataset}")
        clean_handler.lambda_handler(dataset_event, {})
        assertion_datasets.remove(dataset)
        assert_all_artifacts(comm, assertion_datasets)
