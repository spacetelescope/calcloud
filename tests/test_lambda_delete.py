import time

import pytest

from . import conftest

from calcloud import io
from calcloud import batch

import delete_handler


def test_cancel_all(batch_client, s3_client, iam_client):
    """cancel all simply posts a broadcast message"""

    comm = io.get_io_bundle()

    # setup batch and submit a job to each queue
    q_arns, jobdef_arns = conftest.setup_batch(iam_client, batch_client, busybox_sleep_timer=10)

    jobIds = []
    for i, (job_q_arn, job_definition_arn) in enumerate(zip(q_arns, jobdef_arns)):
        response = batch_client.submit_job(jobName=f"ipst_{i}", jobQueue=job_q_arn, jobDefinition=job_definition_arn)
        jobIds.append(response["jobId"].replace("-", "_"))

    # post the message (to ensure the message is removed by the lambda)
    comm.messages.put("cancel-all")

    # modify generic event to cancel-all
    event = conftest.load_event("generic-message-event.yaml")
    event = conftest.modify_generic_message(event, "cancel-all")

    # run the lambda
    delete_handler.lambda_handler(event, {})

    messages = comm.messages.listl()
    # the lambda should delete the message it triggered from
    assert "cancel-all" not in messages

    # get the broadcast messages
    broadcast = conftest.get_broadcast(comm)
    expected = [f"cancel-{jobid}" for jobid in jobIds]

    assert sorted(broadcast["messages"]) == sorted(expected)


def test_cancel_jobid_no_xdata(batch_client, s3_client, iam_client):
    """cancel-jobid actually terminates the job. This no_xdata version picks out an exception block in the lambda for testing"""

    comm = io.get_io_bundle()

    # setup batch and submit a job to each queue
    q_arns, jobdef_arns = conftest.setup_batch(iam_client, batch_client, busybox_sleep_timer=30)

    jobIds = []
    for i, (job_q_arn, job_definition_arn) in enumerate(zip(q_arns, jobdef_arns)):
        response = batch_client.submit_job(jobName=f"ipppssoo{i}", jobQueue=job_q_arn, jobDefinition=job_definition_arn)
        jobIds.append(response["jobId"].replace("-", "_"))

    # pick out the first job to cancel
    cancel_id = jobIds[0]
    jobIds.remove(cancel_id)

    # post the message
    comm.messages.put(f"cancel-{cancel_id}")

    # modify generic event to cancel-all
    event = conftest.load_event("generic-message-event.yaml")
    event = conftest.modify_generic_message(event, f"cancel-{cancel_id}")

    delete_handler.lambda_handler(event, {})

    # have to wait a short time for the job to actually stop
    time.sleep(5)
    job_ids = batch.get_job_ids()
    assert sorted(jobIds) == sorted(job_ids)
    assert cancel_id not in job_ids


