from pathlib import Path
import os
import sys
import logging
import io
import zipfile

import pytest
import boto3
from moto import mock_s3, mock_batch, mock_iam, mock_ec2, mock_lambda, mock_dynamodb
import yaml

# for logging to double-check we're getting fake credentials and not real ones
boto3.set_stream_logger("botocore.credentials", logging.DEBUG)

# add lambda paths for testing
sys.path.append(str(Path(__file__).resolve().parent.parent / "lambda/blackboard"))
sys.path.append(str(Path(__file__).resolve().parent.parent / "lambda/batch_events"))
sys.path.append(str(Path(__file__).resolve().parent.parent / "lambda/AmiRotation"))
sys.path.append(str(Path(__file__).resolve().parent.parent / "lambda/JobClean"))
sys.path.append(str(Path(__file__).resolve().parent.parent / "lambda/JobDelete"))
sys.path.append(str(Path(__file__).resolve().parent.parent / "lambda/JobRescue"))
sys.path.append(str(Path(__file__).resolve().parent.parent / "lambda/broadcast"))


EVENT_DIR = str(Path(__file__).resolve().parent / "artifacts/events")

JOBDEFINITIONS = ["calcloud-jobdef-2g", "calcloud-jobdef-8g", "calcloud_jobdef-16g", "calcloud-jobdef-64g"]
CENVIRONMENTS = ["calcloud-cenv-2g", "calcloud-cenv-8g", "calcloud-cenv-16g", "calcloud-cenv-64g"]
JOBQUEUES = ["calcloud-jobqueue-2g", "calcloud-jobqueue-8g", "calcloud-jobqueue-16g", "calcloud-jobqueue-64g"]
BUCKET = "calcloud-processing-moto"

os.environ["JOBDEFINITIONS"] = ",".join(JOBDEFINITIONS)
os.environ["JOBQUEUES"] = ",".join(JOBQUEUES)
os.environ["BUCKET"] = BUCKET
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["MAX_MEMORY_RETRIES"] = "4"
os.environ["MAX_DOCKER_RETRIES"] = "4"
os.environ["LAUNCH_TEMPLATE_NAME"] = "test_launch_template"
os.environ["SUBMIT_TIMEOUT"] = "10"  # for timing out waiting for inputs to submit batch jobs
os.environ["JOBPREDICTLAMBDA"] = "job_predict_lambda"
os.environ["DDBTABLE"] = "mock_ddb_table"


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def s3_client(aws_credentials):
    with mock_s3():
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket=os.environ["BUCKET"])
        yield s3_client


@pytest.fixture(scope="function")
def batch_client(aws_credentials):
    with mock_batch():
        yield boto3.client("batch", region_name="us-east-1")


@pytest.fixture(scope="function")
def iam_client(aws_credentials):
    with mock_iam():
        yield boto3.client("iam", region_name="us-east-1")


@pytest.fixture(scope="function")
def ec2_client(aws_credentials):
    with mock_ec2():
        yield boto3.client("ec2", region_name="us-east-1")


@pytest.fixture(scope="function")
def ec2_resource(aws_credentials):
    with mock_ec2():
        yield boto3.resource("ec2", region_name="us-east-1")


@pytest.fixture(scope="function")
def lambda_client(aws_credentials):
    with mock_lambda():
        yield boto3.client("lambda", region_name="us-east-1")


@pytest.fixture(scope="function")
def dynamodb_client(aws_credentials):
    with mock_dynamodb():
        yield boto3.client("dynamodb", region_name="us-east-1")


def load_event(basename):
    with open(f"{EVENT_DIR}/{basename}") as file:
        return yaml.safe_load(file)


