def lambda_handler(event, context):
    import boto3
    import os
    import uuid
    import datetime

    print(event)

    # various metadata definitions
    inst_map = {"i": "wfc3", "j": "acs", "o": "stis", "l": "cos"}
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

    queues = os.environ["JOBQUEUES"].split(",")

    filename = f"/tmp/{str(uuid.uuid4())}"

    default_timestamp = 0

    s3 = boto3.client("s3")
    client = boto3.client("batch")
    with open(filename, "w") as fout:
        # write the header
        out_str = "|".join(header_names) + "\n"
        fout.write(out_str)
        # must loop over job statuses and queues
        for jobStatus in jobStatuses:
            for q in queues:
                jobs = client.list_jobs(jobQueue=q, jobStatus=jobStatus)
                for j in jobs["jobSummaryList"]:
                    print(j)  # gets it into cloudWatch; remove later
                    job_keys = j.keys()

                    jobId = j["jobId"]
                    job_meta = client.describe_jobs(
                        jobs=[
                            jobId,
                        ]
                    )  # max of 100 jobs here so we'll just have to do one at a time I guess
                    print(job_meta)  # gets it into cloudWatch; remove later

                    # submitDate = datetime.datetime.fromtimestamp(int(j['createdAt']/1000.0))
                    # jobStartDate = datetime.datetime.fromtimestamp(int(j['startedAt']/1000.0))
                    # completionDate = datetime.datetime.fromtimestamp(int(j['stoppedAt']/1000.0))
                    submitDate = int(j["createdAt"] / 1000.0)

                    # if the job hasn't started the start/stop keys won't exist.
                    if "startedAt" in job_keys:
                        jobStartDate = int(j["startedAt"] / 1000.0)
                    else:
                        jobStartDate = default_timestamp
                    if "stoppedAt" in job_keys:
                        completionDate = int(j["stoppedAt"] / 1000.0)
                    else:
                        completionDate = default_timestamp

                    jobDuration = int(completionDate - jobStartDate)
                    imageSize = 0
                    jobState = jobStatus

                    # if the job hasn't started container doesn't seem to be in the keys
                    if "container" in job_keys:
                        exitCode = j["container"]["exitCode"]
                        # presumably if the job hasn't exited the reason is not in the container object either
                        if "reason" in j["container"].keys():
                            exitReason = j["container"]["reason"]
                        else:
                            # if the user kills the job it goes here; good generic status reason
                            exitReason = j["statusReason"]
                    else:
                        # exit code is 0 when job hasn't started
                        exitCode = 0
                        exitReason = j["statusReason"]

                    dataset = j["jobName"].split("-")[-1]

                    # log stream isn't made until job is running
                    if "logStreamName" in job_meta["jobs"][0]["container"].keys():
                        LogStream = job_meta["jobs"][0]["container"]["logStreamName"]
                    else:
                        LogStream = "None"
                    s3Path = f"{job_meta['jobs'][0]['container']['command'][3]}"
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

    with open(filename, "rb") as f:
        s3.upload_fileobj(f, os.environ["BUCKET"], "blackboard/blackboardAWS.snapshot")

    return None
