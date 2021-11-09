import time
import os
import tempfile

from . import conftest
import scrape_batch


def test_blackboard(batch_client, s3_client, iam_client):
    # mock s3 bucket
    bucket = s3_client.create_bucket(Bucket=os.environ["BUCKET"])
    print(bucket)

    # we'll need a mock iam role to pass to the mock batch client
    iams = iam_client.create_role(
        RoleName="test_batch_client",
        AssumeRolePolicyDocument="string",
    )
    iam_arn = iams.get("Role").get("Arn")
    print("iamRoleArn: " + iam_arn)

    # mocks for each job ladder step
    for i, ce in enumerate(conftest.CENVIRONMENTS):
        created_cenv = batch_client.create_compute_environment(
            computeEnvironmentName=ce, type="UNMANAGED", serviceRole=iam_arn
        )

        compute_environment_arn = created_cenv.get("computeEnvironmentArn")
        print("computeEnvironmentArn: " + compute_environment_arn)

        created_queue = batch_client.create_job_queue(
            jobQueueName=conftest.JOBQUEUES[i],
            state="ENABLED",
            priority=1,
            computeEnvironmentOrder=[
                {"order": 1, "computeEnvironment": compute_environment_arn},
            ],
        )
        job_q_arn = created_queue.get("jobQueueArn")
        print("jobQueueArn: " + job_q_arn)

        created_jobdef = batch_client.register_job_definition(
            jobDefinitionName=conftest.JOBDEFINITIONS[i],
            type="container",
            containerProperties={
                "image": "busybox",
                "vcpus": 1,
                "memory": 128,
                "command": ["sleep", "1"],
            },
        )
        job_definition_arn = created_jobdef.get("jobDefinitionArn")
        print("jobDefinitionArn: " + job_definition_arn)

        # Add job
        batch_client.submit_job(jobName=f"ipst_{i}", jobQueue=job_q_arn, jobDefinition=job_definition_arn)

    time.sleep(15)
    scrape_batch.lambda_handler({}, {})

    # check the file
    with tempfile.TemporaryFile() as tmp_file:
        snapshot_location = f"{tmp_file}"
        s3_client.download_file(os.environ["BUCKET"], "blackboard/blackboardAWS.snapshot", snapshot_location)

        with open(snapshot_location, "r") as f:
            lines = f.readlines()

    # header + 4 jobs submitted in this test
    assert len(lines) == 5

    # TODO: validate contents of snapshot
