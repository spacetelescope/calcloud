from calcloud import hst
from . import conftest

IPPPSSOOT_INSTR = hst.IPPPSSOOT_INSTR


def test_plan_mock(s3_client, lambda_client, iam_client, dynamodb_client):
    from calcloud import plan
    from calcloud import io

    bucket = conftest.BUCKET
    conftest.create_mock_lambda(lambda_client, iam_client)  # create a mock job_predict lambda
    conftest.setup_dynamodb(dynamodb_client)

    ipst = "lpppssoo0"

    # get the default metadata
    metadata = io.get_default_metadata()
    metadata["job_id"] = ipst

    # get plan
    job_plan = plan.get_plan(ipst, bucket, f"{bucket}/inputs", metadata)

    assert job_plan[0] == ipst
    assert job_plan[1] == IPPPSSOOT_INSTR[ipst[0].upper()]
    assert job_plan[6] == 0
