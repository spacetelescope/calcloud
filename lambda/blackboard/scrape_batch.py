def lambda_handler(event, context):
    import boto3
    import os
    import uuid
    import datetime
    import time

    # print(event)

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

    tnew = time.time()

    s3 = boto3.client("s3")
    batch = boto3.client("batch")
    gateway = boto3.client("storagegateway")
    maxJobResults = 1000

    # somehow need to batch up the describe_jobs call

    jobIds = []
    with open(filename, "w") as fout:
        # write the header
        out_str = "|".join(header_names) + "\n"
        fout.write(out_str)
        # must loop over job statuses and queues
        for q in queues:
            for jobStatus in jobStatuses:
                # nextJobToken allows pagination of the list_jobs call. We initialize it with a dummy value
                nextJobToken = "0"
                # we will set nextJobToken to false when it is not returned by list_jobs anymore
                while nextJobToken:
                    if nextJobToken is not "0":
                        jobs = batch.list_jobs(
                            jobQueue=q, jobStatus=jobStatus, nextToken=nextJobToken, maxResults=maxJobResults
                        )
                    else:
                        jobs = batch.list_jobs(jobQueue=q, jobStatus=jobStatus, maxResults=maxJobResults)
                    nextJobToken = jobs.get("nextToken", False)

                    print(f"handling {len(jobs['jobSummaryList'])} jobs from {q} in {jobStatus} status...")
                    for j in jobs["jobSummaryList"]:
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

    with open(filename, "rb") as f:
        s3.upload_fileobj(f, os.environ["BUCKET"], "blackboard/blackboardAWS.snapshot")

    response = gateway.refresh_cache(FileShareARN=os.environ["FILESHARE"], FolderList=["/blackboard/"], Recursive=True)

    print(response)

    return None
