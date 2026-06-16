import argparse
import boto3
from dataclasses import dataclass
import datetime
import base64
from pathlib import Path

AMI_OWNER = "590529340912"


@dataclass
class Config:
    profile: str
    launch_template_id: str


CONFIG = {
    "sb": Config(
        profile="aws-hst-repro-sb-Developer",
        launch_template_id="lt-00ce80dd164671cf4",
    ),
    "dev": Config(
        profile="aws-hst-repro-dev-Developer",
        launch_template_id="lt-0b011d863b9e632ec",
    ),
    "test": Config(
        profile="aws-hst-repro-test-Developer",
        launch_template_id="lt-0fcb4c6dc67e968c0",
    ),
    "ops": Config(
        profile="aws-hst-repro-ops-Developer",
        launch_template_id="lt-0c20e3c04f8957c63",
    ),
}


@dataclass
class Ami:
    image_id: str
    name: str
    creation_date: datetime.datetime


def get_most_recent_ami_id(ec2_client):
    paginator = ec2_client.get_paginator("describe_images")

    amis = []

    for page in paginator.paginate(
        ExecutableUsers=["self"],  # Only AMIs shared with this account
        Owners=[AMI_OWNER],
        Filters=[{"Name": "name", "Values": ["STSCI-AMAZON-LINUX*"]}, {"Name": "state", "Values": ["available"]}],
    ):
        for image in page["Images"]:
            amis.append(
                Ami(image["ImageId"], image.get("Name"), datetime.datetime.fromisoformat(image["CreationDate"]))
            )

    return sorted(amis, key=lambda x: x.creation_date)[-1].image_id


def create_launch_template_version(ec2_client, launch_template_id, new_ami_id):
    with open(Path(__file__).resolve().parent / "resources" / "user_data.txt", "rb") as f:
        user_data_bytes = f.read()

    response = ec2_client.create_launch_template_version(
        LaunchTemplateId=launch_template_id,
        SourceVersion="283",  # Inherits from the current newest version
        LaunchTemplateData={
            "ImageId": new_ami_id,
            "BlockDeviceMappings": [
                {
                    "DeviceName": "/dev/xvda",
                    "Ebs": {
                        "Encrypted": True,
                        "DeleteOnTermination": True,
                        "Iops": 3000,
                        "VolumeType": "gp3",
                        "VolumeSize": 32,
                        "Throughput": 125,
                    },
                }
            ],
            "UserData": base64.b64encode(user_data_bytes).decode("utf-8"),
        },
    )
    if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        raise Exception(f"Unexpected response: {response}")


def create_ci_node(ec2_resource, launch_template_id):
    instances = ec2_resource.create_instances(
        LaunchTemplate={"LaunchTemplateId": launch_template_id, "Version": "$Latest"}, MinCount=1, MaxCount=1
    )
    if not instances:
        raise Exception(f"No instances created")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Launch a CI node with an updated AMI")
    parser.add_argument(
        "-e", "--environment", required=True, choices=["sb", "dev", "test", "ops"], help="Environment to use"
    )


def main():
    ARGS = parse_arguments()
    config = CONFIG[ARGS.environment]

    session = boto3.Session(profile_name=config.profile)
    ec2_client = session.client("ec2")
    ec2_resource = session.resource("ec2")

    new_ami_id = get_most_recent_ami_id(ec2_client)
    create_launch_template_version(ec2_client, config.launch_template_id, new_ami_id)
    create_ci_node(ec2_resource, config.launch_template_id)


if __name__ == "__main__":
    main()
