from pathlib import Path
import os
import sys
import logging
import json

import pytest
import boto3
from moto import mock_s3, mock_batch, mock_iam
import yaml

# for logging to double-check we're getting fake credentials and not real ones
boto3.set_stream_logger("botocore.credentials", logging.DEBUG)

# add lambda paths for testing
sys.path.append(str(Path(__file__).resolve().parent.parent / "lambda/blackboard"))
sys.path.append(str(Path(__file__).resolve().parent.parent / "lambda/batch_events"))

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


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


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


class Struct(dict):
    """A dictionary which supports dotted access to members.  Can be initialized from JSON/YAML file or dict."""

    def __init__(self, filename_or_dict):
        if isinstance(filename_or_dict, str):
            if filename_or_dict.endswith((".yml", ".yaml", ".jsn", ".json")):
                d = yaml.safe_load(open(filename_or_dict))
            else:
                raise ValueError("filename_or_dict should be a string specifying a .json or .yaml file.")
        else:
            d = filename_or_dict
        super().__init__(self._from_dict(d))

    def _from_dict(self, d):
        result = {}
        for key, val in d.items():
            if isinstance(val, dict):
                result[key] = Struct(val)
            else:
                result[key] = val
        return result

    def _to_dict(self):
        result = {}
        for key, val in self.items():
            if isinstance(val, Struct):
                result[key] = val._to_dict()
            else:
                result[key] = val
        return result

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, val):
        self[name] = val

    def __repr__(self):
        return yaml.dump(self._to_dict())

    def save(self, filename):
        with open(filename, "w+") as file:
            file.write(self)


def load_event(basename):
    return Struct(f"{EVENT_DIR}/{basename}")
