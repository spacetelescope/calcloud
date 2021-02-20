"""This module handles messaging and I/O layered on top of S3.
It hides the structure of the messaging system and provides a
simple API for putting, getting, listing, and deleting messages.
"""
import sys
import doctest
import json

from calcloud import s3

# -------------------------------------------------------------

__all__ = [
    "get_io_bundle",
    "MESSAGE_TYPES",
    "S3Io",
    "MessageIo",
    "ControlIo",
    "InputsIo",
    "OutputsIo",
]

# -------------------------------------------------------------


class S3Io:
    """This class provides and API for S3 which implements basic
    put/get/list/del operations,  particularly as they pertain to
    messaging.
    """

    def __init__(self, s3_path, client=None):
        """API operating relative to `s3_path` using S3 `client`.

        Note that `s3_path` can include the beginning of the object key,
        e.g. 's3://bucket/messages' or 's3://bucket/outputs'.

        If client is not specified the calcoud default S3 client is
        used which is presumed only suitable for single threaded
        or single process applications.
        """
        self.client = client or s3.get_default_client()
        self.s3_path = s3_path

    def path(self, prefix):
        """Given an additional `prefix`,  return a full S3 path,  which
        is potentially still incomplete and can  result in multiple S3
        list results.
        """
        return self.s3_path + "/" + prefix

    def expand_prefix(self, prefix):
        """For simple APIs,  a prefix of "all" translates to a partial S3 list
        key of "".   Anything other prefix is returned unchanged.   Hence:

        expand_prefix("all") -> ""

        expand_prefix("anything-else") -> "anything-else"
        """
        yield "" if prefix == "all" else prefix

    def expand_all(self, prefixes):
        """Takes either a single prefix string or sequence of prefix strings,
        each of which is expanded into one or more partial S3 list keys / suffixes.

        The remainder of the key is determined by `self.s3_path` which includes
        both the bucket and beginning of the S3 object key.

        This method is most important when overriden by subclasses,  particularly
        the MessageIo subclass which translates "all-" into a sequence of all
        message types.
        """
        if isinstance(prefixes, str):
            prefixes = [prefixes]
        for prefix in prefixes:
            for expanded in self.expand_prefix(prefix):
                yield expanded

    def list_s3(self, prefixes="all"):
        """Given S3 `prefixes` described earlier, generate the sequence of
        full S3 paths corresponding to those prefixes,  list each path in
        S3,  and generate a single combined sequence of list results.

        Note that each individual prefix has the potential to result
        in multiple S3 paths and each full S3 path has the potential
        to list multiple objects.
        """
        for expanded in self.expand_all(prefixes):
            yield from s3.list_objects(self.path(expanded), client=self.client)

    def list(self, prefixes="all"):
        """Given S3 `prefixes` described earlier, use list_s3() to generate a
        sequence of listed objects and yield only the final prefix
        component of each listed object.
        """
        for s3_path in self.list_s3(prefixes):
            yield s3_path.split("/")[-1]

    def listl(self, prefixes="all"):
        """Return the outputs of list() as a list,  mainly for testing since list()
        returns a generator which reveals little in its repr().
        """
        return list(sorted(self.list(prefixes)))

    def get(self, prefix, encoding="utf-8"):
        return s3.get_object(self.path(prefix), client=self.client, encoding=encoding)

    def put(self, msgs, encoding="utf-8"):
        """Put messages `msgs` into S3,  accepting several forms:

        1. "simple-message"
        2. ["simple-message1", "simple-message2", ...]
        2. {"simple-message" : "message-payload", ...}

        The forms with no payloads specified put the empty string.

        The form with string payloads specified write out the bytes resulting from
        encoding the payload with `encoding`.  Simple text messages as well as YAML
        or JSON serializations should "just work".  Use encoding=None to write out
        byte strings directly.
        """
        if isinstance(msgs, (list, tuple)):
            msgs = zip(msgs, [""] * len(msgs))
        elif isinstance(msgs, str):
            msgs = [(msgs, "")]
        elif isinstance(msgs, dict):
            msgs = msgs.items()
        for msg, payload in msgs:
            s3.put_object(payload, self.path(msg), encoding=encoding, client=self.client)

    def delete(self, prefixes):  # dangerous to support 'all' as default
        """Given typical message/output prefixes, locate and delete the corresponding objects,
        which are nominally S3 files of some kind.
        """
        for path in self.list_s3(prefixes):
            s3.delete_object(path, client=self.client)

    def move(self, prefix_from, prefix_to):
        """Pass any contents of `prefix_from` to `prefix_to` and delete the object at `prefix_from`."""
        s3.move_object(self.path(prefix_from), self.path(prefix_to), client=self.client)


