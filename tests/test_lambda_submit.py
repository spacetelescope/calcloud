from . import conftest


def test_lambda_submit_mock(s3_client, lambda_client, iam_client, dynamodb_client, batch_client):
    from calcloud import io
    from calcloud import lambda_submit

    # set up mock environment
    bucket = conftest.BUCKET
    conftest.create_mock_lambda(lambda_client, iam_client)
    conftest.setup_dynamodb(dynamodb_client)
    conftest.setup_batch(iam_client, batch_client, busybox_sleep_timer=5)

    comm = io.get_io_bundle()

    # set up io messages
    ipst = "lpppssoo0"
    placed_msg = f"placed-{ipst}"
    submit_msg = f"submit-{ipst}"
    terminate_msg = f"terminated-{ipst}"
    error_msg = f"error-{ipst}"
    inputs_tar = f"{ipst}.tar.gz"
    controls_mem_model_feature = f"{ipst}/{ipst}_MemModelFeatures.txt"
    overrides = {}

    comm_messages = {
        "ipst": ipst,
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
    ipst = comm_messages["ipst"]

    lambda_submit.main(comm, ipst, bucket, overrides)

    messages = comm.messages.listl()
    assert comm_messages["submit_msg"] in messages

    comm.clean()


def no_placed_msg_submit(comm, bucket, comm_messages):
    from calcloud import lambda_submit

    # a submit that will end in error because the placed-ipppssoot or rescue-ipppssoot message is not present

    overrides = comm_messages["overrides"]
    ipst = comm_messages["ipst"]

    lambda_submit.main(comm, ipst, bucket, overrides)

    messages = comm.messages.listl()
    assert comm_messages["error_msg"] in messages

    result = comm.messages.get(comm_messages["error_msg"])
    fail_message = (
        f"Both the 'placed' and 'rescue' messages for {ipst} have been deleted. Aborting input wait and submission."
    )
    assert result["exception"] == fail_message

    comm.clean()


def no_input_submit(comm, bucket, comm_messages):
    from calcloud import lambda_submit

    # a submit that will end in error because input tar.gz and memory model feature files are not present

    overrides = comm_messages["overrides"]
    ipst = comm_messages["ipst"]

    comm.messages.put(comm_messages["placed_msg"])

    lambda_submit.main(comm, ipst, bucket, overrides)

    messages = comm.messages.listl()
    assert comm_messages["error_msg"] in messages

    result = comm.messages.get(comm_messages["error_msg"])
    fail_message = f"Wait for inputs for {ipst} timeout, aborting submission.  input_tarball=0  memory_modeling=0"
    assert result["exception"] == fail_message

    comm.clean()


def terminated_submit(comm, bucket, comm_messages):
    from calcloud import lambda_submit

    # a submit that will end in error because the placed-ipppssoot or rescue-ipppssoot message is not present
    # it will also has terminated-ipppssoot as error message instead of error-ipppssoot because a terminated-ipppssoot is present in messages

    overrides = comm_messages["overrides"]
    ipst = comm_messages["ipst"]

    comm.messages.put(comm_messages["terminate_msg"])

    lambda_submit.main(comm, ipst, bucket, overrides)

    messages = comm.messages.listl()
    assert comm_messages["terminate_msg"] in messages

    result = comm.messages.get(comm_messages["terminate_msg"])
    fail_message = (
        f"Both the 'placed' and 'rescue' messages for {ipst} have been deleted. Aborting input wait and submission."
    )
    assert result["exception"] == fail_message

    comm.clean()
