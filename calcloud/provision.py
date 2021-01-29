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

OUTLIER_THRESHHOLD_MEGABYTES = 8192-128  # m5.large - 128M ~overhead

JobEnv = namedtuple(
    "JobEnv", ("job_queue", "job_definition", "command"))

Plan = namedtuple("Plan", JobResources._fields + JobEnv._fields)

def main(resource_file):
    handle = sys.stdin if resource_file == "-" else open(resource_file,"r")
    resources = []
    for line in handle.read().splitlines():
        resource_tup = ast.literal_eval(line)
        resources.append(resource_tup)
    for p in get_plan_tuples(resources):
        print(tuple(p))

def get_plan_tuples(job_resources_list):
    return [ get_plan(plan.JobResources(*resource_reqs))
             for resource_reqs in job_resources_list ]

def get_plan(job_resources):
    env = get_environment(job_resources)
    return Plan(*(job_resources + env))

def get_environment(job_resources):
    job_resources = JobResources(*job_resources)
    job_definition = os.environ['JOBDEFINITION']
    normal_queue = os.environ['NORMALQUEUE']
    outlier_queue = os.environ['OUTLIERQUEUE']

    if job_resources.memory <= OUTLIER_THRESHHOLD_MEGABYTES:
        return JobEnv(normal_queue, job_definition, "caldp-process")
    else:
        return JobEnv(outlier_queue, job_definition, "caldp-process")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: provision <resource_reqs_file> | -")
        sys.exit(1)
    main(sys.argv[1])