# -------------------------------------------------------------

MESSAGE_TYPES = [
    "placed",
    "submit",
    "processing",
    "processed",
    "error",
    "ingesterror",
    "ingested",
    "terminated",
    "cancel",
    "rescue",
]


class MessageIo(S3Io):
    """The MessageIo class provides put/get/list/delete operations for
    messages of various types used to track the state of dataset
    processing.

    It can operate on a particular message type for a paritcular
    ipppssoot, e.g.  'error-lcw303cjq'.

    It can operate on all message types for a particular ipppssoot,
    e.g. 'all-lcw303cj'

    It can operate on a particular message type for all ipppssoots,
    e.g. 'error' or 'error-all'.

    It can operate on all types of messages for all ipppssoots,
    e.g. 'all'.

    >>> comm = get_io_bundle()

    >>> comm.messages.put(['cancel-lcw303cjq', 'error-lcw303cjq', 'placed-lcw303cjq', 'rescue-lcw303cjq']);
    >>> comm.messages.listl()
    ['cancel-lcw303cjq', 'error-lcw303cjq', 'placed-lcw303cjq', 'rescue-lcw303cjq']

    >>> list(comm.messages.list_s3("error")) #doctest: +ELLIPSIS
    ['s3://.../messages/error-lcw303cjq']

    >>> comm.messages.listl("rescue")
    ['rescue-lcw303cjq']

    >>> comm.messages.delete("rescue");
    >>> comm.messages.listl()
    ['cancel-lcw303cjq', 'error-lcw303cjq', 'placed-lcw303cjq']

    >>> comm.messages.delete("all");
    >>> comm.messages.listl()
    []

    >>> list(comm.messages.expand_all('all-lcw303cjq'))
    ['placed-lcw303cjq', 'submit-lcw303cjq', 'processing-lcw303cjq', 'processed-lcw303cjq', 'error-lcw303cjq', 'ingesterror-lcw303cjq', 'ingested-lcw303cjq', 'terminated-lcw303cjq', 'cancel-lcw303cjq', 'rescue-lcw303cjq']

    >>> comm.messages.put(['cancel-lcw303cjq', 'error-lcw303cjq', 'rescue-lcw304cjq']);
    >>> comm.messages.delete('all-lcw303cjq');
    >>> comm.messages.listl()
    ['rescue-lcw304cjq']

    >>> comm.messages.put(['error-lcw303cjq', 'error-lcw304cjq', 'error-lcw305cjq']);  comm.messages.listl()
    ['error-lcw303cjq', 'error-lcw304cjq', 'error-lcw305cjq', 'rescue-lcw304cjq']
    >>> comm.messages.delete('error-all');  comm.messages.listl()
    ['rescue-lcw304cjq']

    >>> comm.messages.move('rescue-lcw304cjq', 'terminated-lcw304cjq'); comm.messages.listl();
    ['terminated-lcw304cjq']

    >>> comm.messages.delete("all")
    """

    add_trigger_types = ["processed"]

    def path(self, prefix):
        """Message `prefix` should always start with at least the `type` aspect of
        a type-ipppssoot message id,  or 'all' types.

        >>> comm = get_io_bundle()
        >>> comm.messages.path('rescue-lcw304cjq')  #doctest: +ELLIPSIS
        's3://.../messages/rescue-lcw304cjq'
        """
        parts = prefix.split("-")
        if parts[0] not in MESSAGE_TYPES + ["all"]:
            raise ValueError("Invalid message type for prefix: " + repr(prefix))
        # if parts[0] in self.add_trigger_types and len(parts) == 2:  # XXXXX whoop whoop whoop,  .trigger hack!!
        #     prefix += ".trigger"
        return self.s3_path + "/" + prefix

    def expand_prefix(self, prefix):
        """For the MessageIo,  expand_all is used to generate a sequence of partial S3 keys
        which correspond to:

        1. "all messages of all types"    when prefix="all"
        2. "all types for one ipppssoot"  when prefix="all-{ipst}"
        3. "one type for one ipppssoot"   when prefix="{type}-{ipst}"
        4. "all ipppssoots of one type"   when prefix="{type}-{all}" also equivalent to "{type}"

        >>> comm = get_io_bundle()
        >>> list(comm.messages.expand_all('all'))
        ['placed', 'submit', 'processing', 'processed', 'error', 'ingesterror', 'ingested', 'terminated', 'cancel', 'rescue']

        >>> list(comm.messages.expand_all('all-lcw303cjq'))
        ['placed-lcw303cjq', 'submit-lcw303cjq', 'processing-lcw303cjq', 'processed-lcw303cjq', 'error-lcw303cjq', 'ingesterror-lcw303cjq', 'ingested-lcw303cjq', 'terminated-lcw303cjq', 'cancel-lcw303cjq', 'rescue-lcw303cjq']

        >>> list(comm.messages.expand_all('rescue-lcw304cjq'))
        ['rescue-lcw304cjq']

        >>> list(comm.messages.expand_all('rescue-all'))
        ['rescue']
        """
        if prefix == "all":
            prefix = "all-"
        if prefix.endswith("-all"):
            prefix = prefix[: -len("-all")]
        if prefix == "all" or prefix.startswith("all-"):
            ipppssoot = prefix[len("all-") :]
            for type in MESSAGE_TYPES:
                yield f"{type}-{ipppssoot}" if ipppssoot else type
        else:
            yield prefix


