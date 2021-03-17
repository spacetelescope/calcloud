"""The clean lambda is used to remove all traces of the specified ipppssoots.

If clean-all is specified,  then all files related to processing any ipppssoot
are deleted.
"""

from calcloud import io
from calcloud import s3


def lambda_handler(event, context):

    bucket_name, ipst = s3.parse_s3_event(event)

    comm = io.get_io_bundle(bucket_name)

    if ipst == "all":
        print("Cleaning all;  removing all job resources (S3 files).")

        comm.messages.delete_literal("clean-all")  # don't interpret all as existing ipppssoots

        cleanup_ids = comm.ids("all")

        comm.messages.broadcast("clean", cleanup_ids)
    else:
        print("Cleaning", ipst)
        comm.clean(ipst)
