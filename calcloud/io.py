"""This module handles messaging and I/O layered on top of S3.
It hides the structure of the messaging system and provides a
simple API for putting, getting, listing, and deleting messages.
"""
import sys
import os
import doctest
import json
import uuid
import yaml

from calcloud import s3
from calcloud import hst
from calcloud import batch
from calcloud import log

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
    "clean",
]

MAX_BROADCAST_MSGS = 10**6  # safety

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
        return self.s3_path + "/" + prefix if prefix else self.s3_path

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

    def get(self, prefixes, encoding="utf-8"):
        """Return the contents of S3 file associated with `prefixes` if prefixes is a string.

        Otherwise return the dictionary mapping each element of `prefixes` to its contents.
        """
        if isinstance(prefixes, str):
            return s3.get_object(self.path(prefixes), client=self.client, encoding=encoding)
        else:
            return {prefix: self.get(prefix, encoding) for prefix in prefixes}

    def put(self, msgs, payload="", encoding="utf-8"):
        """Put messages `msgs` into S3,  accepting several forms.

        See normalize_put_parameters() for permissible values and handling of
        `msgs` and `payload`.

        """
        msgs = self.normalize_put_parameters(msgs, payload)
        for msg, value in msgs.items():
            s3.put_object(value, self.path(msg), encoding=encoding, client=self.client)

    def normalize_put_parameters(self, msgs, payload):
        """Consolidate put() parameters into normalized dictionary form where each item
        specifies a fully specified message and corresponding payload.

        Any payload must be specified as a string or bytes for

        The forms called with the default payload="" put an encoded empty string:

        1. "simple-message", ""
        2. ["simple-message1", "simple-message2", ...], ""

        The forms called specifying a non-empty payload use it for every message
        specifed as a string, tuple, list, or set:

        3. "simple-message", payload
        4. ["simple-message1", "simple-message2", ...], payload

        The dictionary form of `msgs` can specify a unique payload for every message in
        the dictionary.  Alternately if `payload` is specified it overrides any values
        specified by the dictionary:

        5. {"simple-message1" : "message-payload1", ...}, ""
        6. {"simple-message1" : payload, ...}, ""

        The form with string payloads specified write out the bytes resulting from
        encoding the payload with `encoding`.  Simple text messages as well as YAML
        or JSON serializations should "just work".  Use encoding=None to write out
        byte strings directly.
        """
        if isinstance(msgs, str):
            msgs = {msgs: payload}
        elif isinstance(msgs, (list, tuple, set)):
            msgs = {msg: payload for msg in msgs}
        elif isinstance(msgs, dict):
            msgs = dict((msg, payload or value) for (msg, value) in msgs.items())
        else:
            raise ValueError("msgs parameter to put() must be str, list, tuple, set, or dict.")
        return msgs

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

    def ids(self, prefixes="all"):
        """Return the list of unique ipppssoot/id directories associated with `prefixes`."""
        return list(set(obj.split("/")[0] for obj in self.list(prefixes) if obj))


# -------------------------------------------------------------


class PayloadIo(S3Io):
    """Abstract serializes/deserializes objects when putting/getting from S3."""

    loader = None
    _dumper = None

    def get(self, prefixes):
        """Return the decoded message object fetched from literal message name `prefixes` if
        prefix is a string,  otherwise return a dictionary {prefix: contents, ...} for each
        prefix in the sequence `prefixes`.
        """
        if isinstance(prefixes, str):
            text = super().get(prefixes)
            return self.loader(text)
        else:
            return {prefix: self.get(prefix) for prefix in prefixes}

    def put(self, msgs, payload="", encoding="utf-8"):
        """Put messages defined by message name `msgs` and payload `value`.

        See S3IO.normalize_put_parameters() for more information on permissible values
        for `msgs` and `payload`.

        Prior to putting, any payloads passed to S3Io, including the empty string,
        are encoded in JSON using json.dumps().

        See S3Io.put() for more information about putting JSON encoded payloads coming from
        JsonIo,  including handling of `encoding`.
        """
        msgs = self.normalize_put_parameters(msgs, payload)
        super().put({msg: self.dumper(value) for (msg, value) in msgs.items()}, encoding=encoding)

    def dumper(self, value):
        """Ensure the empty string is dumped as an empty string,  not serialization of empty string."""
        if value != "":
            return self._dumper(value)
        else:
            return ""


class JsonIo(PayloadIo):
    """Serialize to/from JSON before storing/loading message payloads."""

    loader = staticmethod(json.loads)
    _dumper = staticmethod(json.dumps)


class YamlIo(PayloadIo):
    """Serialize to/from YAML before storing/loading message payloads."""

    loader = staticmethod(yaml.safe_load)
    _dumper = staticmethod(yaml.dump)


