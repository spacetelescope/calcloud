"""This module is used to create processing resourcess given a list of ipppssoots and parameters to
define outputs locations.

The idea behind creating resourcess is to generate enough information such that an ipppssoot or
set of ipppssoots can be assigned to well tuned processing resources.
"""
import sys
import os
from collections import namedtuple

from . import hst
from . import metrics
from . import log
from . import s3

# ----------------------------------------------------------------------

OUTLIER_THRESHHOLD_MEGABYTES = 8192 - 128  # m5.large - 128M ~overhead

JobResources = namedtuple(
    "JobResources",
    [
        "ipppssoot",
        "instrument",
        "job_name",
        "s3_output_uri",
        "input_path",
        "crds_config",
        "vcpus",
        "memory",
        "max_seconds",
    ],
)

JobEnv = namedtuple("JobEnv", ("job_queue", "job_definition", "command"))

Plan = namedtuple("Plan", JobResources._fields + JobEnv._fields)

# ----------------------------------------------------------------------

# This is the top level entrypoint called from calcloud.lambda_submit.main
# It returns a Plan() tuple which is passed to the submit function.
#
# It's the expectation that most/all of this file will be re-written during
# the integration of new memory requirements modelling and new AWS Batch
# infrastructure allocation strategies.   The signature of the get_plan()
# function is the main thing to worry about changing externally.

def get_plan(ipppssoot, output_bucket, input_path, memory_retries=0):
    """Given the resource requirements for a job,  map them onto appropriate
    requirements and Batch infrastructure needed to process the job.

    ipppssoot          dataset ID to plan
    output_bucket      S3 output bucket,  top level
    input_path
    memory_retries     increasing counter of retries with 0 being first try,
                       intended to drive increasing memory for each subsequent retry
                       with the maximum retry value set in Terraform.

    Returns    Plan   (named tuple)
    """
    job_resources = get_resources(ipppssoot, output_bucket, input_path, memory_retries)
    env = _get_environment(job_resources)
    return Plan(*(job_resources + env))


def get_resources(ipppssoot, output_bucket, input_path, retries=0):
    """Given an HST IPPPSSOOT ID,  return information used to schedule it as a batch job.

    Conceptually resource requirements can be tailored to individual IPPPSSOOTs.

    This defines abstract memory and CPU requirements independently of the AWS Batch
    resources used to satisfy them.

    Returns:  JobResources named tuple
    """
    ipppssoot = ipppssoot.lower()
    s3_output_uri = f"{output_bucket}/outputs/{ipppssoot}"
    instr = hst.get_instrument(ipppssoot)
    job_name = ipppssoot
    input_path = input_path
    crds_config = "caldp-config-offsite"
    return JobResources(
        *(ipppssoot, instr, job_name, s3_output_uri, input_path, crds_config)
        + _get_job_resources(instr, ipppssoot, retries)
    )


def _get_environment(job_resources):
    job_resources = JobResources(*job_resources)
    job_definition = os.environ["JOBDEFINITION"]
    normal_queue = os.environ["NORMALQUEUE"]
    outlier_queue = os.environ["OUTLIERQUEUE"]

    if job_resources.memory <= OUTLIER_THRESHHOLD_MEGABYTES:
        return JobEnv(normal_queue, job_definition, "caldp-process")
    else:
        return JobEnv(outlier_queue, job_definition, "caldp-process")


def _get_job_resources(instr, ipppssoot, retries=0):
    """Given the instrument `instr` and dataset id `ipppssoot`...

    Return  required resources (cores, memory in M,  seconds til kill)

    Note that these are "required" and still need to be matched to "available".
    """
    info = [0] * 3
    try:
        memory_megabytes, cpus, wallclock_seconds = metrics.get_resources(ipppssoot)
        info[0] = cpus
        info[1] = memory_megabytes + 512  # add some overhead for AWS Batch (>= 32M) and measurement error
        info[2] = max(int(wallclock_seconds * cpus * 6), 120)  # kill time,  BEWARE:  THIS LOOKS WRONG
    except KeyError:
        info = (32, 64 * 1024, int(60 * 60 * 48))  # 32 cores,  64G/72G,  48 hours max   (c5.9xlarge)
        log.warning("Defaulting (cpu, memory, time) requirements for unknown dataset:", ipppssoot, "to", info)
    return tuple(info)


# ----------------------------------------------------------------------


def test():
    import doctest
    from calcloud import plan
    return doctest.testmod(plan, optionflags=doctest.ELLIPSIS)


# ----------------------------------------------------------------------


def _planner(ipppssoots_file, output_bucket=s3.DEFAULT_BUCKET + "/outputs", input_path=s3.DEFAULT_BUCKET, retries=0):
    """Given a set of ipppssoots in `ipppssoots_file` separated by spaces or newlines,
    as well as an `output_bucket` to define how the jobs are named and
    where outputs should be stored,  print out the associated batch resources tuples which
    can be submitted.
    """
    for line in open(ipppssoots_file).readlines():
        if line.strip().startswith("#"):
            continue
        for ipst in line.split():
            print(
                tuple(get_plan(ipst, output_bucket, input_path, retries))
            )  # Drop type to support literal_eval() vs. eval()


if __name__ == "__main__":
    if len(sys.argv) in [2, 3, 4, 5]:
        if sys.argv[1] == "test":
            print(test())
        else:
            # ipppssoots_file = sys.argv[1] # filepath listing ipppssoots to plan
            # output_bucket = sys.argv[2]   # 's3://calcloud-processing'
            # inputs = sys.argv[3]          #  astroquery: or S3 inputs
            # retries = sys.argv[4]         #  0..N
            _planner(*sys.argv[1:])
    else:
        print(
            "usage: python -m calcloud.plan  <ipppssoots_file>  [<output_bucket>]  [input_path]  [retry]",
            file=sys.stderr,
        )
