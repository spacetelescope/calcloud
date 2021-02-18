"""Given memory, cpu, and time JobResources provided by the planner, this
module identifies which batch queues, and job definitions the jobs should be
assigned to.  Alternately, this module assigns the jobs to the appropriate
HTCondor queues.

In an advanced implementation, given the resource requirements for a batch of
jobs, provision first creates the environment in which they'll be processed.
"""
import sys
import ast
import os
from collections import namedtuple

from . import plan
from .plan import JobResources

# -------------------------------------------------------------------------------

# XXXX during refactor,  hopefully keep interfaces:
#
#    Plan                     --  named tuple used to describe the result of get_plan()
#
#    get_plan(job_resources)  -- convert requirements defined by job_resources to a Plan
#
# but re-define what get_plan() actually does in terms of modelling
# and predefined Batch resources.
#

OUTLIER_THRESHHOLD_MEGABYTES = 8192 - 128  # m5.large - 128M ~overhead

JobEnv = namedtuple("JobEnv", ("job_queue", "job_definition", "command"))

Plan = namedtuple("Plan", JobResources._fields + JobEnv._fields)


def get_plan(job_resources):
    """Given the resource requirements for a job,  map them onto appropriate
    Batch resources needed to process the job.

    Returns a Plan named tuple
    """
    env = _get_environment(job_resources)
    return Plan(*(job_resources + env))


# -------------------------------------------------------------------------------


def _get_environment(job_resources):
    job_resources = JobResources(*job_resources)
    job_definition = os.environ["JOBDEFINITION"]
    normal_queue = os.environ["NORMALQUEUE"]
    outlier_queue = os.environ["OUTLIERQUEUE"]

    if job_resources.memory <= OUTLIER_THRESHHOLD_MEGABYTES:
        return JobEnv(normal_queue, job_definition, "caldp-process")
    else:
        return JobEnv(outlier_queue, job_definition, "caldp-process")


# -------------------------------------------------------------------------------


def _main(resource_file):
    """Run this on the output of plan.py to generate complete Plan tuples
    which can be inspected or piped into submit.py.
    """
    handle = sys.stdin if resource_file == "-" else open(resource_file, "r")

    for line in handle.read().splitlines():
        resource_tup = ast.literal_eval(line)
        plan = get_plan(resource_tup)
        print(tuple(plan))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: provision <resource_reqs_file> | -")
        sys.exit(1)
    _main(sys.argv[1])
