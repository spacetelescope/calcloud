# TODO: add queue name to metadata
def lambda_handler(event, context):
    import boto3
    import os
    import tempfile
    from calcloud import batch
    from calcloud import common
    from calcloud import hst

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
                        print(j)
                        jobId = j["jobId"]

                        submitDate = int(j.get("createdAt", default_timestamp) / 1000.0)

                        jobStartDate = int(j.get("startedAt", default_timestamp) / 1000.0)
                        completionDate = int(j.get("stoppedAt", default_timestamp) / 1000.0)

                        # if the job hasn't completed yet, set duration to 0 so it's not -50 years
                        # we check for the stoppedAt attribute, and default to startDate
                        durationCheck = int(j.get("stoppedAt", j.get("startedAt", default_timestamp)) / 1000.0)
                        jobDuration = int(durationCheck - jobStartDate)

                        # imageSize currently not implemented. could be pulled from metrics file
                        imageSize = 0
                        jobState = jobStatus

                        # if the job hasn't started container doesn't seem to be in the keys
                        container = j.get("container", {})
                        exitCode = container.get("exitCode", 0)

                        containerReason = container.get("reason", "None")
                        jobReason = j.get("statusReason", "None")
                        if jobReason.startswith("Essential"):
                            exitReason = containerReason[:120] + "; " + jobReason[:120]
                        else:
                            exitReason = container.get("reason", j.get("statusReason", "None"))[:255]

                        # dataset = j["jobName"].split("-")[-1]
                        jobname = j["jobName"]
                        if hst.IPPPSSOOT_RE.match(jobname) or hst.SVM_RE.match(jobname) or hst.MVM_RE.match(jobname):
                            dataset = jobname
                        else:
                            splitname = "-".join(jobname.split("-")[1:])
                            if (
                                hst.IPPPSSOOT_RE.match(splitname)
                                or hst.SVM_RE.match(splitname)
                                or hst.MVM_RE.match(splitname)
                            ):
                                dataset = splitname
                            else:
                                raise Exception("No valid dataset name found in jobName")

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
                        line = "|".join(map(str, out_list)).replace("\n", " ")
                        fout.write(line + "\n")

    with open(temppath, "rb") as f:
        s3.upload_fileobj(f, os.environ["BUCKET"], "blackboard/blackboardAWS.snapshot")

    os.remove(temppath)

    return None
