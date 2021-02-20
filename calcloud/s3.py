"""This module handles file operations with AWS s3 with a
simplified interface.

The primary simplifications is to specifying s3 object paths
as a combination of bucket and object key which are then
broken apart internally like this:

    bucket_name, object_path = s3_split_path(s3_path)
"""
import os
import os.path

import boto3

# -------------------------------------------------------------

__all__ = [
    "s3_split_path",
    "download_filepath",
    "upload_filepath",
    "download_objects",
    # "upload_directory",
    "list_objects",
    "get_object",
    "put_object",
    "delete_object",
    "move_object",
    "copy_object",
    "get_default_client",
    "DEFAULT_BUCKET",
]

# -------------------------------------------------------------

DEFAULT_S3_CLIENT = None


def get_default_client():
    global DEFAULT_S3_CLIENT
    if DEFAULT_S3_CLIENT is None:
        DEFAULT_S3_CLIENT = boto3.client("s3")
    return DEFAULT_S3_CLIENT


DEFAULT_BUCKET = os.environ.get("S3_PROCESSING_BUCKET", "s3://calcloud-UNDEFINED-bucket")

# -------------------------------------------------------------


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
    client = client or boto3.client("s3")
    bucket_name, object_name = s3_split_path(s3_filepath)
    return client, bucket_name, object_name


# -------------------------------------------------------------


def upload_filepath(filepath, s3_filepath, client=None):
    """Given `filepath` to upload, copy it to `s3_filepath`.

    Parameters
    ----------
    filepath : str
       Local filesystem path to a file to upload, including filename.
    s3_filepath : str
        Full s3 path to object to upload,  including the bucket prefix,
        e.g. s3://hstdp/batch-1-2020-06-11T19-35-51/acs/j8cb010b0/process.txt
    client : boto3.client('s3')
        Optional boto3 s3 client to re-use for multiple files.

    Returns
    ------
    None
    """
    client, bucket_name, object_name = _s3_setup(client, s3_filepath)
    return client.upload_file(filepath, bucket_name, object_name)


def download_filepath(filepath, s3_filepath, client=None):
    """Given `filepath` to download, copy s3 object  at `s3_filepath` to it.

    Parameters
    ----------
    filepath : str
       Local filesystem path to file to download, including filename.
    s3_filepath : str
        Full s3 path to object to download,  including the bucket prefix,
        e.g. s3://hstdp/batch-1-2020-06-11T19-35-51/acs/j8cb010b0/process.txt
    client : boto3.client('s3')
        Optional boto3 s3 client to re-use for multiple files.
    Returns
    ------
    None
    """
    client, bucket_name, object_name = _s3_setup(client, s3_filepath)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    return client.download_file(bucket_name, object_name, filepath)


def copy_object(s3_filepath_from, s3_filepath_to, client=None):
    """Given `s3_filepath_from` pointing to an s3 source object, copy
    its contents to `s3_filepath_to`.

    Parameters
    ----------
    s3_filepath_from : str
        s3 source object path.
        e.g. s3://hstdp/batch-1-2020-06-11T19-35-51/acs/j8cb010b0/process.txt
    s3_filepath_to : str
        s3 destination object path.
    client : boto3.client('s3')
        Optional boto3 s3 client to re-use for multiple files.
    Returns
    ------
    None
    """
    client = client or boto3.client("s3")
    from_bucket_name, from_object_name = s3_split_path(s3_filepath_from)
    to_bucket_name, to_object_name = s3_split_path(s3_filepath_to)
    return client.copy_object(
        Bucket=to_bucket_name,
        Key=to_object_name,
        CopySource={
            "Bucket": from_bucket_name,
            "Key": from_object_name,
        },
    )


def move_object(s3_filepath_from, s3_filepath_to, client=None):
    """Given `s3_filepath_from` pointing to an s3 source object, copy
    its contents to `s3_filepath_to` and delete it,  effectively moving
    the object.

    Parameters
    ----------
    s3_filepath_from : str
        s3 source object path.
        e.g. s3://hstdp/batch-1-2020-06-11T19-35-51/acs/j8cb010b0/process.txt
    s3_filepath_to : str
        s3 destination object path.
    client : boto3.client('s3')
        Optional boto3 s3 client to re-use for multiple files.
    Returns
    ------
    None
    """
    client = client or boto3.client("s3")
    copy_object(s3_filepath_from, s3_filepath_to, client)
    delete_object(s3_filepath_from, client)


# -------------------------------------------------------------


