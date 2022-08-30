import time

from . import conftest

from calcloud import batch

jobStatuses = batch.JOB_STATUSES


def test_batch_mock(batch_client, s3_client, iam_client):
    """Tests the functions in calcloud/batch.py"""

    # setup batch and submit a job to each queue
    q_arns, jobdef_arns = conftest.setup_batch(iam_client, batch_client, busybox_sleep_timer=30)

    jobIds = []
    ipppssoots = []
    queues = []
    for i, (job_q_arn, job_definition_arn) in enumerate(zip(q_arns, jobdef_arns)):
        ipst = f"ipppssoo{i}"
        response = batch_client.submit_job(jobName=ipst, jobQueue=job_q_arn, jobDefinition=job_definition_arn)
        job_id = response["jobId"]
        queue = job_q_arn.split("/")[1]
        jobIds.append(job_id)
        ipppssoots.append(ipst)
        queues.append(queue)

    # create a dict of submitted jobs to make variable names easier to interpret
    submitted_jobs = {"jobNames": ipppssoots, "jobIds": jobIds, "queues": queues}

    # check that the queues from batch.get_queues is the same as those set up by conftest.setup_batch
    returned_queues = batch.get_queues()
    submitted_queues = submitted_jobs["queues"]
    assert sorted(returned_queues) == sorted(submitted_queues)

    # check that batch._list_jobs_iterator returns one job per queue
    for i, q in enumerate(queues):
        n_jobs_in_queue = 0
        for jobStatus in jobStatuses:
            jobs_iterator = batch._list_jobs_iterator(q, jobStatus)
            for page in jobs_iterator:
                n_jobs_in_queue += len(page["jobSummaryList"])
        assert n_jobs_in_queue == 1
        # To Check: What if a job changes status during the test (e.g. from SUBMITTED to RUNNABLE)?

    # check that job_ids from batch.get_job_ids match those submitted
    returned_job_ids = batch.get_job_ids()
    returned_job_ids = [job_id.replace("_", "-") for job_id in returned_job_ids]  # deal with the '-' to '_' hack
    assert sorted(returned_job_ids) == sorted(submitted_jobs["jobIds"])

    # check that batch.describe_job returns the correct jobName for a given jobId
    test_jobId = submitted_jobs["jobIds"][0]
    test_jobName = submitted_jobs["jobNames"][0]
    response = batch.describe_job(test_jobId)
    assert response["jobName"] == test_jobName

    # check that batch.describe_jobs returns the correct jobNames
    description = batch.describe_jobs(submitted_jobs["jobIds"])
    for i in range(len(description)):
        assert description[i]["jobName"] == submitted_jobs["jobNames"][i]

    # check that batch.get_job_name returns the correct jobName
    test_jobId = submitted_jobs["jobIds"][0]
    test_jobName = submitted_jobs["jobNames"][0]
    response_jobName = batch.get_job_name(test_jobId)
    assert response_jobName == test_jobName

    # check that batch.describe_jobs_of_queue returns the correct jobs
    for i, q in enumerate(submitted_jobs["queues"]):
        descriptions = batch.describe_jobs_of_queue(q)
        assert descriptions[0]["jobId"] == submitted_jobs["jobIds"][i]

    # check that batch.terminate_job actualy terminates the job, run this last
    cancel_jobId = submitted_jobs["jobIds"][0]
    batch.terminate_job(cancel_jobId, "Operator cancelled")
    time.sleep(10)  # wait a while for job to stop
    description = batch.describe_job(cancel_jobId)
    assert description["status"] == "FAILED"
