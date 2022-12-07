import time
import os
import tempfile

from . import conftest
import scrape_batch


def test_blackboard(batch_client, s3_client, iam_client):

    q_arns, jobdef_arns = conftest.setup_batch(iam_client, batch_client)

    submitted_datasets = list()

    for i, (job_q_arn, job_definition_arn) in enumerate(zip(q_arns, jobdef_arns)):
        # Add job
        try:
            dataset = conftest.TEST_DATASET_NAMES[i]
        except IndexError:
            dataset = f"ipppssoo{i}"
        batch_client.submit_job(jobName=dataset, jobQueue=job_q_arn, jobDefinition=job_definition_arn)
        submitted_datasets.append(dataset)

    time.sleep(5)
    scrape_batch.lambda_handler({}, {})

    # check the file
    with tempfile.TemporaryFile() as tmp_file:
        snapshot_location = f"{tmp_file}"
        s3_client.download_file(os.environ["BUCKET"], "blackboard/blackboardAWS.snapshot", snapshot_location)

        with open(snapshot_location, "r") as f:
            lines = f.readlines()

    # get a dict of blackboard jobs, with each column as a list
    lines = [line.replace("\n", "").split("|") for line in lines]  # removes new line character
    header_keys = lines[0]  # header line
    blackboard_columns = list()
    for i in range(len(header_keys)):
        blackboard_columns.append([line[i] for line in lines[1:]])
    blackboard_jobs = dict(zip(header_keys, blackboard_columns))

    # assert that all submitted datasets are in the list of jobs scraped from batch
    assert sorted(blackboard_jobs["Dataset"]) == sorted(submitted_datasets)

    # TODO: validate other contents of snapshot