class InputsIo(S3Io):
    """InputsIo provides simple standard operations on the processing
    inputs store.

    >>> comm = get_io_bundle()
    >>> comm.inputs.path('lcw303cjq') #doctest: +ELLIPSIS
    's3://.../inputs/lcw303cjq'
    """


class OutputsIo(S3Io):
    """OutputsIo provides simple standard operations on the processing
    outputs store.

    >>> comm = get_io_bundle()
    >>> comm.outputs.put({'lcw303cjq/something.fits': 'some contents'})
    >>> comm.outputs.get('lcw303cjq/something.fits')
    'some contents'

    >>> comm.outputs.put({'lcw303cjq/something.fits': b'some contents'}, encoding=None)
    >>> comm.outputs.get('lcw303cjq/something.fits', encoding=None)
    b'some contents'

    >>> comm.outputs.put('lcw303cjq/something.fits')
    >>> comm.outputs.get('lcw303cjq/something.fits')
    ''

    >>> list(comm.outputs.list_s3("all"))   #doctest: +ELLIPSIS
    ['s3://.../outputs/lcw303cjq/something.fits']

    >>> comm.outputs.delete("all");   list(comm.outputs.list_s3())
    []
    """


class ControlIo(S3Io):
    """Provides simple standard operations on the processing control store,
    transparently serializing/de-serializing Python objects as a JSON
    encoded payload.

    >>> comm = get_io_bundle()

    >>> obj = {'job_params': {'memory': 1500, 'vcpus': 2}, 'job_id': '1cc5817c-8d93-4119-bbd4-25407ee233b5', 'retry': 0}
    >>> comm.control.put('lcw303cjq', obj)

    >>> comm.control.get('lcw303cjq')
    {'job_params': {'memory': 1500, 'vcpus': 2}, 'job_id': '1cc5817c-8d93-4119-bbd4-25407ee233b5', 'retry': 0}
    """

    def get(self, ipppssoot):
        text = super().get(ipppssoot)
        return json.loads(text)

    def put(self, ipppssoot, obj):
        if not isinstance(obj, str):
            text = json.dumps(obj)
        super().put({ipppssoot: text})


# -------------------------------------------------------------


class IoBundle:
    """Bundle all the I/O branches into one package."""

    def __init__(self, bucket=s3.DEFAULT_S3_BUCKET, client=None):
        self.client = client or s3.get_default_client()
        self.bucket = bucket
        self.messages = MessageIo("s3://" + self.bucket + "/messages", self.client)
        self.inputs = InputsIo("s3://" + self.bucket + "/inputs", self.client)
        self.outputs = OutputsIo("s3://" + self.bucket + "/outputs", self.client)
        self.control = ControlIo("s3://" + self.bucket + "/control", self.client)


def get_io_bundle(bucket=s3.DEFAULT_S3_BUCKET, client=None):
    return IoBundle(bucket, client)


# ------------------------------------------------------------


def test():
    from calcloud import io

    return doctest.testmod(io)


if __name__ == "__main__":
    if sys.argv[1] == "test":
        print(test())
