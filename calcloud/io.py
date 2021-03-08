"""This module handles messaging and I/O layered on top of S3.
It hides the structure of the messaging system and provides a
simple API for putting, getting, listing, and deleting messages.
"""
import sys
import doctest
import json
import uuid

from calcloud import s3
from calcloud import hst

# -------------------------------------------------------------

__all__ = [
    "get_io_bundle",
    "MESSAGE_TYPES",
    "S3Io",
    "MessageIo",
    "ControlIo",
    "InputsIo",
    "OutputsIo",
    "JsonIo",
    "MetadataIo",
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

    def list_s3(self, prefixes="all", max_objects=s3.MAX_LIST_OBJECTS):
        """Given S3 `prefixes` described earlier, generate the sequence of
        full S3 paths corresponding to those prefixes,  list each path in
        S3,  and generate a single combined sequence of list results.

        Note that each individual prefix has the potential to result
        in multiple S3 paths and each full S3 path has the potential
        to list multiple objects.
        """
        for expanded in self.expand_all(prefixes):
            yield from s3.list_objects(self.path(expanded), client=self.client, max_objects=max_objects)

    def list(self, prefixes="all", max_objects=s3.MAX_LIST_OBJECTS):
        """Given S3 `prefixes` described earlier, use list_s3() to generate a
        sequence of listed objects and yield only the final prefix
        component of each listed object.
        """
        for s3_path in self.list_s3(prefixes, max_objects=max_objects):
            yield s3_path[len(self.s3_path + "/") :]

    def listl(self, prefixes="all", max_objects=s3.MAX_LIST_OBJECTS):
        """Return the outputs of list() as a list,  mainly for testing since list()
        returns a generator which reveals little in its repr().
        """
        return list(sorted(self.list(prefixes, max_objects=max_objects)))

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

    def delete(self, prefixes, check_exists=True):  # dangerous to support 'all' as default
        """Given typical *message* prefixes, locate and delete the corresponding objects,
        which are nominally S3 files of some kind.

        If check_exists is True and an expanded prefix looks like type-ipppssoot, then
        check to see if that message exists with s3.get() before trying
        s3.delete().  When most expansions of all-ipppssoot don't exist,  they only pay
        1/12 the cost of an unneeded delete making it reasonably cheap to use all-ipppssoot
        even when most types don't exist.

        If it's expected that most expansions do exist,  then set check_exists=False to avoid
        unnecessary tests for messges known to exist,  just delete them.
        """
        for prefix in self.expand_all(prefixes):
            parts = prefix.split("-")
            if len(parts) == 2 and parts[0] in MESSAGE_TYPES:
                try:
                    # these don't have self.s3_path added yet
                    s3_path = self.path(prefix)
                    if check_exists:  # don't try to delete
                        s3.get_object(s3_path, client=self.client)
                    s3.delete_object(s3_path, client=self.client)
                except self.client.exceptions.NoSuchKey:
                    pass  # Catch any failed gets
            else:
                for path in self.list_s3(prefix):
                    s3.delete_object(path, client=self.client)

    def delete_literal(self, msg):
        """Given the name of a message `msg`,  delete it,  and in the case of "all-xxxx" or "xxxx-all"
        messages,  do not expand "all" first.
        """
        s3.delete_object(self.path(msg), client=self.client)

    def move(self, prefix_from, prefix_to):
        """Pass any contents of `prefix_from` to `prefix_to` and delete the object at `prefix_from`."""
        s3.move_object(self.path(prefix_from), self.path(prefix_to), client=self.client)

    def pop(self, prefix):
        """Fetch the contents of message `prefix` and delete it."""
        msg = self.get(prefix)
        self.delete_literal(prefix)
        return msg

    def ids(self):
        """Return the list of all unique ipppssoot/id directories."""
        return list(set(obj.split("/")[0] for obj in self.list("all")))


# -------------------------------------------------------------


class JsonIo(S3Io):
    """Serializes/deserializes objects to JSON when putting/getting from S3."""

    def get(self, prefix):
        """Return the decoded message object fetched from literal message name `prefix`."""
        text = super().get(prefix)
        return json.loads(text)

    def put(self, prefix, obj=""):
        """Put messages defined by message name `prefix` and  payload `obj`.

        If `prefix` is a string, it is the message name and `obj` defines the payload.
        If `prefix` is a list of strings, they are message names, and `obj` defines the common payload.
        If `prefix` is a dict,  they keys are messages names,  the values are message payload objects.

        Prior to putting,  any payloads are encoded in JSON using json.dumps().
        """
        if isinstance(prefix, str):
            prefix = [prefix]
        if isinstance(prefix, list):
            prefix = {pref: obj for pref in prefix}
        super().put({pref: json.dumps(obj) for (pref, obj) in prefix.items()})


MESSAGE_TYPES = [
    "broadcast",
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


class MessageIo(JsonIo):
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

    put() enables sending a message or sequence of messages which should be fully specified
    including the full ipppssoot.   Specified as a string or list the message payload(s) are
    defaulted to the empty string:

    >>> comm.messages.put(['cancel-lcw303cjq', 'error-lcw303cjq', 'processed-lcw303cjq', 'rescue-lcw303cjq']);
    >>> comm.messages.listl()
    ['cancel-lcw303cjq', 'error-lcw303cjq', 'processed-lcw303cjq', 'rescue-lcw303cjq']

    list_s3() yields the fully qualified S3 paths matching the given prefix(es) that exist on S3:

    >>> list(comm.messages.list_s3("error")) #doctest: +ELLIPSIS
    ['s3://.../messages/error-lcw303cjq']

    listl() is primarily a test method which returns the list of messages matching prefix(es):

    >>> comm.messages.listl("rescue")
    ['rescue-lcw303cjq']

    delete(type) removes all messages of type:

    >>> comm.messages.delete("rescue");
    >>> comm.messages.listl()
    ['cancel-lcw303cjq', 'error-lcw303cjq', 'processed-lcw303cjq']

    The "all" or "" messages expand to all existing messages:

    >>> comm.messages.delete("all");
    >>> comm.messages.listl()
    []

    expand_all("all-ipppssoot") is expanded into type-ipppssoot for every type
    in MESSAGE_TYPES regardless of the existence of the message on S3:

    >>> list(comm.messages.expand_all('all-lcw303cjq'))
    ['broadcast-lcw303cjq', 'placed-lcw303cjq', 'submit-lcw303cjq', 'processing-lcw303cjq', 'processed-lcw303cjq', 'error-lcw303cjq', 'ingesterror-lcw303cjq', 'ingested-lcw303cjq', 'terminated-lcw303cjq', 'cancel-lcw303cjq', 'rescue-lcw303cjq']

    The all-ipppssoot message is expanded to every type-ipppssoot:

    >>> comm.messages.put(['cancel-lcw303cjq', 'error-lcw303cjq', 'rescue-lcw304cjq']);
    >>> comm.messages.delete('all-lcw303cjq'); comm.messages.listl()
    ['rescue-lcw304cjq']

    The type-all message is expanded into every type-ipppssoot combination and is really
    equivalent to searching for S3 prefix "type".

    >>> comm.messages.put(['error-lcw303cjq', 'error-lcw304cjq', 'error-lcw305cjq']);  comm.messages.listl()
    ['error-lcw303cjq', 'error-lcw304cjq', 'error-lcw305cjq', 'rescue-lcw304cjq']
    >>> comm.messages.delete('error-all');  comm.messages.listl()
    ['rescue-lcw304cjq']

    Methods list() and listl() report 'processed' messages without the .trigger suffix:

    >>> comm.messages.move('rescue-lcw304cjq', 'processed-lcw304cjq'); comm.messages.listl();
    ['processed-lcw304cjq']

    On S3,  .trigger is appended to the 'processed-ipppssoot' message:

    >>> list(comm.messages.list_s3('processed-lcw304cjq')) #doctest: +ELLIPSIS
    ['s3://.../messages/processed-lcw304cjq.trigger']

    >>> comm.messages.delete("all");  list(comm.messages.list_s3())
    []
    """

    add_trigger_types = ["processed"]

    def path(self, prefix):
        """Converts `prefix` to an appropriate fully specified S3 path, which
        may designate an individual type-ipppssoot message or a more ambiguous
        partial key.

        Message `prefix` should always start with at least the `type` aspect of
        a type-ipppssoot message id,  or 'all'.

        >>> comm = get_io_bundle()
        >>> comm.messages.path('rescue-lcw304cjq')  #doctest: +ELLIPSIS
        's3://.../messages/rescue-lcw304cjq'
        """
        parts = prefix.split("-")
        if parts[0] not in MESSAGE_TYPES + ["all"]:
            raise ValueError("Invalid message type for prefix: " + repr(prefix))
        if parts[0] in self.add_trigger_types and len(parts) == 2:  # XXXXX add .trigger hack!!
            prefix += ".trigger"
        return self.s3_path + "/" + prefix

    def expand_prefix(self, prefix):
        """For the MessageIo,  expand_all is used to generate a sequence of partial S3 keys
        which correspond to:

        1. "all messages of all types"    when prefix="all"
        2. "all types for one ipppssoot"  when prefix="all-{ipst}"
        3. "one type for one ipppssoot"   when prefix="{type}-{ipst}"
        4. "all ipppssoots of one type"   when prefix="{type}-{all}" also equivalent to "{type}"

        >>> comm = get_io_bundle()

        Used w/o -ipppssoot,  "all" expands into the all message types, which when used as S3 object
        key prefixes, match all ipppssoots of each type:

        >>> list(comm.messages.expand_all('all'))
        ['broadcast', 'placed', 'submit', 'processing', 'processed', 'error', 'ingesterror', 'ingested', 'terminated', 'cancel', 'rescue']

        The message 'all-ipppssoot' expands into a sequence of type-ipppssoot messages for each
        type in MESSAGE_TYPES:

        >>> list(comm.messages.expand_all('all-lcw303cjq'))
        ['broadcast-lcw303cjq', 'placed-lcw303cjq', 'submit-lcw303cjq', 'processing-lcw303cjq', 'processed-lcw303cjq', 'error-lcw303cjq', 'ingesterror-lcw303cjq', 'ingested-lcw303cjq', 'terminated-lcw303cjq', 'cancel-lcw303cjq', 'rescue-lcw303cjq']

        A fully specified type-ipppsoot message expands to itself:

        >>> list(comm.messages.expand_all('rescue-lcw304cjq'))
        ['rescue-lcw304cjq']

        Since expand_all() operates regardless of S3 content,  the 'type-all' messsage expands
        to the search prefix 'type' suitable for listing all ipppsoots of 'type':

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

    def get_id(self):
        """Return a unique message ID,  nominally for broadcast messages."""
        return str(uuid.uuid4()).replace("-", "_")

    def broadcast(self, type, ipppssoots):
        """Output a `type` message for each dataset in `ipppssoots`.  This
        is nominally done by sending a list of messages to the broadcast lambda
        which then sends them using a divide-and-conquer approach.

        >>> comm = get_io_bundle()

        Calling the broadcast method writes a single broadcast message containing a payload of messages to send.
        Broadcast messages are named using a random id instead of ipppssoot, a uuid with _ replacing -.

        >>> msg = comm.messages.broadcast("cancel", ["lcw303cjq", "lcw304cjq", "lcw305cjq"]);
        >>> comm.messages.listl() #doctest: +ELLIPSIS
        ['broadcast-..._..._..._..._...']

        The contents of a broadcast message is a list of no-payload messages which will later be sent
        by the lambda which processes broadcast messages:

        >>> comm.messages.pop(msg)
        ['cancel-lcw303cjq', 'cancel-lcw304cjq', 'cancel-lcw305cjq']

        >>> comm.messages.delete("all")
        """
        msg = f"broadcast-{self.get_id()}"
        self.put(msg, [f"{type}-{ipst}" for ipst in ipppssoots])
        return msg

    def ids(self, message_types="all"):
        """Given a list of `message_types`, return the list of unique
        ipppssoots such that each ipppssoot has at least one message
        of those types.
        """
        return list(set(msg.split("-")[1] for msg in self.list(message_types)))

    def list(self, prefix, max_objects=s3.MAX_LIST_OBJECTS):
        """List all objects related to `prefix,  removing any .trigger suffix."""
        for obj in super().list(prefix, max_objects=max_objects):
            if obj.endswith(".trigger"):  # XXXX Undo trigger hack
                obj = obj[: -len(".trigger")]
            yield obj


class InputsIo(S3Io):
    """InputsIo provides simple standard operations on the processing
    inputs store.

    >>> comm = get_io_bundle()
    >>> comm.inputs.path('lcw303cjq') #doctest: +ELLIPSIS
    's3://.../inputs/lcw303cjq'
    """

    def ids(self):
        """Return the ipppssoots associated with every input tarball."""
        return [tarball.split(".")[0] for tarball in self.list("all") if tarball]


class ControlIo(S3Io):
    """ControlIo provides simple standard operations on the processing
    control store.

    >>> comm = get_io_bundle()
    >>> comm.control.path('lcw303cjq/env') #doctest: +ELLIPSIS
    's3://.../control/lcw303cjq/env'
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


class MetadataIo(JsonIo):
    """Provides simple standard operations on the processing job control metadata,
    transparently serializing/de-serializing Python objects as a JSON encoded payload.

    Metadata is stored in the ipppssoot control folder as s3://.../control/ipppssoot/job.json

    >>> comm = get_io_bundle()

    >>> obj = {'job_params': {'memory': 1500, 'vcpus': 2}, 'job_id': '1cc5817c-8d93-4119-bbd4-25407ee233b5', 'retry': 0}
    >>> comm.xdata.put('lcw303cjq', obj)

    >>> list(comm.xdata.list_s3('lcw303cjq'))  #doctest: +ELLIPSIS
    ['s3://.../control/lcw303cjq/job.json']

    >>> comm.xdata.get('lcw303cjq')
    {'job_params': {'memory': 1500, 'vcpus': 2}, 'job_id': '1cc5817c-8d93-4119-bbd4-25407ee233b5', 'retry': 0}


    >>> comm.xdata.put('icw304cjq')
    >>> comm.xdata.put('jcw305cjq')
    >>> comm.xdata.put('lcw303cjq')
    >>> comm.xdata.listl()
    ['icw304cjq', 'jcw305cjq', 'lcw303cjq']

    >>> comm.xdata.delete("all")
    """

    def list(self, prefixes="all", max_objects=s3.MAX_LIST_OBJECTS):
        """Given S3 `prefixes` described earlier, use list_s3() to generate a
        sequence of listed objects and yield only the final prefix
        component of each listed object.

        Yield the ipppssoot folder name of each listed metadata file.
        """
        for s3_path in self.list_s3(prefixes, max_objects=max_objects):
            ipppssoot = s3_path.split("/")[-2]  # return ipppssoot folder
            if ipppssoot != "control":
                yield ipppssoot

    def path(self, ipppssoot):
        assert hst.IPPPSSOOT_RE.match(ipppssoot) or ipppssoot in ["all", ""], f"Bad ipppssoot {ipppssoot}"
        prefix = f"{ipppssoot}/job.json" if ipppssoot not in ["all", ""] else ""
        return super().path(prefix)


# -------------------------------------------------------------


class IoBundle:
    """Bundle all the I/O branches into one package."""

    def __init__(self, bucket=s3.DEFAULT_BUCKET, client=None):
        self.bucket = bucket if bucket.startswith("s3://") else "s3://" + bucket
        self.client = client or s3.get_default_client()
        self.messages = MessageIo(
            self.bucket + "/messages", self.client
        )  # i/o to message files of the form type-ipppssoot + all
        self.inputs = InputsIo(self.bucket + "/inputs", self.client)  # simple text inputs i/o, abitrary file prefix
        self.outputs = OutputsIo(self.bucket + "/outputs", self.client)  # simple text outputs i/o, abitrary file prefix
        self.control = ControlIo(self.bucket + "/control", self.client)  # simple text control i/o, abitrary file prefix
        self.xdata = MetadataIo(self.bucket + "/control", self.client)  # serialized object job control metadata i/o

    def reset(self, ids="all"):
        """Delete outputs, messages, and control files."""
        self.outputs.delete(ids)
        self.messages.delete(ids)
        self.xdata.delete(ids)  # IPPPSSOOT control metadata / retry status

    def clear(self, ids="all"):
        """Delete every S3 file managed by this IoBundle."""
        self.reset(ids)
        self.control.delete(ids)  # Memory model inputs
        self.inputs.delete(ids)  # Input tarballs


def get_io_bundle(bucket=s3.DEFAULT_BUCKET, client=None):
    return IoBundle(bucket, client)


# ------------------------------------------------------------


def test():
    from calcloud import io

    return doctest.testmod(io)


if __name__ == "__main__":
    if sys.argv[1] == "test":
        print(test())
