"""This module is the primary path for job submission, for both
initial "placed" submissions and "rescue" submissions which are
triggered by the corresponding lambdas.

The key difference between "placed" and "rescue" submissions is that
placed submissions reset job control metadata to initial conditions
(primarily no retries yet) while rescue submissions merely use the
existing control data to drive job planning and job definition
(memory allocation) selection.

See the batch_event handler, rescue handler, and s3_trigger
handlers for more information on how jobs are initiated and
retried.
"""
import time

from . import plan
from . import submit


class CalcloudInputsFailure(RuntimeError):
    """The inputs needed to plan and run this job were not ready in time."""


def main(comm, ipppssoot, bucket_name):
    """Submit the job for `ipppssoot` using `bucket_name` and io bundle `comm`.

    1. Deletes all messages for `ipppssoot`.
    2. Creates a metadata file for `ipppssoot` if it doesn't exist already.
    3. Computes a job Plan leveraging the retry counter in the metadata file.
    4. Submits the Plan creating a Batch job.
    5. Saves the job_id reported by the Batch submission in the metadata file.
    6. Nominally sends "submit-ipppssoot" message.
    7. If an exception occurs but a terminate-ipppssoot message exists,
       a terminated-ipppssoot message is sent.
    8. If an exception occurs but a terminate-ipppssoot message does not exist,
       an error-ipppssoot messaage is sent.
    """
    try:
        terminated = comm.messages.listl(f"terminated-{ipppssoot}")
        _main(comm, ipppssoot, bucket_name)
    except Exception as exc:
        print(f"Exception in lambda_submit.main for {ipppssoot} = {exc}")
        if terminated:
            status = "terminated-" + ipppssoot
        else:
            status = "error-" + ipppssoot
        comm.messages.delete(f"all-{ipppssoot}")
        comm.messages.put({status: "submit lambda exception handler"})


def _main(comm, ipppssoot, bucket_name):
    """Core job submission function factored out of main() to clarify exception handling."""

    wait_for_inputs(comm, ipppssoot)

    comm.messages.delete(f"all-{ipppssoot}")
    comm.outputs.delete(f"{ipppssoot}")

    # retries don't climb ladder,  memory_retries do,  increasing bin sizes each try
    try:
        metadata = comm.xdata.get(ipppssoot)  # retry/rescue path
    except comm.client.exceptions.NoSuchKey:
        metadata = dict(retries=0, memory_retries=0, job_id=None, terminated=False)

    # get_plan() raises AllBinsTriedQuit when retries exhaust higher memory job definitions
    p = plan.get_plan(ipppssoot, bucket_name, f"{bucket_name}/inputs", metadata["memory_retries"])

    # Only reached if get_plan() defines a viable job plan
    print("Job Plan:", p)
    response = submit.submit_job(p)
    print("Submitted job for", ipppssoot, "as ID", response["jobId"])
    metadata["job_id"] = response["jobId"]
    comm.xdata.put(ipppssoot, metadata)
    comm.messages.put(f"submit-{ipppssoot}")


def wait_for_inputs(comm, ipppssoot):
    """Ensure that the inputs required to plan and run the job for `ipppssoot` are available.

    Each iteration,  check for the S3 message files which trigger submissions and abort if none
    are found.

    Eventually after 15 min (default) the lambda will die if it's still waiting.
    """
    input_tarball, memory_modeling = [], []
    while not input_tarball or not memory_modeling:
        input_tarball = comm.inputs.listl(f"{ipppssoot}.tar.gz")
        memory_modeling = comm.control.listl(f"{ipppssoot}/{ipppssoot}_MemModelFeatures.txt")
        if not comm.messages.listl([f"placed-{ipppssoot}", f"rescue-{ipppssoot}"]):
            raise CalcloudInputsFailure(
                f"Both the 'placed' and 'rescue' messages for {ipppssoot} have been deleted. Aborting input wait and submission."
            )
        if not input_tarball or not memory_modeling:
            print(
                f"Waiting for inputs for {ipppssoot}. input_tarball={input_tarball}  memory_modeling={memory_modeling}"
            )
            time.sleep(30)
    print(f"Inputs for {ipppssoot} found.")
