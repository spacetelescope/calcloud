import os
from . import conftest
from . import test_model_ingest

mem_model_text = test_model_ingest.mem_model_text
mem_model_default_param = test_model_ingest.mem_model_default_param
get_mem_model_file_text = test_model_ingest.get_mem_model_file_text

metrics_text = test_model_ingest.metrics_text
metrics_default_param = test_model_ingest.metrics_default_param
get_metrics_file_text = test_model_ingest.get_metrics_file_text

put_mem_model_file = test_model_ingest.put_mem_model_file
put_process_metrics_file = test_model_ingest.put_process_metrics_file
put_preview_metrics_file = test_model_ingest.put_preview_metrics_file


def test_model_lambda_scrape(s3_client, dynamodb_client, dynamodb_resource):
    """Test the lambda handler for ModelIngest"""

    from calcloud import io
    from ModelIngest import lambda_scrape

    bucket = conftest.BUCKET
    table_name = os.environ.get("DDBTABLE")
    conftest.setup_dynamodb(dynamodb_client)

    comm = io.get_io_bundle(bucket=bucket, client=s3_client)

    ipst = "ipppssoo7"
    processed_msg = f"processed-{ipst}"

    # create and put the memory model file
    mem_model_params = mem_model_default_param.copy()
    put_mem_model_file(ipst, comm, fileparams=mem_model_params)

    # create and put the process metrics file
    process_metrics_params = metrics_default_param.copy()
    put_process_metrics_file(ipst, comm, fileparams=process_metrics_params)

    # create and put the preview metrics file
    preview_metrics_params = metrics_default_param.copy()
    put_preview_metrics_file(ipst, comm, fileparams=preview_metrics_params)

    # create the processed-ipppssoot event
    event = conftest.get_message_event(processed_msg)

    # call lambda_scrape handler to scrape the info it needs from these files and put them in dynamodb
    lambda_scrape.lambda_handler(event)

    # get the entry from dynamodb and check that it has the right ipppssoot
    table = dynamodb_resource.Table(table_name)
    response = table.get_item(Key={"ipst": ipst})["Item"]
    assert response["ipst"] == ipst
