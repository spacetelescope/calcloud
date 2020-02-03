import os, os.path

import boto3

# -------------------------------------------------------------

def upload_filename(filename, bucket, objectname=None, prefix=None):
    if bucket.startswith("s3://"):
        bucket = bucket[5:]
    if objectname is None:
        objectname = object_name(filename, prefix)
    client = boto3.client('s3')
    with open(filename, "rb") as f: 
        client.upload_fileobj(f, bucket, objectname)

def download_filename(filename, bucket, objectname=None, prefix=None):
    if bucket.startswith("s3://"):
        bucket = bucket[5:]
    if objectname is None:
        objectname = object_name(filename, prefix)
    client = boto3.client('s3')
    with open(filename, "wb+") as f:
        client.download_fileobj(bucket, objectname, f)
    
# -------------------------------------------------------------

def object_name(filename, prefix=None):
    object_name = os.path.basename(filename)
    if prefix is not None:
        object_name = prefix + "/" + object_name
    return object_name

