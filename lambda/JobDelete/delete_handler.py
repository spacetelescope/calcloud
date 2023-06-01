"""This lambda handles job terminations based on cancel-all or cancel-dataset
S3 trigger messages.

For cancel-all,  the lambda first determines the job id's of all jobs in a killable
state,  then broadcasts the cancel-job_id form of single job kill message.

For cancel-job_id,  the lambda determines the dataset from the job name,  kills
the job,  and adjusts messages and the control file based on the dataset.

For cancel-dataset,  the lambda determines the job_id from the control file,  kills
the job,  and adjusts messages and the control file based on the dataset.

1. The job's control metadata "terminated" flag is set to True.
2. The batch.terminate_job function is called.
3. All messages for the dataset are deleted.
4. The terminated-dataset message is sent.

The control metadata of the cancelled dataset is updated,  not deleted, in
order to short circuit memory based retries on subsequent rescues.
"""

from calcloud import batch
from calcloud import io
from calcloud import s3
from calcloud import log
from calcloud import hst


def lambda_handler(event, context):
    bucket_name, dataset = s3.parse_s3_event(event)

    comm = io.get_io_bundle(bucket_name)

    if dataset == "all":
        # Delete exactly the cancel-all message,  not every dataset
        comm.messages.delete_literal("cancel-all")
        # Cancel all jobs in a killable state broadcasting cancel over job_ids
        job_ids = batch.get_job_ids()
        comm.messages.broadcast("cancel", job_ids)
    elif batch.JOB_ID_RE.match(dataset):
        job_id, dataset = dataset, "unknown"  # kill one job, dataset = job_id
        print("Cancelling job_id", job_id)
        comm.messages.delete_literal(f"cancel-{job_id}")
        with log.trap_exception("Handling messages + control for", job_id):
            dataset = batch.get_job_name(job_id)
            print("Handling messages and control for", dataset)
            comm.messages.delete(f"all-{dataset}")
            comm.messages.put(f"terminated-{dataset}", "cancel lambda " + bucket_name)
            try:
                metadata = comm.xdata.get(dataset)
            except comm.xdata.client.exceptions.NoSuchKey:
                metadata = dict(job_id=job_id, cancel_type="job_id")
            metadata["terminated"] = True
            comm.xdata.put(dataset, metadata)
        # Do last so terminate flag is set if possible.
        print("Terminating", job_id)
        batch.terminate_job(job_id, "Operator cancelled")
    elif hst.IPPPSSOOT_RE.match(dataset) or hst.SVM_RE.match(dataset) or hst.MVM_RE.match(dataset):  # kill one dataset
        print("Cancelling dataset", dataset)
        comm.messages.delete(f"all-{dataset}")
        comm.messages.put(f"terminated-{dataset}", "cancel lambda " + bucket_name)
        metadata = comm.xdata.get(dataset)
        metadata["terminated"] = True
        metadata["cancel_type"] = "dataset"
        comm.xdata.put(dataset, metadata)
        job_id = metadata["job_id"]
        with log.trap_exception("Terminating", job_id):
            print("Terminating", job_id)
            batch.terminate_job(job_id, "Operator cancelled")
    else:
        raise ValueError("Bad cancel ID", dataset)
