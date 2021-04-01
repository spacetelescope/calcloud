import os

from calcloud import io
from calcloud import s3
from calcloud import common

import boto3


def lambda_handler(event, context):
    print(event)

    client = boto3.client("batch", config=common.retry_config)
    bucket_name, crds_context = s3.parse_s3_event(event)
    comm = io.get_io_bundle(bucket_name)
    jobdefs = os.environ["JOBDEFINITIONS"].split(",")

    for jd in jobdefs:
        # finding it hard to find the job definitions using the
        # jbDefinitions list; presumably due to revision number
        # this query returns the active version of the correct
        # job definition for the environment
        response = client.describe_job_definitions(jobDefinitionName=jd, status="ACTIVE")

        for jobdef in response["jobDefinitions"]:
            print(jobdef)
            # replace the containerProperties env var for CRDS_CONTEXT
            # with the context in the received message
            env_vars = jobdef["containerProperties"]["environment"]
            for var in env_vars:
                if var["name"] == "CRDS_CONTEXT":
                    var["value"] = f"hst_{crds_context}.pmap"

            # registers a new version of the job definition
            response = client.register_job_definition(
                jobDefinitionName=jd,
                type="container",
                parameters=jobdef["parameters"],
                containerProperties=jobdef["containerProperties"],
            )
            print(response)

            # deregisters the previous version of the job definition
            response = client.deregister_job_definition(jobDefinition=jobdef["jobDefinitionArn"])
            print(response)

            # it's a bit ridiculous that there's not an API for updating
            # a job definition...

    comm.messages.delete_literal(f"crds-{crds_context}")
