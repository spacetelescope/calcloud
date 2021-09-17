import os

import boto3

ec2 = boto3.client("ec2")


def lambda_handler(event, context):
    print(event)
    ec2.run_instances(
        LaunchTemplate={"LaunchTemplateName": os.environ["LAUNCH_TEMPLATE_NAME"]},
        MinCount=1,
        MaxCount=1,
        SubnetId=os.environ["SUBNET"],
    )
