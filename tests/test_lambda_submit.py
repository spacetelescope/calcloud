from . import conftest


def test_lambda_submit_mock(s3_client, lambda_client, iam_client, dynamodb_client, batch_client):
    from calcloud import io

    # set up mock environment
    bucket = conftest.BUCKET
    conftest.create_mock_lambda(lambda_client, iam_client)
    conftest.setup_dynamodb(dynamodb_client)
    conftest.setup_batch(iam_client, batch_client, busybox_sleep_timer=5)
    datasets = conftest.TEST_DATASET_NAMES

    comm = io.get_io_bundle()

    for dataset in datasets:
        print("Testing dataset: ", dataset)

        # set up io messages
        # dataset = "acs_aaa_00"
        placed_msg = f"placed-{dataset}"
        submit_msg = f"submit-{dataset}"
        terminate_msg = f"terminated-{dataset}"
        error_msg = f"error-{dataset}"
        inputs_tar = f"{dataset}.tar.gz"
        controls_mem_model_feature = f"{dataset}/{dataset}_MemModelFeatures.txt"
        overrides = {}

        comm_messages = {
            "dataset": dataset,
            "placed_msg": placed_msg,
            "submit_msg": submit_msg,
            "terminate_msg": terminate_msg,
            "error_msg": error_msg,
            "inputs_tar": inputs_tar,
            "controls_mem_model_feature": controls_mem_model_feature,
            "overrides": overrides,
        }

        # test different submits
        good_submit(comm, bucket, comm_messages)

        no_placed_msg_submit(comm, bucket, comm_messages)

        no_input_submit(comm, bucket, comm_messages)

        terminated_submit(comm, bucket, comm_messages)


def good_submit(comm, bucket, comm_messages):
    from calcloud import lambda_submit

    # a proper submit with all the required inputs in place, should result in a submit-ippssoot message
    comm.messages.put(comm_messages["placed_msg"])
    comm.inputs.put(comm_messages["inputs_tar"])
    comm.control.put(comm_messages["controls_mem_model_feature"])
    overrides = comm_messages["overrides"]
    dataset = comm_messages["dataset"]

    lambda_submit.main(comm, dataset, bucket, overrides)

    messages = comm.messages.listl()
    assert comm_messages["submit_msg"] in messages

    comm.clean()


def no_placed_msg_submit(comm, bucket, comm_messages):
    from calcloud import lambda_submit

    # a submit that will end in error because the placed-dataset or rescue-dataset message is not present

    overrides = comm_messages["overrides"]
    dataset = comm_messages["dataset"]

    lambda_submit.main(comm, dataset, bucket, overrides)

    messages = comm.messages.listl()
    assert comm_messages["error_msg"] in messages

    result = comm.messages.get(comm_messages["error_msg"])
    fail_message = (
        f"Both the 'placed' and 'rescue' messages for {dataset} have been deleted. Aborting input wait and submission."
    )
    assert result["exception"] == fail_message

    comm.clean()


def no_input_submit(comm, bucket, comm_messages):
    from calcloud import lambda_submit

    # a submit that will end in error because input tar.gz and memory model feature files are not present

    overrides = comm_messages["overrides"]
    dataset = comm_messages["dataset"]

    comm.messages.put(comm_messages["placed_msg"])

    lambda_submit.main(comm, dataset, bucket, overrides)

    messages = comm.messages.listl()
    assert comm_messages["error_msg"] in messages

    result = comm.messages.get(comm_messages["error_msg"])
    fail_message = f"Wait for inputs for {dataset} timeout, aborting submission.  input_tarball=0  memory_modeling=0"
    assert result["exception"] == fail_message

    comm.clean()


def terminated_submit(comm, bucket, comm_messages):
    from calcloud import lambda_submit

    # a submit that will end in error because the placed-dataset or rescue-dataset message is not present
    # it will also has terminated-dataset as error message instead of error-dataset because a terminated-dataset is present in messages

    overrides = comm_messages["overrides"]
    dataset = comm_messages["dataset"]

    comm.messages.put(comm_messages["terminate_msg"])

    lambda_submit.main(comm, dataset, bucket, overrides)

    messages = comm.messages.listl()
    assert comm_messages["terminate_msg"] in messages

    result = comm.messages.get(comm_messages["terminate_msg"])
    fail_message = (
        f"Both the 'placed' and 'rescue' messages for {dataset} have been deleted. Aborting input wait and submission."
    )
    assert result["exception"] == fail_message

    comm.clean()
