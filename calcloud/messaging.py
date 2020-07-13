"""This module implements a messaging abstraction on S3 and local file systems.

It is used by the Syncer process to communicate system state changes and other
associated information.
"""
import os
import tempfile
import glob
import shutil

import boto3

from calcloud import s3
from calcloud import log

# -------------------------------------------------------------


class Message:
    """One parcel of communication which can be categorized as `type` and is
    named `name`.   If specified,   the message contains/is string `contents`.
    """
    def __init__(self, type, name, contents=None):
        self.type = type
        self.name = name
        self.contents = contents

    def retype(self, new_type):
        """Given `new_type`,  return a message like this one with that type instead.""""
        return Message(new_type, self.name, self.contents)


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

    def message_path(self, message):
        """Given strings `message_type` and `message_name` return the
        S3 path for that message.
        """
        return "/".join([self.s3_path, "messages", message.type, message.name])

    def data_path(self, name):
        """Given string  `name`,  return the corresponding S3 path within
        the messenger's data branch.
        """
        return "/".join([self.s3_path, "data", name])

    def message_name(self, s3_msg_path):
        """Given `s3_msg_path` string,  return the name of the message."""
        return s3_msg_path.split("/")[-1]

    def message_type(self, s3_msg_path):
        """Given `s3_msg_path` string,  return the type of the message."""
        return s3_msg_path.split("/")[-2]

    def download_directory(self, local_path, s3_path, max_files=1000):
        """Given S3 directory at `s3_path`,  download all files to `local_path`."""
        log.info(f"Downloading '{s3_path}' to '{local_path}'.")
        return s3.download_directory(
            local_path, s3_path, client=self.client, max_objects=max_files)

    def list_messages(self, message_type, max_messages=1):
        """Given string `message_type`,  return the S3 paths of up to
        `max_messages` of that  type.
        """
        s3_prefix = self.s3_path + "/messages/" + message_type
        log.verbose(f"Listing messages at '{s3_prefix}'.")
        return s3.list_directory(
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
            s3.delete_object(message_paths[0], self.client)
            return message
        return None

    def load(self, message_path, encoding='utf-8'):
        """Given string S3 `message_path`,  get the object contents
        from that message path with `encoding`.

        return Message
        """
        contents = s3.get_object(
            message_path, client=self.client, encoding=encoding)
        return Message(
            self.message_type(message_path),
            self.message_name(message_path),
            contents)

    def send(self, message):
        """Given string `message_type` and a (name, contents) tuple
        `message`,  upload the contents to that  appropriate S3 path
        for that message type and name.
        """
        tmp_name = os.path.join(self.tmp_dir, message.name)
        with open(tmp_name, "w+") as _tmp_file:
            _tmp_file.write(message.contents)
        s3_name = self.message_path(message)
        s3.upload_filepath(tmp_name, s3_name, client=self.client)
        return message

    def receive_and_resend(self, old_type, new_type):
        """Given S3 message type string  `old_type` and `new_type`,
        receive one message from `old_type`,  send it to `new_type`,  and
        return it.

        Returns  Message
        """
        message = self.receive(old_type)
        if message:
            return self.send(message.retype(new_type))
        return message

    def delete(self, message):
        """Given  `message`, delete the S3 object at the corresponding
        S3 message path.
        """
        s3.delete_object(self.message_path(message), self.client)

    def pass_message(self, new_type, message):
        """Given S3 message type string `old_type`, `new_type`, and
        (name, contents) tuple `message`,  send the contents
        of `message` to `new_type` and delete the object at S3
        `old_type` with the message's `name`.
        """
        new_message = self.send(message.retype(new_type))
        self.delete(message)
        return new_message

    def reset(self, to_type, from_types):
        """Given message type `to_type`,  find all S3 messages for the types
        in list `from_types` and move them to `to_type`.   This can be used
        to reset batch outputs to their original un-synced state following
        failures or during development.
        """
        for from_type in from_types:
            for path in self.list_messages(from_type, max_messages=2**30):
                self.pass_message(to_type, self.load(path))


# -------------------------------------------------------------


class FsMessenger:
    """This class implements Messenger methods needed to output
    messages to a file system,  nominally for communicating about
    datasets which are ready to archive.
    """
    def __init__(self, output_dir):
        self.output_dir = output_dir

    def data_path(self, dataset_subpath):
        return os.path.join(self.output_dir, "data", dataset_subpath)

    def message_path(self, message):
        """Return the path to the message file of type `kind`
        named `dataset`.
        """
        return os.path.join(self.output_dir, "messages", message.type, message.name)

    def message_name(self, message_path):
        return os.path.basename(message_path)

    def send(self, message):
        """Send message of type `kind` with name `dataset`
        and contents `text` which defaults to the empty string.
        """
        msg_path = self.message_path(message)
        os.makedirs(os.path.dirname(msg_path), exist_ok=True)
        with open(msg_path, "w+") as msg:
            msg.write(message.contents)

    def pass_message(self, new_kind, message):
        """Given the `dataset` with (dataset_name, _),  move the message
        to type `new_kind`.
        """
        old_path = self.message_path(message)
        new_path = self.message_path(message.retype(new_kind))
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        shutil.move(old_path, new_path)

    def reset(self, kinds):
        """Delete all messages of types in list `kinds`."""
        for kind in kinds:
            where = self.message_path(Message(kind, "*"))
            log.info(f"Removing messages at '{where}'")
            msgs = glob.glob(where)
            for msg in msgs:
                os.remove(msg)

