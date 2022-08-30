from . import conftest


def test_lambda_s3_trigger(s3_client, lambda_client, iam_client, dynamodb_client, batch_client):
    from calcloud import io
    from calcloud import batch
    from s3_trigger import s3_trigger_handler

    # set up mock environment
    bucket = conftest.BUCKET
    conftest.create_mock_lambda(lambda_client, iam_client)
    conftest.setup_dynamodb(dynamodb_client)
    conftest.setup_batch(iam_client, batch_client, busybox_sleep_timer=5)

    # put a placed-ipppssoot message, and also the expected input tar and memory model feature file
    comm = io.get_io_bundle()
    ipst = "ipppsso42"

    placed_msg = f"placed-{ipst}"
    inputs_tar = f"{ipst}.tar.gz"
    controls_mem_model_feature = f"{ipst}/{ipst}_MemModelFeatures.txt"

    comm.messages.put(placed_msg)
    comm.inputs.put(inputs_tar)
    comm.control.put(controls_mem_model_feature)

    # get a placed event message
    event = conftest.get_message_event(placed_msg)
    context = {}

    # handle the s3 event
    s3_trigger_handler.lambda_handler(event, context)

    # get the submitted batch job
    job_ids = batch.get_job_ids(client=batch_client)
    assert len(job_ids) == 1
