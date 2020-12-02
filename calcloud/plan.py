"""This module is used to create processing resourcess given a list of ipppssoots and parameters to
define outputs locations.

The idea behind creating resourcess is to generate enough information such that an ipppssoot or
set of ipppssoots can be assigned to well tuned processing resources.
"""
import sys
import datetime
import math
from collections import namedtuple

from . import hst
from . import metrics
from . import log

# ----------------------------------------------------------------------

def get_batch_name(name):
    when = datetime.datetime.now().isoformat()
    when = when.replace(":","-")
    when = when.replace(".","-")
    return name + "-" + when[:-7]   # drop subseconds

# One key function of JOB_DEFINITION appears to be indelible declaration of Docker image.
# New image == new definition required.

"""
WFC3: 95 per duration 0.93 hr
WFC3: 99 per duration 1.79 hr
WFC3: 95 per mem 0.83 gb
WFC3: 99 per mem 0.97 gb
ACS: 95 per duration 3.52 hr
ACS: 99 per duration 6.33 hr
ACS: 95 per mem 1.08 gb
ACS: 99 per mem 2.38 gb
COS: 95 per duration 0.14 hr
COS: 99 per duration 0.31 hr
COS: 95 per mem 0.83 gb
COS: 99 per mem 1.05 gb
STIS: 95 per duration 0.12 hr
STIS: 99 per duration 0.24 hr
STIS: 95 per mem 0.64 gb
STIS: 99 per mem 1.0 gb
"""

# For optimization with AWS Batch, key insights are:
#
# batch-queue    -- defines which compute environments to execute on which in turn select EC2 instance types
#                   instance types in turn define available cores and memory.  the larger the instance,  the
#                   greater the chance that it will spend some portion of its lifespan with unused resources.
#
# job-definition -- defines which Docker container to run, the command line, and default resource constraints
#
# job -- can override resource constraints
#
# vcpus, memory -- will influence how the AWS Batch scheduler packs jobs onto workers.
#
# long bombing -- the AWS Batch auto-scaler tends to throw long bombs,  if you request a thousand jobs it will
#                 max out worker instances to the level limited by the compute environment.   This means that
#                 a major factor in amortizing the startup+shutdown costs for workers is limiting workers to
#                 the level that they each run a number of jobs with a total runtime scaled to match some
#                 multiple of the startup+shutdown.   E.g. if the total runtime == startup+shutdown,  50% of
#                 the instance's total lifespan is spent starting up and shutting down vs. doing actual work.
#                 An integer multiple isn't required.
#
# NOTE:  for the initial prototype,  the job definition is named calcloud-hst-caldp-job-definition
JobResources = namedtuple("JobResources", [
    "ipppssoot", "instrument", "job_name", "s3_output_uri", "input_path", "crds_config", "vcpus", "memory", "max_seconds"
    ])

# Conceptually the resource requirements defined here could be obtained from a database that records real-world
# memory, cpu, and expected runtime on a per-IPPPSSOOT basis.   The exact values in the tuples are less important
# now than determining which fields should be defined to optimize resource consumption.   The Plan() tuple defines
# the knobs which can be used to do optimization,  some more complex than others:  e.g. a queue and it's associated
# compute environment is complex,  but memory or CPU consumption are simple values.

JOB_INFO = { # cores, memory M, time secs
    "acs" : (4, int(4*1024),  int(60*60*6.5)),
    "cos" : (1, int(1.25*1024), int(60*20)),
    "stis" : (1, int(1.25*1024), int(60*20)),
    "wfc3" : (4, int(4*1024), int(60*60*2)),
    }

