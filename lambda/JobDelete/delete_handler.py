from calcloud import batch
from calcloud import io


def lambda_handler(event, context):

    print(event)

    message = event["Records"][0]["s3"]["object"]["key"]
    print(f"received {message}")

    # some generic variables we'll need
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    ipst = message.split("-")[-1]

    # these types of messages on any deleted ipppssoot will be deleted
    # cleanup_messages = ["processing-", "submit-", "processed-", "error-"]
    #
    # these Batch job status states are cancellable
    # cancelStates = ["RUNNING", "SUBMITTED", "PENDING", "RUNNABLE", "STARTING"]

    comm = io.get_io_bundle(bucket_name)

    if ipst == "all":
        # what we don't want is to delete cancel-ipppssoot for all ipppsssots.
        comm.messages.delete_literal("cancel-all")
        control_files = comm.control.list("all", max_objects=100)
        cancelled = False
        for existing in control_files:
            cancelled = cancelled or cancel(comm, existing)
        if cancelled:
            comm.messages.put("cancel-all")
    else:
        cancel(comm, ipst)


def cancel(comm, ipst):
    ctrl_msg = comm.control.get(ipst)
    comm.control.delete(ipst)  # this prevents retries
    try:
        batch.terminate_job(ctrl_msg["job_id"], ipst, "Operator cancelled")
    except Exception as exc:
        print("Exception terminating", ipst, "was", exc)
    comm.messages.delete(f"all-{ipst}")
    # comm.outputs.delete(ipst)   ???
    comm.messages.put(f"terminated-{ipst}")
    return True
