"""The rescue lambda restarts failed jobs after first deleting all messages
and outputs.

For the rescue-all form of trigger,  all error and terminated messages are
used to identify the set of ipppssoots to rescue.

A key feature of "rescuing" is the deletion of prior job outputs,  if any.
"""

from calcloud import io
from calcloud import lambda_submit
from calcloud import s3

RESCUE_TYPES = ["error", "terminated"]

MAX_PER_LAMBDA = 100


def lambda_handler(event, context):

    bucket_name, ipst = s3.parse_s3_event(event)

    comm = io.get_io_bundle(bucket_name)

    if ipst == "all":
        print("Rescuing all")
        comm.messages.delete_literal("rescue-all")  # don't interpret all as existing ipppssoots
        rescues = set()
        for message in comm.messages.list(RESCUE_TYPES):
            kind, ipst = message.split("-")
            rescues.add(ipst)
        comm.messages.broadcast("rescue", rescues)
    else:
        print("Rescuing", ipst)
        comm.outputs.delete(ipst)
        lambda_submit.main(comm, ipst, bucket_name)
