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
import os

from . import plan
from . import submit
from . import log
from . import io
from . import hst


class CalcloudInputsFailure(RuntimeError):
    """The inputs needed to plan and run this job were not ready in time."""


def main(comm, dataset, bucket_name, overrides):
    """Submit the job for `dataset` using `bucket_name` and io bundle `comm`.
    Control parameters can be overridden by dictionary `overrides`.

    1. Deletes all messages for `dataset`.
    2. Creates a metadata file for `dataset` if it doesn't exist already.
    3. Computes a job Plan leveraging the retry counter in the metadata file.
    4. Submits the Plan creating a Batch job.
    5. Saves the job_id reported by the Batch submission in the metadata file.
    6. Nominally sends "submit-dataset" message.
    7. If an exception occurs but a terminate-dataset message exists,
       a terminated-dataset message is sent.
    8. If an exception occurs but a terminate-dataset message does not exist,
       an error-dataset messaage is sent.
    """
    try:
        terminated = comm.messages.listl(f"terminated-{dataset}")
        _main(comm, dataset, bucket_name, overrides)
    except Exception as exc:
        log.error(f"Exception in lambda_submit.main for {dataset} = {exc}")
        if terminated:
            msg_name = "terminated-" + dataset
        else:
            msg_name = "error-" + dataset
        comm.messages.delete(f"all-{dataset}")
        comm.messages.put(
            msg_name, payload=dict(where="submit lambda exception handler " + bucket_name, exception=str(exc))
        )


def _main(comm, dataset, bucket_name, overrides):
    """Core job submission function factored out of main() to clarify exception handling."""

    overrides = io.validate_control(overrides)

    # get dataset type: ipst, svm, or mvm
    dataset_type = hst.get_dataset_type(dataset)

    _wait_for_inputs(comm, dataset)

    comm.messages.delete(f"all-{dataset}")
    comm.outputs.delete(f"{dataset}")

    # retries don't climb ladder,  memory_retries do,  increasing bin sizes each try
    try:
        metadata = comm.xdata.get(dataset)  # retry/rescue path
    except comm.xdata.client.exceptions.NoSuchKey:
        metadata = io.get_default_metadata()
    metadata = io.validate_control(metadata)
    metadata.update(overrides)

    # get_plan() raises AllBinsTriedQuit when retries exhaust higher memory job definitions
    p = plan.get_plan(dataset, dataset_type, bucket_name, f"{bucket_name}/inputs", metadata)

    # Only reached if get_plan() defines a viable job plan
    log.info("Job Plan:", p)
    response = submit.submit_job(p)
    log.info("Submitted job for", dataset, "as ID", response["jobId"])
    metadata["job_id"] = response["jobId"]
    comm.xdata.put(dataset, metadata)
    comm.messages.put(f"submit-{dataset}")


def _wait_for_inputs(comm, dataset):
    """Ensure that the inputs required to plan and run the job for `dataset` are available.

    Each iteration,  check for the S3 message files which trigger submissions and abort if none
    are found.

    Eventually after 15 min (default) the lambda will die if it's still waiting.  Instead,  if
    it's still running at 14 minutes an exception is raised to force cleanup and send and error message.
    """
    poll_seconds, seconds_to_fail = 30, int(os.environ.get("SUBMIT_TIMEOUT", 14 * 60))
    input_tarball, memory_modeling = [], []
    while not input_tarball or not memory_modeling:
        input_tarball = comm.inputs.listl(f"{dataset}.tar.gz")
        memory_modeling = comm.control.listl(f"{dataset}/{dataset}_MemModelFeatures.txt")
        if not comm.messages.listl([f"placed-{dataset}", f"rescue-{dataset}"]):
            raise CalcloudInputsFailure(
                f"Both the 'placed' and 'rescue' messages for {dataset} have been deleted. Aborting input wait and submission."
            )
        if not input_tarball or not memory_modeling:
            log.info(
                f"Waiting for inputs for {dataset} time remaining={seconds_to_fail}. input_tarball={len(input_tarball)}  memory_modeling={len(memory_modeling)}"
            )
            time.sleep(poll_seconds)
            seconds_to_fail -= poll_seconds
            if seconds_to_fail <= 0:
                raise CalcloudInputsFailure(
                    f"Wait for inputs for {dataset} timeout, aborting submission.  input_tarball={len(input_tarball)}  memory_modeling={len(memory_modeling)}"
                )
    log.info(f"Inputs for {dataset} found.")
