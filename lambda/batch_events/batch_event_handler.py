"""The batch event lambda currently processes failure events for AWS Batch
issued through CloudWatch.

Currently failure events are classified as "memory related" and "other" where
memory related failures results in automatic retries if:

1. The job control metadata does not indicate the job was terminated/cancelled.

2. The job control memory_retries count hasn't exceeded the maximum.

Job control data is updated with a new retry count and other information from
the Batch event.

All messages for the failed dataset are deleted.

A rescue message is sent to trigger the rescue lambda for qualifying
memory related failures, otherwise an error-dataset message is sent.
"""

import boto3
import os

from calcloud import io
from calcloud import exit_codes
from calcloud.log import configure_logging, lambda_logging

logger = configure_logging()


def get_caldp_log(job_id, dataset):
    batch = boto3.client("batch")
    logs = boto3.client("logs")

    # 1. Get the log stream name from AWS Batch
    response = batch.describe_jobs(jobs=[job_id])
    if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        logger.warning(f"describe_jobs failed for {job_id}, {dataset}, {response}")
        return None
    jobs = response["jobs"]
    if not jobs:
        logger.warning(f"No jobs found for {job_id}, {dataset}")
        return None

    log_stream = jobs[0].get("container", {}).get("logStreamName")

    if not log_stream:
        logger.warning(
            f"Log stream not available for dataset {dataset}, job {job_id} yet "
            "(job may still be pending or starting)"
        )
        return None

    # 2. Fetch all log events using forward pagination
    log_group = "/aws/batch/job"

    kwargs = {
        "logGroupName": log_group,
        "logStreamName": log_stream,
        "startFromHead": True,  # Read oldest logs first
    }

    lines = []
    while True:
        response = logs.get_log_events(**kwargs)
        if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
            logger.warning(
                f"get_log_events failed for log stream {log_stream} in log group {log_group}, "
                f"dataset {dataset}, {response}"
            )
            return None
        lines.extend(event["message"] for event in response["events"])

        # CloudWatch returns the same nextForwardToken when you reach the end of the stream
        next_token = response.get("nextForwardToken")
        if not next_token or next_token == kwargs.get("nextToken"):
            break

        kwargs["nextToken"] = next_token

    if lines:
        logger.info(f"Retrieved caldp log for dataset {dataset}")
    else:
        logger.warning(f"No caldp log found for dataset {dataset}")

    return "\n".join(lines)


@lambda_logging(lambda event: event["detail"]["container"]["command"][1])
def lambda_handler(event, context):
    logger.info(event)

    detail = event["detail"]
    job_id = detail["jobId"]
    job_name = detail["jobName"]  # appears to be dataset
    status_reason = detail.get("statusReason", "undefined")

    container = event["detail"]["container"]
    dataset = container["command"][1]
    bucket = container["command"][2].split("/")[2]
    container_reason = container.get("reason", "undefined")
    exit_code = container.get("exitCode", "undefined")
    exit_reason = exit_codes.explain(exit_code) if exit_code != "undefined" else exit_code

    comm = io.get_io_bundle(bucket)

    metadata = comm.xdata.get(dataset)
    metadata["dataset"] = dataset
    metadata["bucket"] = bucket
    metadata["job_id"] = job_id
    metadata["job_name"] = job_name
    metadata["exit_code"] = exit_code
    metadata["exit_reason"] = exit_reason
    metadata["status_reason"] = status_reason
    metadata["container_reason"] = container_reason

    if exit_reason != "undefined":
        combined_reason = exit_reason
    elif container_reason != "undefined":
        combined_reason = container_reason
    else:
        combined_reason = status_reason

    continuation_msg = "clouderror-" + dataset

    if exit_codes.is_memory_error(exit_code) or container_reason.startswith("OutOfMemoryError: Container killed"):
        if not metadata["terminated"] and metadata["memory_retries"] < int(os.environ["MAX_MEMORY_RETRIES"]):
            metadata["memory_retries"] += 1
            continuation_msg = "rescue-" + dataset
            logger.info(
                "Automatic OutOfMemory rescue of %s with memory retry count %s",
                dataset,
                metadata["memory_retries"],
            )
        else:
            logger.error("Automatic OutOfMemory retries for %s exhausted at %s", dataset, metadata["memory_retries"])
    elif container_reason.startswith("CannotInspectContainer"):
        if not metadata["terminated"] and metadata["retries"] < int(os.environ["MAX_DOCKER_RETRIES"]):
            metadata["retries"] += 1
            continuation_msg = "rescue-" + dataset
            logger.info(
                "Automatic CannotInspectContainer rescue for %s with retry count %s",
                dataset,
                metadata["retries"],
            )
        else:
            logger.error(
                "Automatic CannotInspectContainer retries for %s exhausted at %s",
                dataset,
                metadata["retries"],
            )
    elif container_reason.startswith("DockerTimeoutError"):
        if not metadata["terminated"] and metadata["retries"] < int(os.environ["MAX_DOCKER_RETRIES"]):
            metadata["retries"] += 1
            continuation_msg = "rescue-" + dataset
            logger.info(
                "Automatic DockerTimeoutError rescue for %s with retry count %s",
                dataset,
                metadata["retries"],
            )
        else:
            logger.error("Automatic DockerTimeoutError retries for %s exhausted at %s", dataset, metadata["retries"])
    elif status_reason.startswith("Operator cancelled"):
        logger.info("Operator cancelled job %s for %s no automatic retry.", job_id, dataset)
        continuation_msg = "terminated-" + dataset
    else:
        logger.error("Failure for %s no automatic retry for %s", dataset, combined_reason)

    if continuation_msg in (f"clouderror-{dataset}", f"terminated-{dataset}"):
        diagnostic = (
            f"Dataset: {dataset}\n"
            f"Batch job ID: {job_id}\n"
            f"Exit code: {exit_code}\n"
            f"Exit reason: {exit_reason}\n"
            f"Status reason: {status_reason}\n"
            f"Container reason: {container_reason}\n\n"
        )

        try:
            caldp_log = get_caldp_log(job_id, dataset)
        except Exception as exc:
            logger.exception(
                "Could not retrieve Batch logs for %s, job %s",
                dataset,
                job_id,
            )
            diagnostic += f"Batch log retrieval failed: {type(exc).__name__}: {exc}\n"
        else:
            diagnostic += caldp_log or "No Batch log content was available.\n"

        if continuation_msg == f"clouderror-{dataset}":
            # A cloud-error trigger promises that diagnostics exist.
            comm.outputs.put({f"{dataset}/caldp_{dataset}.log": diagnostic})
        else:
            try:
                comm.outputs.put({f"{dataset}/caldp_{dataset}.log": diagnostic})
            except Exception:
                logger.exception(
                    "Could not upload Batch diagnostics for %s",
                    dataset,
                )

    # XXXX Since retry count used in planning, control output must precede rescue message
    logger.info(metadata)
    comm.xdata.put(dataset, metadata)
    comm.messages.delete("all-" + dataset)
    comm.messages.put(continuation_msg)


if __name__ == "__main__":
    result = get_caldp_log("411b6722-d714-45ba-ad94-679595e7856e", "acs_cxx_01")
    a = 1
