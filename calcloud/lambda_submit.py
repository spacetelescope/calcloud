"""This module is the primary path for job submission,  for both initial "placed"
submissions and "rescue" submissions which are triggered by the corresponding
lambdas.

The key difference between "placed" and "rescue" submissions is that
rescue submissions track failure metadata in a control file,
e.g. retry count, while placed submissions clear all messages and
control data.

Another primary source of control information is the batch event
lambda which responds to CloudWatch failure events for Batch jobs.
For the first several retries, the fail event increments the retry
counter, stores other metadata, and triggers a rescue.  After a few
retries not documented here, the failure lambda stops attempting to
rescue.   This info is all stored in a control file.
"""

from . import plan
from . import submit
from . import io


def main(ipppssoot, bucket_name):

    comm = io.get_io_bundle(bucket_name)

    bucket = f"s3://{bucket_name}"
    input_path = f"{bucket}/inputs"

    ipppssoot = ipppssoot.lower()

    try:
        ctrl_msg = comm.metadata.get(ipppssoot)
    except comm.metadata.client.exceptions.NoSuchKey:
        ctrl_msg = dict()

    # memory_retries is incremented in the batch failure event if it's a memory fail
    if "memory_retries" not in ctrl_msg:
        ctrl_msg["memory_retries"] = 0

    p = plan.get_plan(ipppssoot, bucket, input_path, ctrl_msg["memory_retries"])

    print("Job Plan:", p)

    try:
        response = submit.submit_job(p)
        ctrl_msg["job_id"] = response["jobId"]
    except Exception as e:
        print(e)
        comm.messages.put("error-" + ipppssoot)
        return

    comm.metadata.put(ipppssoot, ctrl_msg)
    comm.messages.put("submit-" + ipppssoot)
