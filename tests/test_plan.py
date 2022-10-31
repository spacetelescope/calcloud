from calcloud import hst
from decimal import Decimal
from . import conftest
import pytest
import json
import os

IPPPSSOOT_INSTR = hst.IPPPSSOOT_INSTR


def test_plan_mock(s3_client, lambda_client, iam_client, dynamodb_client):
    from calcloud import plan
    from calcloud import io

    bucket = conftest.BUCKET
    conftest.create_mock_lambda(lambda_client, iam_client)  # create a mock job_predict lambda
    conftest.setup_dynamodb(dynamodb_client)

    dataset = "lpppssoo0"

    # get the default metadata
    metadata = io.get_default_metadata()
    metadata["job_id"] = dataset

    # get plan
    job_plan = plan.get_plan(dataset, bucket, f"{bucket}/inputs", metadata)

    assert job_plan[0] == dataset
    assert job_plan[1] == IPPPSSOOT_INSTR[dataset[0].upper()]
    assert job_plan[6] == 0

    # modify metadata so that the memory bin is higher than available, this should throw an AllBinsTriedQuit error
    metadata["memory_bin"] = 5
    with pytest.raises(plan.AllBinsTriedQuit):
        job_plan = plan.get_plan(dataset, bucket, f"{bucket}/inputs", metadata)


def test_plan_query_ddb(s3_client, dynamodb_resource, dynamodb_client):
    from calcloud import plan

    table_name = os.environ.get("DDBTABLE")
    conftest.setup_dynamodb(dynamodb_client)

    dataset = "lpppssoo0"
    table = dynamodb_resource.Table(table_name)

    wallclock_times = [123.2, 130.5, 145.4, 134.8]
    wc_std = 5.0

    # put in a few items for this dataset with different wallclock times

    for i in range(len(wallclock_times)):
        mock_db_row = {"ipst": dataset, "wallclock": wallclock_times[i], "wc_std": wc_std}
        ddb_payload = json.loads(json.dumps(mock_db_row, allow_nan=True), parse_int=Decimal, parse_float=Decimal)
        table.put_item(Item=ddb_payload)

    # if there are more than one entries for one dataset in the table, plan.query_ddb will grab the first query result
    # not sure if/how the query is sorted, so just assert that the "wallclock" values is one of the inputs
    query_result = plan.query_ddb(dataset)
    assert query_result[0] in wallclock_times
    assert query_result[1] == wc_std
