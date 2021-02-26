"""This lambda handles job terminations based on cancel-all or cancel-ipppssoot
S3 trigger messages.

For cancel-all,  the lambda first lists all error and terminated messages,  then
iterates through them issuing cancel-ipppssoot messages to trigger individual
lambdas to do the primary cancellation work.

When an individual cancel-ipppssoot message is processed:

1. The job's control metadata "terminated" flag is set to True
2. The batch.terminate_job function is called using the job_id in the control metadata
3. All messages for the ipppssoot are deleted.
4. The terminated-ipppssoot message is sent.

The control metadata of the cancelled ipppssoot is updated,  not deleted, in
order to short circuit memory based retries on subsequent rescues.
"""

from calcloud import batch
from calcloud import io
from calcloud import s3
from calcloud import hst


CLEANUP_TYPES = ["processing", "submit", "processed", "error"]


def lambda_handler(event, context):

    bucket_name, ipst = s3.parse_s3_event(event)

    comm = io.get_io_bundle(bucket_name)

    if ipst == "all":
        # Delete exactly the cancel-all message,  not every ipppssoot
        comm.messages.delete_literal("cancel-all")
        ipppssoots, already_cancelled = set(), set()
        for message in comm.messages.listl("all"):
            kind, ipst = message.split("-")
            if not hst.IPPPSSOOT_RE.match(ipst):
                continue
            if kind == "cancel":
                already_cancelled.add(ipst)
            else:
                ipppssoots.add(ipst)
        comm.messages.broadcast("cancel", ipppssoots - already_cancelled)
    else:
        metadata = comm.xdata.get(ipst)
        metadata["terminated"] = True
        comm.xdata.put(ipst, metadata)

        try:
            batch.terminate_job(metadata["job_id"], ipst, "Operator cancelled")
        except Exception as exc:
            print("Exception terminating", ipst, "was", exc)

        comm.messages.delete(f"all-{ipst}")
        comm.messages.put(f"terminated-{ipst}")
