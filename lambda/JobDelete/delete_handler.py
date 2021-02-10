def lambda_handler(event, context):
    import boto3
    import os
    from botocore.config import Config

    def get_list_of_jobs(q, jobStatus, nextJobToken, maxJobResults = 100):
        if nextJobToken is not "0":
            jobs = batch.list_jobs(
                jobQueue=q, jobStatus=jobStatus, nextToken=nextJobToken, maxResults=maxJobResults
            )
        else:
            jobs = batch.list_jobs(jobQueue=q, jobStatus=jobStatus, maxResults=maxJobResults)
        nextJobToken = jobs.get("nextToken", False)
        return jobs, nextJobToken

    # we need some mitigation of potential API rate restrictions for the Batch API
    config = Config(
        retries = {
        'max_attempts': 100,
        'mode': 'adaptive'
        }
    )

    s3 = boto3.client("s3", config=config)
    batch = boto3.client("batch", config=config)

    cancelStates = ["RUNNING","SUBMITTED","PENDING","RUNNABLE","STARTING"]
    queues = os.environ["JOBQUEUES"].split(",")
    # these types of messages on any deleted ipppssoot will be deleted
    cleanup_messages = ['processing-', 'submit-', 'processed-', 'error-']
    # this will be the final state message for any deleted ipppssoot
    deleted_message = 'terminated-'

    print(event)

    # some generic variables we'll need
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    message = event['Records'][0]['s3']['object']['key']
    ipst = message.split('-')[-1]
    cancel_reason = f"operator posted {message} message"

    print(f"received {message}")

    # will be set if we hit a job to cancel, otherwise we won't enter the block to transition messages
    affected_dataset = False
    # list_jobs requires a queue and a state (otherwise it will only return running state)
    # so we really have no choice but a nested loop of some sort
    for q in queues:
        for jobStatus in cancelStates:
            # nextJobToken allows pagination of the list_jobs call. We initialize it with a dummy value
            nextJobToken = "0"
            # we will set nextJobToken to false when it is not returned by list_jobs anymore
            while nextJobToken:
                jobs, nextJobToken = get_list_of_jobs(q, jobStatus, nextJobToken)
                print(f"handling {len(jobs['jobSummaryList'])} jobs from {q} in {jobStatus} status...")

                for j in jobs["jobSummaryList"]:
                    jobId = j["jobId"]
                    # this makes pretty rigid assumptions about job name and will probably need to be modified in the future, i.e. when HAP comes to the cloud
                    dataset = j["jobName"].split("-")[-1]

                    if (dataset == ipst):
                        response = batch.terminate_job(jobId=jobId, reason=cancel_reason)
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


                        