class MessageIo(YamlIo):
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

    A special case exists for 'clean-ingested' where 'ingested' corresponds to every
    ipppssoot which already as an 'ingested-<ipppssoot>' message.

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

    A special case exists for 'clean-ingested' where 'ingested' corresponds to every
    ipppssoot which already as an 'ingested-<ipppssoot>' message.  This is a limited
    special case which may not support all methods and use cases.

    >>> comm.messages.put("clean-ingested")
    >>> comm.messages.listl()
    ['clean-ingested']

    >>> comm.messages.delete("all");
    >>> comm.messages.listl()
    []

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
        """For the MessageIo, expand_prefix() is used to customize the behavior of
        expand_all to handle message types.  expand_all() is used to generate a
        sequence of partial S3 keys which correspond to:

        1. "all messages of all types"    when prefix="all"
        2. "all types for one ipppssoot"  when prefix="all-{ipst}"
        3. "one type for one ipppssoot"   when prefix="{type}-{ipst}"
        4. "all ipppssoots of one type"   when prefix="{type}-{all}" also equivalent to "{type}"

        >>> comm = get_io_bundle()

        Used w/o -ipppssoot,  "all" expands into the all message types, which when used as S3 object
        key prefixes, match all ipppssoots of each type:

        >>> list(comm.messages.expand_all('all'))
        ['broadcast', 'placed', 'submit', 'processing', 'processed', 'error', 'ingesterror', 'ingested', 'terminated', 'cancel', 'rescue', 'clean']

        The message 'all-ipppssoot' expands into a sequence of type-ipppssoot messages for each
        type in MESSAGE_TYPES:

        >>> list(comm.messages.expand_all('all-lcw303cjq'))
        ['broadcast-lcw303cjq', 'placed-lcw303cjq', 'submit-lcw303cjq', 'processing-lcw303cjq', 'processed-lcw303cjq', 'error-lcw303cjq', 'ingesterror-lcw303cjq', 'ingested-lcw303cjq', 'terminated-lcw303cjq', 'cancel-lcw303cjq', 'rescue-lcw303cjq', 'clean-lcw303cjq']

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

    def broadcast(self, type, ipppssoots, payload=None):
        """Output a `type` message for each dataset in `ipppssoots`.  This
        is nominally done by sending a list of messages to the broadcast lambda
        which then sends them using a divide-and-conquer approach.

        A yaml-serializable `payload` may also be sent for all messages.

        >>> comm = get_io_bundle()

        Calling the broadcast method writes a single broadcast message containing a payload of messages to send.
        Broadcast messages are named using a random id instead of ipppssoot, a uuid with _ replacing -.

        >>> msg = comm.messages.broadcast("cancel", ["lcw303cjq", "lcw304cjq", "lcw305cjq"]);
        >>> comm.messages.listl() #doctest: +ELLIPSIS
        ['broadcast-..._..._..._..._...']

        The contents of a broadcast message is a dictionary defining:

        1. A list of messages which will be written to S3.
        2. A single optional payload object which is sent for all messages.

        by the lambda which processes broadcast messages:

        >>> comm.messages.pop(msg)
        {'messages': ['cancel-lcw303cjq', 'cancel-lcw304cjq', 'cancel-lcw305cjq'], 'payload': None}

        When the messages list a broadcast message contains large numbers of messages,  the message list is
        partitioned into two half-length lists and re-broadcast.

        When the message list is sufficiently small,  each message is sent serially and
        requires ~50-200 msec each.   So e.g. 100 serial messages might take 5-20 seconds.

        A key purpose of message payloads is to pass override parameters into lambda handlers for messages
        such as 'place' or 'rescue':

        >>> comm.messages.put('rescue-lcw303cjq', { "timeout_scale" : 1.25 })
        >>> comm.messages.get('rescue-lcw303cjq')
        {'timeout_scale': 1.25}

        While it could be individualized,  for simplicity broadcast nominally sends the same payload
        to all child messages.

        >>> msg = comm.messages.broadcast("rescue", ['lcw303cjq', 'lcw304cjq', 'lcw305cjq'], {"timeout_scale" : 1.3})
        >>> comm.messages.pop(msg)
        {'messages': ['rescue-lcw303cjq', 'rescue-lcw304cjq', 'rescue-lcw305cjq'], 'payload': {'timeout_scale': 1.3}}

        >>> comm.messages.delete("all")

        """
        assert type in MESSAGE_TYPES
        assert type != "broadcast"  # don't broadcast broadcasts....
        assert isinstance(ipppssoots, list)
        assert not len(ipppssoots) or isinstance(ipppssoots[0], str)
        assert "all" not in ipppssoots  # don't broadcast message tails of "all"
        assert len(ipppssoots) < MAX_BROADCAST_MSGS
        msg = f"broadcast-{self.get_id()}"
        self.put(msg, dict(messages=[f"{type}-{ipst}" for ipst in ipppssoots], payload=payload))
        return msg

    def bifurcate_broadcast(self, messages, payload):
        """Given the `messages` and object `payload` of a broadcast message,  send two new
        broadcast messages,  each with half the original messages and same payload.

        Returns (broadcast_msg_name1, broadcast_msg_name2)

        >>> comm = get_io_bundle()

        >>> msg1, msg2 = comm.messages.bifurcate_broadcast(
        ...    ['rescue-lcw303cjq', 'rescue-lcw304cjq', 'rescue-lcw305cjq'], {'timeout_scale' : 1.3})

        >>> comm.messages.listl() #doctest: +ELLIPSIS
        ['broadcast-..._..._..._..._...', 'broadcast-..._..._..._..._...']

        >>> comm.messages.pop(msg1)
        {'messages': ['rescue-lcw303cjq'], 'payload': {'timeout_scale': 1.3}}
        >>> comm.messages.pop(msg2)
        {'messages': ['rescue-lcw304cjq', 'rescue-lcw305cjq'], 'payload': {'timeout_scale': 1.3}}
        """
        msg1, msg2 = f"broadcast-{self.get_id()}", f"broadcast-{self.get_id()}"
        self.put(msg1, dict(messages=messages[: len(messages) // 2], payload=payload))
        self.put(msg2, dict(messages=messages[len(messages) // 2 :], payload=payload))
        return msg1, msg2

    def ids(self, message_types="all"):
        """Given a list of `message_types`, return the list of unique
        ipppssoots such that each ipppssoot has at least one message
        of those types.

        >>> comm = get_io_bundle()
        >>> comm.messages.put(['cancel-lcw303cjq', 'cancel-lcw304cjq', 'error-lcw303cjq'])

        >>> result = comm.messages.ids(["cancel", "error"])
        >>> assert set(result) == set(['lcw303cjq', 'lcw304cjq'])

        >>> comm.messages.ids("error")
        ['lcw303cjq']

        >>> comm.messages.ids("placed")
        []

        >>> comm.messages.delete("all")
        """
        return list(set(msg.split("-")[1] for msg in self.list(message_types)))

    def list(self, prefix, max_objects=s3.MAX_LIST_OBJECTS):
        """List all objects related to `prefix,  removing any .trigger suffix."""
        for obj in super().list(prefix, max_objects=max_objects):
            if obj.endswith(".trigger"):  # XXXX Undo trigger hack
                obj = obj[: -len(".trigger")]
            yield obj

    def reset(self, ids):
        """Delete all messages associated with `ids` which are nominally
        ipppssoots or other message tails.
        """
        if isinstance(ids, str):
            ids = [ids]
        self.delete(["all-" + id for id in ids])


class InputsIo(S3Io):
    """InputsIo provides simple standard operations on the processing
    inputs store.

    >>> comm = get_io_bundle()
    >>> comm.inputs.path('lcw303cjq') #doctest: +ELLIPSIS
    's3://.../inputs/lcw303cjq'
    """

    def ids(self, prefixes="all"):
        """Return the ipppssoots associated with every input tarball.

        >>> comm = get_io_bundle()

        >>> comm.inputs.put(["j6d511gvq.tar.gz", "j6m901040.tar.gz"])

        >>> result = comm.inputs.ids()
        >>> assert set(result) == set(['j6d511gvq', 'j6m901040'])

        >>> comm.inputs.delete("all")
        """
        return [tarball.split(".")[0] for tarball in self.list(prefixes) if tarball]


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

    >>> comm.outputs.delete("all");
    >>> comm.outputs.put("j6d511gvq/j6d511gvq.tar.gz")
    >>> comm.outputs.put("j6d511gvq/process_metrics.txt")
    >>> comm.outputs.put("j6m901040/preview.txt")
    >>> result = comm.outputs.ids()
    >>> assert set(result) == set(['j6d511gvq', 'j6m901040'])

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


# Control values can be sent as part of message override payloads or can be recorded in comm.xdata.
# XXXX NOTE: value checks are not currently active,  only field name and type.
CONTROL_KEYWORDS = {
    "cancel_type": ((str,), lambda x: x in ("job_id", "ipppssoot")),
    "job_id": ((str,), batch.JOB_ID_RE.match),
    "memory_bin": ((int, type(None)), lambda x: x in (0, 1, 2, 3, None)),
    "terminated": ((bool,), lambda x: True),
    "timeout_scale": ((int, float), lambda x: x > 0),
    "ipppssoot": ((str,), hst.IPPPSSOOT_RE.match),
    "bucket": ((str,), lambda x: True),
    "job_name": ((str,), lambda x: True),
    "exit_code": ((int, str), lambda x: True),
    "exit_reason": ((str,), lambda x: True),
    "exit_status": ((str,), lambda x: True),
    "status_reason": (
        (
            int,
            str,
        ),
        lambda x: True,
    ),
    "container_reason": (
        (
            int,
            str,
        ),
        lambda x: True,
    ),
    "memory_retries": ((int,), lambda x: x >= 0),
    "retries": ((int,), lambda x: x >= 0),
}


def validate_control(metadata):
    """Check the `metadata` dictionary for valid keywords and value types."""
    log.info("Validating control metadata", metadata)
    if metadata is None:
        return {}
    if not isinstance(metadata, dict):
        raise ValueError("Job metadata isn't a dict.")
    for key, value in metadata.items():
        defined = CONTROL_KEYWORDS.get(key)
        if defined:
            valid_types = defined[0]
            if not isinstance(value, valid_types):
                raise ValueError(f"Control value for {key} should be one of these types: {valid_types}.")
            # f_valid_value = defined[1]
            # if not f_valid_value(value):
            #    raise ValueError(f"Control value for {key} is not valid.")
        else:
            raise ValueError(f"Control keyword {key} is not one of {sorted(list(CONTROL_KEYWORDS))}.")
    return metadata


def get_default_metadata():
    """Return the default metadata needed to run the planner if no corresponding overrides or control data
    are defined.
    """
    return dict(retries=0, memory_retries=0, memory_bin=None, job_id="undefined", terminated=False, timeout_scale=1.0)


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
        if ids == "all":
            ids = self.messages.ids()
        if isinstance(ids, str):
            ids = [ids]
        for tail in ids:
            with log.trap_exception():
                self.outputs.delete(tail)
            with log.trap_exception():
                self.messages.reset(tail)  # messages.delete() doesn't handle "ipppssoot", only "type-ipppssoot".
            with log.trap_exception():
                self.xdata.delete(tail)  # IPPPSSOOT control metadata / retry status

    def clean(self, ids="all"):
        """Delete every S3 file associated with `ids` which specifies one of:

        1. ipppssoot  -  clean one ipppssoot
        2. [ipppssoot, ...]
        3. "all"

        """
        if isinstance(ids, str):
            ids = [ids]
        for id in ids:
            with log.trap_exception():
                self.reset(ids)
            with log.trap_exception():
                self.control.delete(ids)  # Memory model inputs
            with log.trap_exception():
                self.inputs.delete(ids)  # Input tarballs

    def ids(self, prefixes="all"):
        """Return the id associated with every object in any branch of this comm
        bundle.
        """
        ids = set()
        ids = ids | set(self.inputs.ids(prefixes))  # tarball root
        ids = ids | set(self.outputs.ids(prefixes))  # ipppssoot directory
        ids = ids | set(self.control.ids(prefixes))  # ipppssoot directory
        ids = ids | set(self.messages.ids(prefixes))  # ipppssoots / message tails
        return list(ids)

    def list_s3(self, prefixes="all"):
        """Return the S3 listing of all branches of the comm bundle."""
        items = []
        items.extend(list(self.inputs.list_s3(prefixes)))
        items.extend(list(self.control.list_s3(prefixes)))
        items.extend(list(self.messages.list_s3(prefixes)))
        items.extend(list(self.outputs.list_s3(prefixes)))
        return items

    def send(self, msg_type, ipppssoots="all"):
        """Send the message `msg_type` to every ipppssoot in `ipppssoots`.

        If ipppssoots="all", define ipppssoots using self.messsages.ids()
        """
        if ipppssoots == "all":
            ipppssoots = self.inputs.ids()
        assert msg_type in MESSAGE_TYPES
        self.messages.put([msg_type + "-" + ipppssoot for ipppssoot in ipppssoots])


def get_io_bundle(bucket=s3.DEFAULT_BUCKET, client=None):
    """Return the IoBundle defined by root S3 `bucket` and accessed using
    S3 `client`.
    """
    _reject_cross_env_bucket(bucket)
    return IoBundle(bucket, client)


def _reject_cross_env_bucket(bucket):
    """Raise an exception if `bucket` does not match BUCKET in os.environ in order to
    short circuit lambdas executing based on events from other environments.
    """
    bucket1, _null = s3.s3_split_path(bucket)
    bucket2, _null = s3.s3_split_path(os.environ["BUCKET"])
    if bucket1 != bucket2:
        raise RuntimeError(f"Cross-environment bucket mismatch for normalized caller={bucket1} os.environ={bucket2}")


# ------------------------------------------------------------


def test():
    from calcloud import io

    return doctest.testmod(io)


if __name__ == "__main__":
    if sys.argv[1] == "test":
        print(test())
