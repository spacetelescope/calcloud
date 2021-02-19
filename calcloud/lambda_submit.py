""" This module stitches the plan/provision/submit process together in a way that doesn't require intermediate files to be written to disk. 
This is intended for use in an AWS Lambda function where there is no user potentially intervening in each step """

from . import plan
from . import provision
from . import submit

from . import io

import os

# bucket name will need to be env variable?
def main(ipppssoots_file, bucket_name=os.environ["S3_PROCESSING_BUCKET"]):

    messages = io.get_message_api(bucket_name)
    control = io.get_control_api(bucket_name)

    bucket = f"s3://{bucket_name}"
    input_path = f"{bucket}/inputs"

    for ipppssoot in open(ipppssoots_file).read().split():

        ipppssoot = ipppssoot.lower()

        try:
            ctrl_msg = control.get(ipppssoot)
        except control.client.exceptions.NoSuchKey:
            ctrl_msg = dict()

        # memory_retries is incremented in the batch failure event if it's a memory fail
        if "memory_retries" not in ctrl_msg:
            ctrl_msg["memory_retries"] = 0

        resources = plan.get_resources(ipppssoot, bucket, input_path, ctrl_msg["memory_retries"])

        provisioned = provision.get_plan(resources)

        try:
            response = submit.submit_job(provisioned)
            ctrl_msg["job_id"] = response["jobId"]
        except Exception as e:
            print(e)
            continue

        control.put(ipppssoot, ctrl_msg)
        messages.move("placed-" + ipppssoot, "submit-" + ipppssoot)
