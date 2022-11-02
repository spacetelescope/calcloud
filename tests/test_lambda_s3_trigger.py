from . import conftest


def test_lambda_s3_trigger(s3_client, lambda_client, iam_client, dynamodb_client, batch_client):
    from calcloud import io
    from calcloud import batch
    from s3_trigger import s3_trigger_handler

    # set up mock environment
    conftest.create_mock_lambda(lambda_client, iam_client)
    conftest.setup_dynamodb(dynamodb_client)
    conftest.setup_batch(iam_client, batch_client, busybox_sleep_timer=30)

    # put a placed-dataset message, and also the expected input tar and memory model feature file
    comm = io.get_io_bundle()
    datasets = conftest.TEST_DATASET_NAMES
    n_datasets = len(datasets)

    placed_msg = [f"placed-{dataset}" for dataset in datasets]
    inputs_tar = [f"{dataset}.tar.gz" for dataset in datasets]
    controls_mem_model_feature = [f"{dataset}/{dataset}_MemModelFeatures.txt" for dataset in datasets]

    for i in range(n_datasets):
        comm.messages.put(placed_msg[i])
        comm.inputs.put(inputs_tar[i])
        comm.control.put(controls_mem_model_feature[i])

        # get a placed event message
        event = conftest.get_message_event(placed_msg[i])
        context = {}

        # handle the s3 event
        s3_trigger_handler.lambda_handler(event, context)

        # get the submitted batch job and assert that the dataset submitted is in the list of returned job names,
        # check after each submit to catch the job before it "finishes"
        job_ids = batch.get_job_ids(client=batch_client)
        job_names = [batch.get_job_name(job_id) for job_id in job_ids]
        assert datasets[i] in job_names
