""" This module stitches the plan/provision/submit process together in a way that doesn't require intermediate files to be written to disk. 
This is intended for use in an AWS Lambda function where there is no user potentially intervening in each step """

from . import plan 
from . import provision
from . import submit
import os
import boto3

# bucket name will need to be env variable?
def main(ipppssoots_file, bucket_name=os.environ['S3_PROCESSING_BUCKET']):
    # reproduces plan.planner tuples that would normally be dumped to file
    with open(ipppssoots_file) as f:
        ipppssoots = [ipppssoot.lower() for ipppssoot in f.read().split()]
        
    bucket = f"s3://{bucket_name}"
    input_path = f"{bucket}/inputs"
    planned_resource_tuples = plan.get_resources_tuples(ipppssoots, bucket, input_path)

    # reproduces the printed output of provision
    provisioned_resource_tuples = provision.get_plan_tuples(planned_resource_tuples)
    
    s3_client = boto3.resource('s3')

    # submits the jobs
    for p in provisioned_resource_tuples:
        try:
            submit.submit_job(p)
        except Exception as e:
            print(e)
            continue
        
        # pass the message
        old_file_key = f'messages/placed-{p.ipppssoot}'
        new_file_key = f'messages/submit-{p.ipppssoot}'
        s3_client.Object(bucket_name,new_file_key).copy_from(CopySource=f"{bucket_name}/{old_file_key}")
        s3_client.Object(bucket_name,old_file_key).delete()