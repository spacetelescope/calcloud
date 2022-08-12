import time
import os
import tempfile

from . import conftest
import scrape_batch


def test_blackboard(batch_client, s3_client, iam_client):

    q_arns, jobdef_arns = conftest.setup_batch(iam_client, batch_client)

    for i, (job_q_arn, job_definition_arn) in enumerate(zip(q_arns, jobdef_arns)):
        # Add job
        batch_client.submit_job(jobName=f"ipst_{i}", jobQueue=job_q_arn, jobDefinition=job_definition_arn)

    time.sleep(5)
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
