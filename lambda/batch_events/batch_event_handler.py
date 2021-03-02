"""The batch event lambda currently processes failure events for AWS Batch
issued through CloudWatch.

Currently failure events are classified as "memory related" and "other" where
memory related failures results in automatic retries if:

1. The job control metadata does not indicate the job was terminated/cancelled.

2. The job control memory_retries count hasn't exceeded the maximum.

Job control data is updated with a new retry count and other information from
the Batch event.

All messages for the failed ipppssoot are deleted.

A rescue message is sent to trigger the rescue lambda for qualifying
memory related failures, otherwise an error-ipppssoot message is sent.
"""

import os

from calcloud import io


def lambda_handler(event, context):

    print(event)

    ipppssoot = event["detail"]["container"]["command"][1]
    bucket = event["detail"]["container"]["command"][2].split("/")[2]
    job_id = event["detail"]["jobId"]
    job_name = event["detail"]["jobName"]  # appears to be ipppssoot
    attempts = event["detail"]["attempts"]
    if attempts:
        fail_reason = attempts[0]["container"]["reason"]
    else:
        fail_reason = event["detail"]["statusReason"]

    comm = io.get_io_bundle(bucket)

    metadata = comm.xdata.get(ipppssoot)
    metadata["ipppssoot"] = ipppssoot
    metadata["bucket"] = bucket
    metadata["job_id"] = job_id
    metadata["job_name"] = job_name
    metadata["fail_reason"] = fail_reason

    continuation_msg = "error-" + ipppssoot
    if fail_reason.startswith("OutOfMemoryError:"):
        if not metadata["terminated"] and metadata["memory_retries"] < int(os.environ["MAX_MEMORY_RETRIES"]):
            print("Automatic rescue of", ipppssoot, "with memory retry count", metadata["memory_retries"])
            metadata["memory_retries"] += 1
            continuation_msg = "rescue-" + ipppssoot
        else:
            print("Automatic memory retries for", ipppssoot, "exhausted at", metadata["memory_retries"])
    else:
        print("Failure for", ipppssoot, "no automatic retry for", fail_reason)

    # XXXX Since retry count used in planning, control output must precede rescue message
    print(metadata)
    comm.xdata.put(ipppssoot, metadata)
    comm.messages.delete("all-" + ipppssoot)
    comm.messages.put(continuation_msg)
