"""This module is used to define job plans using the high level function
get_plan().

get_plan() returns a named tuple specifying all the information needed to
submit a job.

Based on a memory_retries counter,  get_plan() iterates through a sequence
of job definitions with increasing memory requirements until the job later
succeeds with sufficient memory or exhausts all retries.
"""
import sys
import os
from collections import namedtuple

from . import hst
from . import log
from . import common

import json
import boto3
from boto3.dynamodb.conditions import Key

client = boto3.client("lambda", config=common.retry_config)
dynamodb = boto3.resource("dynamodb", config=common.retry_config, region_name="us-east-1")

# ----------------------------------------------------------------------

JobResources = namedtuple(
    "JobResources",
    [
        "ipppssoot",
        "instrument",
        "job_name",
        "s3_output_uri",
        "input_path",
        "crds_config",
        "initial_modeled_bin",
        "max_seconds",
    ],
)

JobEnv = namedtuple("JobEnv", ("job_queue", "job_definition", "command"))

Plan = namedtuple("Plan", JobResources._fields + JobEnv._fields)


class AllBinsTriedQuit(Exception):
    """Exception to raise when retry is requested but no applicable bin is available."""


# ----------------------------------------------------------------------

# This is the top level entrypoint called from calcloud.lambda_submit.main
# It returns a Plan() tuple which is passed to the submit function.


def get_plan(ipppssoot, output_bucket, input_path, metadata):
    """Given the resource requirements for a job,  map them onto appropriate
    requirements and Batch infrastructure needed to process the job.

    ipppssoot          dataset ID to plan
    output_bucket      S3 output bucket,  top level
    input_path
    metadata           dictionary of parameters sent in message override payloads or
                       recorded in the control file.  Relevant here:
       memory_retries     increasing counter of retries with 0 being first try,
                          intended to drive increasing memory for each subsequent retry
                          with the maximum retry value set in Terraform.
       memory_bin      absolute memory bin number or None
       timeout_scale      factor to multiply kill time by

    Returns    Plan   (named tuple)
    """
    timeout_scale = metadata["timeout_scale"]
    memory_retries = metadata["memory_retries"]
    memory_bin = metadata["memory_bin"]
    job_resources = _get_resources(ipppssoot, output_bucket, input_path, timeout_scale)
    env = _get_environment(job_resources, memory_retries, memory_bin)
    return Plan(*(job_resources + env))


def query_ddb(ipppssoot):
    table_name = os.environ["DDBTABLE"]
    table = dynamodb.Table(table_name)
    response = table.query(KeyConditionExpression=Key("ipst").eq(ipppssoot))
    db_clock, std_err = 20 * 60, 5
    if len(response["Items"]) > 0:
        data = response["Items"][0]
        db_clock = int(data["wallclock"])
        if "std_err" in data:
            std_err = float(data["std_err"])
    return db_clock, std_err


def invoke_lambda_predict(ipppssoot, output_bucket):
    """Invoke calcloud-ai lambda to compute baseline memory bin and kill time."""
    bucket = output_bucket.replace("s3://", "")
    key = f"control/{ipppssoot}/{ipppssoot}_MemModelFeatures.txt"
    inputParams = {"Bucket": bucket, "Key": key, "Ipppssoot": ipppssoot}
    job_predict_lambda = os.environ["JOBPREDICTLAMBDA"]
    response = client.invoke(
        FunctionName=job_predict_lambda,
        InvocationType="RequestResponse",
        Payload=json.dumps(inputParams),
    )
    predictions = json.load(response["Payload"])
    print(f"Predictions for {ipppssoot}: \n {predictions}")
    # defaults: db_clock=20 minutes, std_err=5
    db_clock, std_err = query_ddb(ipppssoot)
    clockTime = predictions["clockTime"] * (1 + std_err)
    return clockTime, db_clock, predictions["memBin"]


def _get_resources(ipppssoot, output_bucket, input_path, timeout_scale):
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
    crds_config = "caldp-config-aws"
    # default: predicted time * 6 or * 1+std_err
    clockTime, db_clock, initial_bin = invoke_lambda_predict(ipppssoot, output_bucket)
    # clip between 20 minutes and 2 days, * timeout_scale
    kill_time = int(min(max(clockTime, db_clock), 48 * 60 * 60) * timeout_scale)
    # minimum Batch requirement 60 seconds
    kill_time = int(max(kill_time, 60))

    return JobResources(ipppssoot, instr, job_name, s3_output_uri, input_path, crds_config, initial_bin, kill_time)


def _get_environment(job_resources, memory_retries, memory_bin):
    """Based on a resources tuple and a memory_retries counter or memory_bin,  determine:

    (queue,  job_definition_for_memory,  caldp_entrypoint)
    """
    job_defs = os.environ["JOBDEFINITIONS"].split(",")
    job_queues = os.environ["JOBQUEUES"].split(",")
    job_resources = JobResources(*job_resources)

    final_bin = memory_bin if memory_bin is not None else job_resources.initial_modeled_bin + memory_retries
    if final_bin < len(job_defs):
        log.info(
            "Selecting resources for",
            job_resources.ipppssoot,
            "Initial modeled bin",
            job_resources.initial_modeled_bin,
            "Memory retries",
            memory_retries,
            "Memory bin",
            memory_bin,
            "Final bin index",
            final_bin,
        )
        job_definition = job_defs[final_bin]
        job_queue = job_queues[final_bin]
    else:
        msg = (
            "No higher memory job definition for",
            job_resources.ipppssoot,
            "after",
            memory_retries,
            "and",
            memory_bin,
        )
        log.info(*msg)
        raise AllBinsTriedQuit(*msg)

    return JobEnv(job_queue, job_definition, "caldp-process")


# ----------------------------------------------------------------------


def test():
    import doctest
    from calcloud import plan

    return doctest.testmod(plan, optionflags=doctest.ELLIPSIS)


# ----------------------------------------------------------------------


if __name__ == "__main__":
    if sys.argv[1] == "test":
        print(test())
