def lambda_handler(event, context):
    import boto3
    import os
    from calcloud import batch
    from calcloud import common

    s3 = boto3.client("s3", config=common.retry_config)
    local_batch_client = boto3.client("batch", config=common.retry_config)
    cancelStates = ["RUNNING","SUBMITTED","PENDING","RUNNABLE","STARTING"]
    queues = os.environ["JOBQUEUES"].split(",")
    # these types of messages on any deleted ipppssoot will be deleted
    cleanup_messages = ['processing-', 'submit-', 'processed-', 'error-']
    # this will be the final state message for any deleted ipppssoot
    deleted_message = 'terminated-'
    maxJobResults = 100

    print(event)

    # some generic variables we'll need
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    message = event['Records'][0]['s3']['object']['key']
    ipst = message.split('-')[-1]
    cancel_reason = f"operator posted {message} message"

    print(f"received {message}")

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

                    if (dataset == ipst):
                        response = local_batch_client.terminate_job(jobId=jobId, reason=cancel_reason)
                        print(response)
                        print(f"terminate response: {response['ResponseMetadata']['HTTPStatusCode']}: {jobId} - {dataset}")
                        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                            affected_dataset = dataset
                    elif (ipst == 'all'):
                        new_cancel_message = f"/tmp/cancel-{dataset}"
                        # upload_fileobj doesn't accept a write buffer, so we have to write and then open as read to upload
                        # probably a better way to do this
                        with open(new_cancel_message, "wb") as f:
                            pass
                        with open(new_cancel_message, "rb") as f:
                            s3.upload_fileobj(f, bucket_name, f"messages/cancel-{dataset}")
                        os.remove(new_cancel_message)

    if affected_dataset:
        # cleanup other now-unwanted messages
        for cm in cleanup_messages:
            cleanup_message = f"messages/{cm}{affected_dataset}"
            s3.delete_object(Bucket=bucket_name, Key=cleanup_message)

        # post final state message
        tmp_message_name = f"/tmp/{deleted_message}{affected_dataset}"
        with open(tmp_message_name, "wb") as f:
            pass
        with open(tmp_message_name, "rb") as f:
            s3.upload_fileobj(f, bucket_name, f"messages/{deleted_message}{affected_dataset}")
        os.remove(tmp_message_name)

    # clean up the cancel message
    s3.delete_object(Bucket=bucket_name, Key=message)


                        