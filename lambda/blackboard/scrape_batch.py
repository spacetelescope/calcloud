def lambda_handler(event, context):
    import boto3
    import os
    import tempfile
    from calcloud import batch
    from calcloud import common

    # various metadata definitions
    jobStatuses = ["FAILED", "SUBMITTED", "PENDING", "RUNNABLE", "STARTING", "RUNNING", "SUCCEEDED"]
    # these are the column names in the blackboardAWS table in the owl DB on-premise
    header_names = [
        "GlobalJobId",
        "SubmitDate",
        "JobStartDate",
        "CompletionDate",
        "JobDuration",
        "ImageSize",
        "JobState",
        "ExitCode",
        "ExitReason",
        "Dataset",
        "LogStream",
        "S3Path",
    ]

    # job queues need to be looped over separately
    queues = os.environ["JOBQUEUES"].split(",")
    # use a random tmp filename just in case there's ever a time where two lambdas end up running together
    # that won't matter for the snapshot, generally, but the tmp file could get wonky without unique filenames
    fd, temppath = tempfile.mkstemp()

    # some params that could be tuned over time
    default_timestamp = 0
    maxJobResults = 100

    # we need s3 to upload the snapshot, and storagegateway to refresh the cache
    s3 = boto3.client("s3", config=common.retry_config)

    with os.fdopen(fd, "w") as fout:
        # write the header
        out_str = "|".join(header_names) + "\n"
        fout.write(out_str)
        # must loop over job statuses and queues
        for q in queues:
            for jobStatus in jobStatuses:
                jobs_iterator = batch._list_jobs_iterator(q, jobStatus, PageSize=maxJobResults)

                for page in jobs_iterator:
                    jobs = page["jobSummaryList"]
                    print(f"handling {len(jobs)} jobs from {q} in {jobStatus} status...")
                    for j in jobs:
                        jobId = j["jobId"]

                        submitDate = int(j["createdAt"] / 1000.0)

                        jobStartDate = int(j.get("startedAt", default_timestamp) / 1000.0)
                        completionDate = int(j.get("startedAt", default_timestamp) / 1000.0)

                        jobDuration = int(completionDate - jobStartDate)
                        imageSize = 0
                        jobState = jobStatus

                        # if the job hasn't started container doesn't seem to be in the keys
                        container = j.get("container", {})
                        exitCode = container.get("exitCode", 0)
                        exitReason = container.get("reason", j.get("statusReason", "None"))

                        dataset = j["jobName"].split("-")[-1]

                        # getting the LogStream requires calling describe_jobs which is very slow.
                        # for the time being we provide a None value, in the hopes we can find
                        # a way to get it into the metadata in the future.
                        LogStream = "None"
                        # writing out the status of the job
                        s3Path = f"{os.environ['BUCKET']}/outputs/{dataset}/"
                        out_list = [
                            jobId,
                            submitDate,
                            jobStartDate,
                            completionDate,
                            jobDuration,
                            imageSize,
                            jobState,
                            exitCode,
                            exitReason,
                            dataset,
                            LogStream,
                            s3Path,
                        ]
                        fout.write("|".join(map(str, out_list)) + "\n")

    with open(temppath, "rb") as f:
        s3.upload_fileobj(f, os.environ["BUCKET"], "blackboard/blackboardAWS.snapshot")

    os.remove(temppath)

    return None
