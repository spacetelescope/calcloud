def lambda_handler(event, context):
    import boto3
    import os
    from calcloud import batch
    from calcloud import common
    from calcloud import io

    # these types of messages on any deleted ipppssoot will be deleted
    cleanup_messages = ["processing-", "submit-", "processed-", "error-"]
    # these Batch job status states are cancellable
    cancelStates = ["RUNNING", "SUBMITTED", "PENDING", "RUNNABLE", "STARTING"]
    local_batch_client = boto3.client("batch", config=common.retry_config)
    queues = os.environ["JOBQUEUES"].split(",")
    maxJobResults = 100

    print(event)

    # some generic variables we'll need
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    message = event["Records"][0]["s3"]["object"]["key"]
    ipst = message.split("-")[-1]
    cancel_reason = f"operator posted {message} message"

    print(f"received {message}")

    comm = io.get_io_bundle(bucket_name)

    # will be set if we hit a job to cancel, otherwise we won't enter the block to transition messages
    affected_dataset = False
    # because we have to individually loop over states while jobs are moving through them,
    # sometimes they transition while we're doing something else and we miss them.
    # so in the cancel-all state we'll loop over the states a few times as a crude failsafe
    if ipst == "all":
        cancelStates *= 3
    # list_jobs requires a queue and a state (otherwise it will only return running state)
    # so we really have no choice but a nested loop
    for q in queues:
        for jobStatus in cancelStates:
            jobs_iterator = batch._list_jobs_iterator(q, jobStatus, PageSize=maxJobResults)
            for page in jobs_iterator:
                jobs = page["jobSummaryList"]
                print(f"handling {len(jobs)} jobs from {q} in {jobStatus} status...")
                for j in jobs:
                    jobId = j["jobId"]
                    # this makes pretty rigid assumptions about job name and will probably need to be modified in the future, i.e. when HAP comes to the cloud
                    dataset = j["jobName"].split("-")[-1]

                    if dataset == ipst:
                        response = local_batch_client.terminate_job(jobId=jobId, reason=cancel_reason)
                        print(response)
                        print(
                            f"terminate response: {response['ResponseMetadata']['HTTPStatusCode']}: {jobId} - {dataset}"
                        )
                        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                            affected_dataset = dataset
                    elif ipst == "all":
                        comm.messages.put(f"cancel-{dataset}")

    if affected_dataset:
        for cm in cleanup_messages:
            comm.messages.delete(f"{cm}-{affected_dataset}")
        comm.messages.put(f"terminated-{affected_dataset}")
        comm.messages.delete(f"cancel-{affected_dataset}")
