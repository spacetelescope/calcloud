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

import os

from calcloud import io
from calcloud import exit_codes


def lambda_handler(event, context):
    print(event)

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

    continuation_msg = "error-" + dataset

    if exit_codes.is_memory_error(exit_code) or container_reason.startswith("OutOfMemoryError: Container killed"):
        if not metadata["terminated"] and metadata["memory_retries"] < int(os.environ["MAX_MEMORY_RETRIES"]):
            metadata["memory_retries"] += 1
            continuation_msg = "rescue-" + dataset
            print("Automatic OutOfMemory rescue of", dataset, "with memory retry count", metadata["memory_retries"])
        else:
            print("Automatic OutOfMemory retries for", dataset, "exhausted at", metadata["memory_retries"])
    elif container_reason.startswith("CannotInspectContainer"):
        if not metadata["terminated"] and metadata["retries"] < int(os.environ["MAX_DOCKER_RETRIES"]):
            metadata["retries"] += 1
            continuation_msg = "rescue-" + dataset
            print("Automatic CannotInspectContainer rescue for", dataset, "with retry count", metadata["retries"])
        else:
            print("Automatic CannotInspectContainer retries for", dataset, "exhausted at", metadata["retries"])
    elif container_reason.startswith("DockerTimeoutError"):
        if not metadata["terminated"] and metadata["retries"] < int(os.environ["MAX_DOCKER_RETRIES"]):
            metadata["retries"] += 1
            continuation_msg = "rescue-" + dataset
            print("Automatic DockerTimeoutError rescue for", dataset, "with retry count", metadata["retries"])
        else:
            print("Automatic DockerTimeoutError retries for", dataset, "exhausted at", metadata["retries"])
    elif status_reason.startswith("Operator cancelled"):
        print("Operator cancelled job", job_id, "for", dataset, "no automatic retry.")
        continuation_msg = "terminated-" + dataset
    else:
        print("Failure for", dataset, "no automatic retry for", combined_reason)

    # XXXX Since retry count used in planning, control output must precede rescue message
    print(metadata)
    comm.xdata.put(dataset, metadata)
    comm.messages.delete("all-" + dataset)
    comm.messages.put(continuation_msg)
