"""This module handles file operations with AWS s3 with a
simplified interface.

The primary simplifications is to specifying s3 object paths
as a combination of bucket and object key which are then
broken apart internally like this:

    bucket_name, object_path = s3_split_path(s3_path)
"""
import os
import os.path
import tempfile

import boto3

from calcloud import log

# -------------------------------------------------------------

__all__ = [
    "s3_split_path",
    "download_filepath",
    "upload_filepath",
    "download_directory",
    # "upload_directory",
    "list_directory",
    "get_object",
    "put_object",
    "delete_object",
    "move_object",
    "copy_object",
    "S3Messenger",
    ]

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
    client = client or boto3.client('s3')
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
    client = client or boto3.client('s3')
    from_bucket_name, from_object_name = s3_split_path(s3_filepath_from)
    to_bucket_name, to_object_name = s3_split_path(s3_filepath_to)
    return client.copy_object(
        Bucket=to_bucket_name,
        Key=to_object_name,
        CopySource={
            'Bucket': from_bucket_name,
            'Key': from_object_name,
        })


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
    client = client or boto3.client('s3')
    copy_object(s3_filepath_from, s3_filepath_to, client)
    delete_object(s3_filepath_from, client)


# -------------------------------------------------------------

def download_directory(dirpath, s3_dirpath, max_objects=1000, client=None):
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
    for s3_filepath in list_directory(s3_dirpath, max_objects=max_objects, client=client):
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


def list_directory(s3_prefix, client=None, max_objects=1, exclude_prefix=True):
    """Given `s3_dirpath_prefix` s3 bucket and prefix to list, return the full
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
    exclude_prefix : bool
        Do not include the path for the empty s3 directory.

    Returns
    ------
    [ full_s3_object_path, ... ]  :  list( str )
        list of full s3 paths of objects matching `s3_dirpath_prefix`.
    """
    msgs = []
    for i in range(max_objects, 0, -1000):
        count = min(i, 1000)
        if count:
            block = _list_directory(s3_prefix, client, count, exclude_prefix)
            msgs.extend(block)
            if len(block)< 1000:
                break
        else:
            break
    return msgs


def _list_directory(s3_prefix, client=None, max_objects=1, exclude_prefix=True):
    """Handle one block of up to 1000 objects for list_directory."""
    client, bucket_name, prefix = _s3_setup(client, s3_prefix)
    response = client.list_objects(
        Bucket=bucket_name, Prefix=prefix, MaxKeys=max_objects)
    return ["s3://" + bucket_name + "/" + result["Key"]
            for result in response.get("Contents", [])
            if result["Key"] != prefix or not exclude_prefix]


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

# -------------------------------------------------------------


