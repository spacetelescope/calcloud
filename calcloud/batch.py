"""This module provides convenience functions for working with AWS Batch,
particularly pagination for the list and describe jobs functions which let
them act on job counts > 100 jobs.
"""
import argparse
import json
import datetime
import boto3
from . import common


JOB_STATUSES = tuple("SUBMITTED|PENDING|RUNNABLE|STARTING|RUNNING|SUCCEEDED|FAILED".split("|"))

DEFAULT_CLIENT = None


def get_default_client():
    global DEFAULT_CLIENT
    if DEFAULT_CLIENT is None:
        DEFAULT_CLIENT = boto3.client("batch", config=common.retry_config)
    return DEFAULT_CLIENT


def list_jobs(queue, collect_statuses=JOB_STATUSES, client=None):
    jobs = []
    for status in collect_statuses:
        jobs.extend(_list_jobs(queue, status, client))
    return jobs


def _list_jobs(queue, status, client=None):
    client = client or get_default_client()
    paginator = client.get_paginator("list_jobs")
    page_iterator = paginator.paginate(jobQueue=queue, jobStatus=status)
    jobs = []
    for page in page_iterator:
        jobs.extend(page["jobSummaryList"])
    return [_format_job_listing(job) for job in jobs]


def _list_jobs_iterator(queue, status, PageSize=10, client=None):
    client = client or get_default_client()
    paginator = client.get_paginator("list_jobs")
    return paginator.paginate(jobQueue=queue, jobStatus=status, PaginationConfig={"PageSize": PageSize})


def _format_job_listing(job):
    revised = dict(job)
    _format_seconds(revised, "createdAt")
    _format_seconds(revised, "startedAt")
    _format_seconds(revised, "stoppedAt")
    return revised


def _format_seconds(source, keyword):
    secs = source.get(keyword, 0) // 1000
    reformatted = datetime.datetime.fromtimestamp(secs).isoformat()
    reformatted = reformatted.split(".")[0]
    source[keyword] = reformatted


def describe_jobs_of_queue(queue, statuses=JOB_STATUSES):
    jobs = list_jobs(queue, statuses)
    job_names = [job["jobId"] for job in jobs]
    return describe_jobs(job_names)


def describe_jobs(job_names, client=None):
    client = client or get_default_client()
    descriptions = []
    for i in range(0, len(job_names), 100):
        block = client.describe_jobs(jobs=job_names[i : i + 100])
        descriptions.extend(block["jobs"])
    return descriptions


def _get_outputter(output_format):
    def func(results):
        if output_format == "json":
            print(json.dumps(results, sort_keys=True, indent=4, separators=(",", ": ")))
        else:
            raise NotImplementedError
            # print(yaml.dump(results))

    return func


def terminate(job_id, ipppssoot, reason=None, client=None):
    """Terminate Batch job `job_id` associated with `ipppsssoot` using Batch `client`.

    Return True IFF client.terminate_job() call terminates a job.
    """
    client = client or get_default_client()
    response = client.terminate_job(jobId=job_id, reason="batch.terminate called")
    print(response)
    print(f"terminate response: {response['ResponseMetadata']['HTTPStatusCode']}: {job_id} - {ipppssoot}")
    return response["ResponseMetadata"]["HTTPStatusCode"] == 200


def main(args=None):
    parser = argparse.ArgumentParser(description="Perform AWS Batch functions on arbitrary numbers of jobs, etc.")
    parser.add_argument("command", choices=("list-jobs", "describe-jobs"), help="Batch function to perform.")
    parser.add_argument(
        "--job-queue",
        dest="job_queue",
        type=str,
        default=None,
        help="Name of Batch queue to list or describe jobs for.",
    )
    parser.add_argument("--job-names", dest="job_names", type=list, default=None, help="Names of jobs to describe.")
    parser.add_argument(
        "--job-statuses",
        dest="job_statuses",
        nargs="+",
        default=JOB_STATUSES,
        help="Job statuses to list jobs for: SUBMITTED|PENDING|RUNNABLE|STARTING|RUNNING|SUCCEEDED|FAILED",
    )
    parser.add_argument(
        "--format", dest="format", choices=("json", "yaml"), default="json", help="Output format for results."
    )
    parsed = parser.parse_args(args)
    outputter = _get_outputter(parsed.format)
    if parsed.command == "list-jobs":
        outputter(list_jobs(parsed.job_queue))
    elif parsed.command == "describe-jobs":
        if parsed.job_names is not None:
            outputter(describe_jobs(parsed.job_names))
        elif parsed.job_queue is not None:
            outputter(describe_jobs_of_queue(parsed.job_queue, parsed.job_statuses))


if __name__ == "__main__":
    main()
