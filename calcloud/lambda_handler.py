import json
import boto3
from datetime import datetime
import re

import warnings
warnings.warn("this lambda handler will be removed soon", DeprecationWarning, stacklevel=1)

DATASET_RE = re.compile(r"^[A-Za-z0-9\-\.]{1,128}$")

def lambda_handler(event, context):

    output_bucket = event.get("s3_output_bucket", "s3://calcloud-hst-pipeline-outputs")
    job_definition = event.get("job_definition", "calcloud-hst-caldp-job-definition")
    job_queue = event.get("calcloud-hst-queue", "calcloud-hst-queue")
    datasets = event.get("datasets")
    if isinstance(datasets, str):
        datasets = datasets.split()

    #Create the batch client
    client = boto3.client('batch')
    dateTimeObj = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    ## Submit the job
    for dataset in datasets:
        dataset = dataset.strip().lower()
        if not DATASET_RE.match(dataset):
            raise ValueError("Invalid dataset ID.")
        batch_name = "batch" + "-" + dateTimeObj
        job_name = batch_name + "-" + dataset
        s3_output_path = output_bucket + "/data/" + batch_name
        response = client.submit_job(
            jobDefinition=job_definition,
            jobName=job_name,
            jobQueue=job_queue,
            parameters = {'dataset': str(dataset), 's3_output_path': s3_output_path},
            timeout = {
                "attemptDurationSeconds": 60*60*6,  # 6 hours max -> kill
            },
        )
    batch_dict = dict(
        datasets=datasets, s3_output_path=s3_output_path, job_queue=job_queue,
        job_definition=job_definition)
    batch_json = json.dumps(batch_dict)
    batch_output = output_bucket + "/messages/batch-new/" + batch_name + ".json"
    put_object(batch_json, batch_output)
    #Return (last) post response
    return {
        'statusCode': 200,
        'body': response

    }

def put_object(string, s3_filepath, encoding="utf-8", client=None):
    """Given `string` to upload, copy it to `s3_filepath` which effectively
    describes the full path of a file in S3 storage defining both bucket
    and object key.
    """
    client, bucket_name, object_name = _s3_setup(client, s3_filepath)
    if encoding:
        string = string.encode(encoding)
    client.put_object(Body=string, Bucket=bucket_name, Key=object_name)

def s3_split_path(s3_path):
    """Given `s3_path` pointing to a bucket, directory path, and optionally an
    object, split the path into its bucket and object remainder components.

    Parameters
    ----------
    s3_path : str
        Full s3 path to a directory or object,  including the bucket prefix,
        e.g. s3://pipeline-outputs/batch-1/acs/j8cb010b0/process.txt

    Returns
    ------
    (bucket_name, object_name) : tuple(str, str)
        e.g. ("s3://pipeline-outputs", "batch-1/acs/j8cb010b0/process.txt")
    """
    if s3_path.startswith("s3://"):
        s3_path = s3_path[5:]
    parts = s3_path.split("/")
    bucket_name, object_name = parts[0], "/".join(parts[1:])
    return bucket_name, object_name


def _s3_setup(client, s3_filepath):
    """Utility for common s3 function setup,  splits `s3_filepath` into bucket
    and key and creates an s3 client if `client` is None.

    Returns client, bucket_name, object_name
    """
    client = client or boto3.client('s3')
    bucket_name, object_name = s3_split_path(s3_filepath)
    return client, bucket_name, object_name


# ------------------------ lambda  test event  CalcloudHstMvp8

{
  "datasets": [
    "J8CB010B0",
    "J8NE53ZNQ",
    "LCYID1030",
    "LDQHPBI9Q",
    "O8L7SWS9Q",
    "OCTKA6010",
    "ICB154060",
    "IDGG23ZTQ"
  ]
}

# ------------------------ lambda  test event  CalcloudHstMvp4

{
  "datasets": "J8CB010B0\nLDQHPBI9Q\nO8L7SWS9Q\nOCTKA6010"
}

# ------------------------ lambda  test event  CalcloudHstNightlyArchive

{
  "datasets": "j6d508010\nj6d511gvq\nj8eh11020\nj8hk01vnq\njbnya2suq\njd5702010\njd5702020\njd5702030\njd5702040\nje5ja1bcq\nje5ja1beq\nla7803fiq\nla8q99030\nlaaf1a010\nlabq740n0\nldd306cbq\no41u4yd4q\no59z03010\no59z03020\nobes03010\nobes03euq\nobes03ewq\nocetl2020\noctu03030\noctu03040\niacs01t4q\niacs01t9q\niacs01tbq\nib8t01010\nibbq01030\nibbq01040\nibbq01n0q\nibvz01010\nibvz01020\nibvz01030\nibvz01040"
}

