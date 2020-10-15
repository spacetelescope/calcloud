"""This module supports submitting job plan tuples to AWS Batch for processing."""

import sys
import ast

import boto3

from . import provision

def submit_job(plan_tuple):
    """Given a job description `plan_tuple` from the planner,  submit a job to AWS batch."""
    info = provision.Plan(*plan_tuple)
    job = {
        "jobName": info.job_name,
        "jobQueue": info.job_queue,
        "jobDefinition": info.job_definition,
        "containerOverrides": {
            "vcpus": info.vcpus,
            "memory": info.memory,
            "command": [
                info.command,
                info.ipppssoot,
                info.input_path,
                info.s3_output_uri,
                info.crds_config
            ],
        },
        "timeout": {
            "attemptDurationSeconds": info.max_seconds,
        },
    }
    client = boto3.client("batch")
    return client.submit_job(**job)

def submit(ipppssoots, s3_output_bucket="s3://calcloud-hst-pipeline-outputs", batch_name="batch"):
    """Given a list of ipppssoots,  submit jobs so that all are processed by the batch
    system.

    Parameters
    ----------
    ipppssoots : list of str
        List of ipppssoot dataset names for processing
    s3_output_bucket : str
        AWS S3 bucket name in which outputs will be stored (in subdirecrtories)
    batch_name : str
        Identifying string for this submission.

    Returns
    -------
    List of JSON dicts returned by the Batch client submit_job() method.
    """
    plans = provision.get_plan_tuples(
        ipppssoots, s3_output_bucket, batch_name)
    jobs = [submit_job(p) for p in plans]
    return jobs

def submit_plans(plan_file):
    """Given a file `plan_file` defining job plan tuples one-per-line,
    submit each job and output the plan and submission response to stdout.
    Plans are generated by the calcloud.plan module.
    """
    if plan_file == "-":
        f = sys.stdin
    else:
        f = open(plan_file)
    for line in f.readlines():
        job_plan = ast.literal_eval(line)
        print(submit_job(job_plan))

if __name__ == "__main__":
    if len(sys.argv) == 2:
        submit_plans(sys.argv[1])
    else:
        print("usage:  python -m calcloud.submit [<plan_file> | - ]", file=sys.stderr)
