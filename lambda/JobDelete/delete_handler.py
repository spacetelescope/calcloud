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

from calcloud import batch
from calcloud import io
from calcloud import s3
from calcloud import log


def lambda_handler(event, context):

    bucket_name, ipst = s3.parse_s3_event(event)

    comm = io.get_io_bundle(bucket_name)

    if ipst == "all":
        # Delete exactly the cancel-all message,  not every ipppssoot
        comm.messages.delete_literal("cancel-all")
        # Cancel all jobs in a killable state broadcasting cancel over job_ids
        job_ids = batch.get_job_ids()
        comm.messages.broadcast("cancel", job_ids)
    elif batch.JOB_ID_RE.match(ipst):  # kill one job
        comm.messages.delete(f"cancel-{ipst}")
        job_id, ipst = ipst.replace("_", "-"), "unknown"
        metadata = dict(job_id=job_id, cancel_type="job_id")
        ipst = batch.get_job_name(job_id)  # ipst or "unknown"

        print("Cancelling ipppssoot", ipst, "job_id", job_id)

        with log.trap_exception("updating control file for", ipst, "job_id", job_id):
            metadata["terminated"] = True
            comm.xdata.put(ipst, metadata)
        with log.trap_exception("handling messages for", ipst, "job_id", job_id):
            comm.messages.delete(f"all-{ipst}")
            comm.messages.put(f"terminated-{ipst}", "cancel lambda " + comm.bucket)
        with log.trap_exception("terminating", ipst, "job_id", job_id):
            batch.terminate_job(job_id, ipst, "Operator cancelled")
    else:
        raise ValueError("Bad cancel ID", ipst)