def download_objects(dirpath, s3_dirpath, max_objects=1000, client=None):
    """Given `s3_dirpath` s3 directory to download, copy it to a local file system
    at `dirpath`.

    Parameters
    ----------
    dirpath : str
        Local filesystem path where s3 directory will be copied to.
        e.g. /outputs/batch-1-2020-06-11T19-35-51/acs/j8cb010b0
    s3_dirpath : str
        Full s3 path to directory to download,  including the bucket prefix,
        e.g. s3://hstdp/batch-1-2020-06-11T19-35-51/data/acs/j8cb010b0
    client : boto3.client('s3')
        Optional boto3 s3 client to re-use for multiple files.
    max_objects : int
        Max number of files to list and download.

    Returns
    ------
    downloads : list (str)
       file paths of downloaded files.
    """
    client = client or boto3.client("s3")
    downloads = []
    for s3_filepath in list_objects(s3_dirpath, max_objects=max_objects, client=client):
        local_filepath = os.path.abspath(s3_filepath.replace(s3_dirpath, dirpath))
        download_filepath(local_filepath, s3_filepath, client)
        downloads.append(local_filepath)
    return downloads


def upload_directory(dirpath, s3_dirpath):
    """Given `dirpath` local directory to download, copy it to s3
    at `s3_dirpath`.

    Parameters
    ----------
    dirpath : str
        Local filesystem path to copy to s3.
    s3_dirpath : str
        Full s3 path to upload to, including the bucket prefix and object
        prefix.
        e.g. s3://hstdp/batch-1-2020-06-11T19-35-51/acs/j8cb010b0

    Returns
    ------
    None
    """
    raise NotImplementedError("upload_directory hasn't been implemented yet.")


def list_objects(s3_prefix, client=None, max_objects=10 ** 6):
    """Given `s3_dirpath_prefix` s3 bucket and prefix to list, yield the full
    s3 paths of every object in the associated bucket which match the prefix.

    Parameters
    ----------
    s3_prefix : str
        Full s3 path to directory and prefix to list:
        e.g. s3://hstdp/messages/dataset-processed
    client : boto3.client('s3')
        Optional boto3 s3 client to re-use for multiple files.
    max_objects : int
        Max number of S3 objects to return.

    Iterates
    ------
    [ full_s3_object_path, ... ]  :  iter( [ str ] )
        list of full s3 paths of objects matching `s3_prefix` except
        `s3_prefix` itself.
    """
    client, bucket_name, prefix = _s3_setup(client, s3_prefix)
    paginator = client.get_paginator("list_objects_v2")
    config = {"MaxItems": max_objects, "PageSize": max_objects}
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix, PaginationConfig=config):
        for result in page.get("Contents", []):
            listed = "s3://" + bucket_name + "/" + result["Key"]
            yield listed


def get_object(s3_filepath, client=None, encoding="utf-8"):
    """Given `s3_dirpath_prefix` s3 bucket and prefix to list, return the full
    s3 paths of every object in the associated bucket which match the prefix.

    Parameters
    ----------
    s3_dirpath_prefix : str
        Full s3 path to object to fetch
        e.g. s3://hstdp/batch-1-2020-06-11T19-35-51/acs/j8cb010b0/process.txt
    client : boto3.client('s3')
        Optional boto3 s3 client to re-use for multiple files.
    encoding : str
        Encoding to decode object contents with.  Default 'utf-8'.

    Returns
    ------
    object contents : str or bytes
    """
    client, bucket_name, object_name = _s3_setup(client, s3_filepath)
    response = client.get_object(Bucket=bucket_name, Key=object_name)
    binary = response["Body"].read()
    if encoding:
        return binary.decode(encoding)
    return binary


def put_object(string, s3_filepath, encoding="utf-8", client=None):
    """Given `string` to upload, copy it to `s3_filepath` which effectively
    describes the full path of a file in S3 storage defining both bucket
    and object key.
    """
    client, bucket_name, object_name = _s3_setup(client, s3_filepath)
    if encoding:
        string = string.encode(encoding)
    client.put_object(Body=string, Bucket=bucket_name, Key=object_name)


def delete_object(s3_filepath, client=None):
    """Given `s3_filepath` delete the corresponding object.

    Parameters
    ----------
    s3_filepath : str
        Full s3 path to object to delete,  including the bucket prefix,
        e.g. s3://hstdp/batch-1-2020-06-11T19-35-51/acs/j8cb010b0/process.txt
    client : boto3.client('s3')
        Optional boto3 s3 client to re-use for multiple files.
    Returns
    ------
    None
    """
    client, bucket_name, object_name = _s3_setup(client, s3_filepath)
    return client.delete_object(Bucket=bucket_name, Key=object_name)
