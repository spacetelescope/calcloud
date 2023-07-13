#! /usr/bin/python3

# the deploy_ami_rotate.sh script calls this script,
# and stops ami rotation before calling terraform
# if this script exits non-zero
# 06/12/2023 - copied and modified check_batch_jobs.py and removed ADMIN_ARN to be called by deploy_ami_rotate_codebuild_script.sh
#              hst-repro-codebuild-role should be used to run everything here
import os
import json
import sys

statuses = ["RUNNING", "SUBMITTED", "PENDING", "RUNNABLE", "STARTING"]

# clean up before running
cmd = "rm ./*.json"
os.system(cmd)

# dump the jobQueues to json
cmd = "aws batch describe-job-queues > queues.json"
os.system(cmd)

with open("./queues.json", "r") as f:
    queues = json.load(f)

for queue in queues["jobQueues"]:
    name = queue["jobQueueName"]
    for status in statuses:
        cmd = f"aws batch list-jobs --job-queue {name} --job-status {status} > {name}_{status}.json"
        print(cmd)
        os.system(cmd)
        with open(f"{name}_{status}.json", "r") as f:
            jobs = json.load(f)
            if len(jobs["jobSummaryList"]) > 0:
                sys.exit(1)
