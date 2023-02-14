"""The rescue lambda restarts failed jobs after first deleting all messages
and outputs.

For the rescue-all form of trigger,  all error and terminated messages are
used to identify the set of datasets to rescue.

A key feature of "rescuing" is the deletion of prior job outputs,  if any.
"""

from calcloud import io
from calcloud import lambda_submit
from calcloud import s3

RESCUE_TYPES = ["error", "terminated"]

MAX_PER_LAMBDA = 100


def lambda_handler(event, context):
    bucket_name, dataset = s3.parse_s3_event(event)

    comm = io.get_io_bundle(bucket_name)

    overrides = comm.messages.get(f"rescue-{dataset}")

    if dataset == "all":
        print("Rescuing all")

        comm.messages.delete_literal("rescue-all")  # don't interpret all as existing datasets

        rescues = comm.messages.ids(RESCUE_TYPES)

        comm.messages.broadcast("rescue", rescues, overrides)
    else:
        print("Rescuing", dataset)
        # comm.outputs.delete(dataset)
        lambda_submit.main(comm, dataset, bucket_name, overrides)
