from pathlib import Path
import os
import sys
import logging

import pytest
import boto3
from moto import mock_s3, mock_batch, mock_iam

# for logging to double-check we're getting fake credentials and not real ones
boto3.set_stream_logger('botocore.credentials', logging.DEBUG)

# add lambda paths for testing
blackboard_path = Path(__file__).resolve().parent.parent / "lambda/blackboard"
sys.path.append(str(blackboard_path))

JOBDEFINITIONS = ["calcloud-jobdef-2g","calcloud-jobdef-8g","calcloud_jobdef-16g","calcloud-jobdef-64g"]
CENVIRONMENTS = ["calcloud-cenv-2g","calcloud-cenv-8g","calcloud-cenv-16g","calcloud-cenv-64g"]
JOBQUEUES = ["calcloud-jobqueue-2g","calcloud-jobqueue-8g","calcloud-jobqueue-16g","calcloud-jobqueue-64g"]
BUCKET="calcloud-processing-moto"
artifact_path = Path(__file__).resolve().parent / "test_artifacts"

os.environ["JOBDEFINITIONS"] = ",".join(JOBDEFINITIONS)
os.environ["JOBQUEUES"] = ",".join(JOBQUEUES)
os.environ["BUCKET"] = BUCKET

@pytest.fixture(scope='function')
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'

@pytest.fixture(scope='function')
def s3_client(aws_credentials):
    with mock_s3():
        yield boto3.client('s3', region_name='us-east-1')

@pytest.fixture(scope='function')
def batch_client(aws_credentials):
    with mock_batch():
        yield boto3.client('batch', region_name='us-east-1')

@pytest.fixture(scope='function')
def iam_client(aws_credentials):
    with mock_iam():
        yield boto3.client('iam', region_name='us-east-1')




