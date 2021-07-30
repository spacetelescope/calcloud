#! /usr/bin/python3

import os
import json
import sys

statuses = ['RUNNING','SUBMITTED','PENDING','RUNNABLE','STARTING']

# clean up before running
cmd = 'rm ./*.json'
os.system(cmd)

# dump the jobQueues to json
cmd = "awsudo $ADMIN_ARN aws batch describe-job-queues > queues.json"
os.system(cmd)

with open('./queues.json', 'r') as f:
    queues = json.load(f)

for queue in queues['jobQueues']:
    name = queue['jobQueueName']
    for status in statuses:
        cmd = f"awsudo $ADMIN_ARN aws batch list-jobs --job-queue {name} --job-status {status} > {name}_{status}.json"
        os.system(cmd)
        with open(f"{name}_{status}.json", 'r') as f:
            jobs = json.load(f)
            if len(jobs['jobSummaryList']) > 0:
                sys.exit(1)
            print(jobs)
    