def test_cancel_jobid(batch_client, s3_client, iam_client):
    """cancel-jobid actually terminates the job. This test includes metadata and other checks of that block of the lambda"""

    comm = io.get_io_bundle()

    # setup batch queues and ce's
    q_arns, jobdef_arns = conftest.setup_batch(iam_client, batch_client, busybox_sleep_timer=30)

    # submit a job to each queue and make a general control entry
    jobIds = []
    ipppssoots = []
    d = io.get_default_metadata()
    for i, (job_q_arn, job_definition_arn) in enumerate(zip(q_arns, jobdef_arns)):
        ipst = f"ipppssoo{i}"
        response = batch_client.submit_job(jobName=ipst, jobQueue=job_q_arn, jobDefinition=job_definition_arn)
        job_id = response["jobId"].replace("-", "_")
        jobIds.append(job_id)
        ipppssoots.append(ipst)

        d["job_id"] = job_id
        comm.xdata.put(ipst, d)

    # pick out the first job to cancel
    cancel_id = jobIds[0]
    cancel_ipst = ipppssoots[0]
    jobIds.remove(cancel_id)
    ipppssoots.remove(cancel_ipst)

    # post the message, and another to ensure deletion of all messages is working
    comm.messages.put(f"cancel-{cancel_id}")
    comm.messages.put(f"processing-{cancel_ipst}")

    # modify generic event to cancel-all
    event = conftest.load_event("generic-message-event.yaml")
    event = conftest.modify_generic_message(event, f"cancel-{cancel_id}")

    delete_handler.lambda_handler(event, {})

    # make sure the two messages are gone, and a terminated message appeared
    messages = comm.messages.listl()
    assert f"cancel-{cancel_id}" not in messages
    assert f"processing-{cancel_ipst}" not in messages
    assert f"terminated-{cancel_ipst}" in messages

    # check the control metadata for the terminated value
    cancelled_xdata = comm.xdata.get(cancel_ipst)
    assert cancelled_xdata["terminated"]

    # check the non-terminated jobs to ensure they're untouched
    for ipst in ipppssoots:
        xdata = comm.xdata.get(ipst)
        assert not xdata["terminated"]

    # have to wait a short time for the job to actually stop
    time.sleep(5)
    job_ids = batch.get_job_ids()
    assert sorted(jobIds) == sorted(job_ids)
    assert cancel_id not in job_ids


def test_cancel_ipst(batch_client, s3_client, iam_client):
    """cancel-ipppssoot actually terminates the job. This test includes metadata and other checks"""

    comm = io.get_io_bundle()

    # setup batch queues and ce's
    q_arns, jobdef_arns = conftest.setup_batch(iam_client, batch_client, busybox_sleep_timer=30)

    # submit a job to each queue and make a general control entry
    jobIds = []
    ipppssoots = []
    d = io.get_default_metadata()
    for i, (job_q_arn, job_definition_arn) in enumerate(zip(q_arns, jobdef_arns)):
        ipst = f"ipppssoo{i}"
        response = batch_client.submit_job(jobName=ipst, jobQueue=job_q_arn, jobDefinition=job_definition_arn)
        job_id = response["jobId"].replace("-", "_")
        jobIds.append(job_id)
        ipppssoots.append(ipst)

        d["job_id"] = job_id
        comm.xdata.put(ipst, d)

    # pick out the first job to cancel
    cancel_id = jobIds[0]
    cancel_ipst = ipppssoots[0]
    jobIds.remove(cancel_id)
    ipppssoots.remove(cancel_ipst)

    # post the message, and another to ensure deletion of all messages is working
    comm.messages.put(f"cancel-{cancel_ipst}")
    comm.messages.put(f"processing-{cancel_ipst}")

    # modify generic event to cancel-all
    event = conftest.load_event("generic-message-event.yaml")
    event = conftest.modify_generic_message(event, f"cancel-{cancel_ipst}")

    delete_handler.lambda_handler(event, {})

    # make sure the two messages are gone, and a terminated message appeared
    messages = comm.messages.listl()
    assert f"cancel-{cancel_id}" not in messages
    assert f"processing-{cancel_ipst}" not in messages
    assert f"terminated-{cancel_ipst}" in messages

    # check the control metadata for the terminated value
    cancelled_xdata = comm.xdata.get(cancel_ipst)
    assert cancelled_xdata["terminated"]

    # check the non-terminated jobs to ensure they're untouched
    for ipst in ipppssoots:
        xdata = comm.xdata.get(ipst)
        assert not xdata["terminated"]

    # have to wait a short time for the job to actually stop
    time.sleep(5)
    job_ids = batch.get_job_ids()
    assert sorted(jobIds) == sorted(job_ids)
    assert cancel_id not in job_ids


def test_bad_ipst(s3_client):
    # modify generic event to a bogus ipst
    event = conftest.load_event("generic-message-event.yaml")
    event = conftest.modify_generic_message(event, "cancel-345")

    with pytest.raises(ValueError):
        delete_handler.lambda_handler(event, {})