def get_job_resources(instr, ipppssoot):
    """Given the instrument `instr` and dataset id `ipppssoot`...

    Return  required resources (cores, memory in M,  seconds til kill)

    Note that these are "required" and still need to be matched to "available".
    """
    info = list(JOB_INFO[instr.lower()])
    try:
        memory_megabytes, cpus, wallclock_seconds = metrics.get_resources(ipppssoot)
        info[0] = cpus
        info[1] = memory_megabytes + 128    # add some overhead for AWS Batch (>= 32M) and measurement error
        info[2] = wallclock_seconds*cpus*2  # kill time,  so too high is better than too low
    except KeyError:
        info = (36, int(70*1024), int(60*60*48))    # 36 cores,  70G/72G,  48 hours max   (c5.9xlarge)
        log.warning("Defaulting (cpu, memory, time) requirements for unknown dataset:", ipppssoot, "to", info)
    return tuple(info)

def get_resources(ipppssoot, output_bucket, batch_name):
    """Given an HST IPPPSSOOT ID,  return information used to schedule it as a batch job.

    Conceptually resource requirements can be tailored to individual IPPPSSOOTs driven
    by a database lookup.

    Returns:  JobResources named tuple
    """
    ipppssoot = ipppssoot.lower()
    s3_output_uri = f"{output_bucket}/{batch_name}"
    instr = hst.get_instrument(ipppssoot)
    job_name = batch_name + "-" + ipppssoot
    input_path = "astroquery:"
    crds_config = "caldp-config-offsite"
    return JobResources(*(ipppssoot, instr, job_name, s3_output_uri, input_path, crds_config) + get_job_resources(instr, ipppssoot))

def get_resources_tuples(ipppssoots, output_bucket="s3://calcloud-hst-pipeline-outputs", batch_name="batch"):
    """
    Given an S3 `output_bucket` name string, a `batch_name` string,
    and a list of IPPPSSOOT dataset IDs `ipppssoots`, get_resources_tuples() return a list of JobResources()
    tuples such that each IPPPSSOOT is handled once.

    The job tuples define key parameters such as:

    - ipppssoot to process
    - Where to put outputs:  's3://calcloud-hst-pipeline-outputs/batch-10-2020-01-31T14-48-20/stis/O8JHG2NNQ'
    - Required cores:  1
    - Required memory: 512
    - CPU seconds til kill: 300

    >> from pprint import pprint
    >> pprint(get_resources_tuples(["O8JHG2NNQ", "O8T9JEHXQ", "O4QPKTDCQ", "O6DCAQK9Q"]))  # doctest: +ELLIPSIS

    """
    batch_name = get_batch_name(batch_name)   # same batch for all ipppssoots
    return [get_resources(ipppssoot, output_bucket, batch_name) for ipppssoot in ipppssoots
            if hst.IPPPSSOOT_RE.match(ipppssoot.upper())]

def planner(ipppssoots_file,  output_bucket="s3://calcloud-hst-pipeline-outputs", batch_name="batch"):
    """Given a set of ipppssoots in `ipppssoots_file` seperated by spaces or newlines,
    as well as an `output_bucket` and `batch_name` to define how the jobs are named and
    where outputs should be stored,  print out the associated batch resources tuples which
    can be submitted.  `batch_name` will be extended by ISO date + time.
    """
    with open(ipppssoots_file) as f:
        ipppssoots = [ipppssoot.lower() for ipppssoot in f.read().split()]
    for p in get_resources_tuples(ipppssoots, output_bucket, batch_name):
        print(tuple(p))  # Drop type to support literal_eval() vs. eval()

# ----------------------------------------------------------------------

def test():
    import doctest
    from calcloud import plan
    return doctest.testmod(plan, optionflags=doctest.ELLIPSIS)

if __name__ == "__main__":
    if len(sys.argv) in [2, 3, 4]:
        if sys.argv[1] == "test":
            print(test())
        else:
            # ipppssoots_file = sys.argv[1]
            # output_bucket = sys.argv[2]  # 's3://calcloud-hst-pipeline-outputs'
            # batch_name = sys.argv[3]  #  'calcloud-hst-test-batch'
            planner(*sys.argv[1:])
    else:
        print("usage: python -m calcloud.plan  <ipppssoots_file>  [<output_bucket>]  [<batch_name>]", file=sys.stderr)