def setup_batch(iam_client, batch_client, busybox_sleep_timer=1):
    # we'll need a mock iam role to pass to the mock batch client
    iams = iam_client.create_role(
        RoleName="test_batch_client",
        AssumeRolePolicyDocument="string",
    )
    iam_arn = iams.get("Role").get("Arn")
    print("iamRoleArn: " + iam_arn)

    q_arns, jobdef_arns = [], []

    # mocks for each job ladder step
    for i, ce in enumerate(CENVIRONMENTS):
        created_cenv = batch_client.create_compute_environment(
            computeEnvironmentName=ce, type="UNMANAGED", serviceRole=iam_arn
        )

        compute_environment_arn = created_cenv.get("computeEnvironmentArn")

        created_queue = batch_client.create_job_queue(
            jobQueueName=JOBQUEUES[i],
            state="ENABLED",
            priority=1,
            computeEnvironmentOrder=[
                {"order": 1, "computeEnvironment": compute_environment_arn},
            ],
        )
        job_q_arn = created_queue.get("jobQueueArn")
        q_arns.append(job_q_arn)

        created_jobdef = batch_client.register_job_definition(
            jobDefinitionName=JOBDEFINITIONS[i],
            type="container",
            containerProperties={
                "image": "busybox",
                "vcpus": 1,
                "memory": 128,
                "command": ["sleep", f"{busybox_sleep_timer}"],
            },
        )
        job_definition_arn = created_jobdef.get("jobDefinitionArn")
        jobdef_arns.append(job_definition_arn)

    return q_arns, jobdef_arns


def modify_generic_message(event, message):
    event["Records"][0]["s3"]["object"]["key"] = f"messages/{message}"
    return event


def get_message_event(message):
    """uses the generic event generic-message-event.yaml to produce an s3 put event
    for the given message"""
    event = load_event("generic-message-event.yaml")
    return modify_generic_message(event, message)


def get_broadcast(comm):
    """from a list of messages, find the one broadcast and pull it's contents"""
    broadcast_message = find_broadcast_message(comm)
    # pull the payload
    broadcast = comm.messages.get(broadcast_message)
    return broadcast


def find_broadcast_message(comm):
    # first find the broadcast
    mess = comm.messages.listl()
    found_broadcast = False
    for i, m in enumerate(mess):
        if "broadcast-" in m:
            found_broadcast = True
            break
    # error if the broadcast message wasn't posted
    assert found_broadcast
    return mess[i]


def job_predict_mock_source_code(memBin=0, clockTime=10):
    code = f"""
import json
def lambda_handler(event, context):
    response = {{"memBin":{memBin}, "clockTime":{clockTime}, "memVal": 2}}
    return response
"""
    return code


def job_predict_zip(memBin=0, clockTime=3600):
    source_code = job_predict_mock_source_code(memBin=memBin, clockTime=clockTime)
    zip_io = io.BytesIO()
    zip_file = zipfile.ZipFile(zip_io, "w", zipfile.ZIP_DEFLATED)
    zip_file.writestr("lambda_function.py", source_code)
    zip_file.close()
    zip_io.seek(0)
    return zip_io.read()


def create_mock_lambda(lambda_client, iam_client, name=os.environ["JOBPREDICTLAMBDA"], memBin=0, clockTime=10):
    iams = iam_client.create_role(
        RoleName="test_lambda_role",
        AssumeRolePolicyDocument="string",
    )
    iam_arn = iams.get("Role").get("Arn")

    response = lambda_client.create_function(
        FunctionName=name,
        Runtime="python3.8",
        Role=iam_arn,
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": job_predict_zip(memBin=memBin, clockTime=clockTime)},
        Description="mocked job predict lambda",
        Timeout=30,
        MemorySize=128,
        Publish=True,
    )


def setup_dynamodb(ddb_client, name=os.environ["DDBTABLE"]):
    response = ddb_client.create_table(
        AttributeDefinitions=[
            {
                "AttributeName": "ipst",
                "AttributeType": "S",
            },
        ],
        KeySchema=[
            {
                "AttributeName": "ipst",
                "KeyType": "HASH",
            },
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
        TableName=name,
    )

    print(response)