class S3Messenger:
    """S3Messenger handles sending and receiving messages via files in S3.  Messages
    can contain arbitrary text and when sent are uploaded as S3 objects stored
    at a path structured like this:

       `s3_path`/`message_type`/`message_name`

    S3 `message_type`s correspond roughly to message queues to which messages are
    sent.   To ease implementation,  the names of messages are preserved and available.

    `s3_path`        batch output path.  Extended by "messages" and "data."
    `messaging_type` the kind of message, e.g. dataset-processed.
    `message_name`   the S3 object where message is stored, e.g. an ipppssoot.
    """
    def __init__(self, s3_path):
        self.s3_path = s3_path
        self.client = boto3.client("s3")
        self.tmp_dir = tempfile.gettempdir()
        if not os.path.isdir(self.tmp_dir):
            os.mkdir(self.tmp_dir)

    def message_path(self, message_type, message_name):
        """Given strings `message_type` and `message_name` return the
        S3 path for that message.
        """
        return "/".join([self.s3_path, "messages", message_type, message_name])

    def data_path(self, name):
        """Given string  `name`,  return the corresponding S3 path within
        the messenger's data branch.
        """
        return "/".join([self.s3_path, "data", name])

    def message_name(self, s3_msg_path):
        """Given `s3_msg_path` string,  return the name of the message."""
        return s3_msg_path.split("/")[-1]

    def download_directory(self, local_path, s3_path, max_files=1000):
        """Given S3 directory at `s3_path`,  download all files to `local_path`."""
        log.info(f"Downloading '{s3_path}' to '{local_path}'.")
        return download_directory(
            local_path, s3_path, client=self.client, max_objects=max_files)

    def list_messages(self, message_type, max_messages=1):
        """Given string `message_type`,  return the S3 paths of up to
        `max_messages` of that  type.
        """
        s3_prefix = self.s3_path + "/messages/" + message_type
        log.verbose(f"Listing messages at '{s3_prefix}'.")
        return list_directory(
            s3_prefix, client=self.client, max_objects=max_messages)

    def list_names(self, message_type, max_messages=1):
        """Given string `message_type`,  return the message names of
        up to `max_messages` of that type.
        """
        paths = self.list_messages(message_type, max_messages)
        return [self.message_name(path) for path in paths]

    def receive(self, message_type, encoding='utf-8'):
        """Given string `message_type`, fetch one message of that
        type and delete the S3 copy.   Return the name of the
        message and contents loaded from the S3 file.

        Returns (message_name, message_content) or ()
        """
        message_paths = self.list_messages(message_type)
        if message_paths:
            message = self.load(message_paths[0], encoding)
            delete_object(message_paths[0], self.client)
            return message
        return ()

    def load(self, message_path, encoding='utf-8'):
        """Given string S3 `message_path`,  get the object contents
        from that message path with `encoding`.

        return (message_name, message_contents)
        """
        contents = get_object(
            message_path, client=self.client, encoding=encoding)
        return (self.message_name(message_path), contents)

    def send(self, message_type, message):
        """Given string `message_type` and a (name, contents) tuple
        `message`,  upload the contents to that  appropriate S3 path
        for that message type and name.
        """
        message_name, message_contents = message
        tmp_name = os.path.join(self.tmp_dir, message_name)
        with open(tmp_name, "w+") as _tmp_file:
            _tmp_file.write(message_contents)
        s3_name = self.message_path(message_type, message_name)
        upload_filepath(tmp_name, s3_name, client=self.client)

    def receive_and_resend(self, old_type, new_type):
        """Given S3 message type string  `old_type` and `new_type`,
        receive one message from `old_type`,  send it to `new_type`,  and
        return it.   This corresponds to moving the message from one
        queue to the next in a linear series while reading the value.

        Returns  (message_name, message_contents)
        """
        message = self.receive(old_type)
        if message:
            self.send(new_type, message)
        return message

    def delete(self, message_type, message_name):
        """Given  string S3 `message_type` and `message_name`, delete
        the S3 object at the corresponding S3 message path.

        This is essentially the same thing as removing a message from
        an AWS SQS queue after receiving it where `message_name` has
        an intelligble value.
        """
        path = self.message_path(message_type, message_name)
        delete_object(path, self.client)

    def pass_message(self, old_type, new_type, message):
        """Given S3 message type string `old_type`, `new_type`, and
        (name, contents) tuple `message`,  send the contents
        of `message` to `new_type` and delete the object at S3
        `old_type` with the message's `name`.

        Assuming `contents` match the message with `name` of `old_type`,
        this corresponds to moving the message from queue `old_type` to
        queue `new_type`.
        """
        self.send(new_type, message)
        self.delete(old_type, message[0])

    def reset(self, to_type, from_types):
        """Given message type `to_type`,  find all S3 messages for the types
        in list `from_types` and move them to `to_type`.   This can be used
        to reset batch outputs to their original un-synced state following
        failures or during development.
        """
        for from_type in from_types:
            for path in self.list_messages(from_type, max_messages=2**30):
                self.pass_message(from_type, to_type, self.load(path))


