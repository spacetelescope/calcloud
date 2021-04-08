"""This lambda handles job terminations based on cancel-all or cancel-ipppssoot
S3 trigger messages.

For cancel-all,  the lambda first determines the job id's of all jobs in a killable
state,  then broadcasts the cancel-job_id form of single job kill message.

For cancel-job_id,  the lambda determines the ipppssoot from the job name,  kills
the job,  and adjusts messages and the control file based on the ipppssoot.

For cancel-ipppssoot,  the lambda determines the job_id from the control file,  kills
the job,  and adjusts messages and the control file based on the ipppssoot.

1. The job's control metadata "terminated" flag is set to True.
2. The batch.terminate_job function is called.
3. All messages for the ipppssoot are deleted.
4. The terminated-ipppssoot message is sent.

The control metadata of the cancelled ipppssoot is updated,  not deleted, in
order to short circuit memory based retries on subsequent rescues.
"""

import contextlib

from calcloud import batch
from calcloud import io
from calcloud import s3
from calcloud import hst


def lambda_handler(event, context):

    bucket_name, ipst = s3.parse_s3_event(event)

    comm = io.get_io_bundle(bucket_name)

    if ipst == "all":
        # Delete exactly the cancel-all message,  not every ipppssoot
        comm.messages.delete_literal("cancel-all")

        # Define jobs as anything with a control metadata file
        # ipppssoots = comm.xdata.listl("all")
        # comm.messages.broadcast("cancel", ipppssoots)

        # Cancel all jobs in a killable state one-by-one using broadcast
        comm.messages.broadcast("cancel", batch.get_job_ids())
    else:
        cancel_one(comm, ipst)


def cancel_one(comm, ipst):
    """Cancel one job based on `ipst` which should either be an ipppssoot or Batch job id."""

    if hst.IPPPSSOOT_RE.match(ipst):  # most likely from singleton operator messages
        metadata = dict(job_id="unknown")
        with trap_exception("retrieving control file for", ipst):
            metadata = comm.xdata.get(ipst)
        job_id = metadata["job_id"]
        metadata["cancel_type"] = "ipppssoot"
    elif batch.JOB_ID_RE.match(ipst):  # most likely from cancel-all broadcast
        comm.messages.delete(f"cancel-{ipst}")  # job-id form of cancel message
        job_id, ipst = ipst.replace("_", "-"), "unknown"
        metadata = dict(job_id=job_id, cancel_type="job_id")
        with trap_exception("describing job", job_id, "to determine ipppssoot."):
            ipst = batch.get_job_name(job_id)  # ipst or "unknown"
    else:
        print("Bad cancel ID", ipst)
        return

    print("Cancelling ipppssoot", ipst, "job_id", job_id)

    if ipst != "unknown":  # can't update control metadata or messages w/o ipppssoot
        with trap_exception("updating control file for", ipst, "job_id", job_id):
            metadata["terminated"] = True
            comm.xdata.put(ipst, metadata)

        with trap_exception("handling messages for", ipst, "job_id", job_id):
            comm.messages.delete(f"all-{ipst}")
            comm.messages.put({f"terminated-{ipst}": "cancel lambda"})

    if job_id != "unknown":  # can't cancel job w/o job_id
        with trap_exception("terminating", ipst, "job_id", job_id):
            batch.terminate_job(job_id, ipst, "Operator cancelled")


@contextlib.contextmanager
def trap_exception(*args):
    """Print a message and continue on exception inside with-block."""
    try:
        yield
    except Exception as exc:
        print("Exception", *args, "was:", exc)
