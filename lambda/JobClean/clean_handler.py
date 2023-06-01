"""The clean lambda is used to remove all traces of the specified datasets.

If clean-all is specified,  then all files related to processing any dataset
are deleted.
"""

from calcloud import io
from calcloud import s3


def lambda_handler(event, context):
    bucket_name, dataset = s3.parse_s3_event(event)

    comm = io.get_io_bundle(bucket_name)

    if dataset == "all":
        print("Cleaning all datasets;  removing all job resources (S3 files).")

        comm.messages.delete_literal("clean-all")  # don't interpret all as existing datasets

        cleanup_ids = comm.ids("all")

        comm.messages.broadcast("clean", cleanup_ids)
    elif dataset == "ingested":  # a variation of "all" restricted to datasets with an ingest message
        print("Cleaning all ingested datasets;  removing all job resources (S3 files).")

        comm.messages.delete_literal("clean-ingested")  # don't interpret "ingested"

        cleanup_ids = comm.messages.ids("ingested")

        comm.messages.broadcast("clean", cleanup_ids)
    else:
        print("Cleaning", dataset)
        comm.clean(dataset)
