import pytest
from . import conftest
from botocore.exceptions import ClientError


def test_io_mock(s3_client):
    """Doctest for io.py"""
    import doctest
    from calcloud import io

    doctest_result = doctest.testmod(io)
    assert doctest_result[0] == 0, "More than zero doctest errors occurred."  # test errors
    assert doctest_result[1] > 80, "Too few tests ran,  something is wrong with testing."  # tests run


def test_io_mock_s3io(s3_client):
    from calcloud import io

    bucket = conftest.BUCKET
    s3io = io.S3Io(bucket, client=s3_client)

    datasets = conftest.TEST_DATASET_NAMES
    prefixes = datasets
    payloads = ["test_payload" + str(i) for i in range(len(datasets))]
    msg = dict(zip(prefixes, payloads))

    s3io.put(msg)
    result = s3io.get(prefixes)
    for i in range(len(result)):
        assert list(result.keys())[i] == prefixes[i]
        assert list(result.values())[i] == payloads[i]

    bad_msg = 1234
    blank_payload = ""
    with pytest.raises(ValueError):
        s3io.normalize_put_parameters(bad_msg, blank_payload)


def test_io_mock_payloadio(s3_client):
    from calcloud import io

    bucket = conftest.BUCKET
    payloadio = io.JsonIo(
        bucket, client=s3_client
    )  # need to use JsonIo becuase PayloadIo's dumper and loader is set to None

    datasets = conftest.TEST_DATASET_NAMES
    prefixes = datasets
    payloads = ["test_payload" + str(i) for i in range(len(datasets))]
    msg = dict(zip(prefixes, payloads))

    payloadio.put(msg)
    result = payloadio.get(prefixes)
    assert len(result) == len(msg)


def test_io_mock_messageio(s3_client):
    from calcloud import io

    bucket = conftest.BUCKET
    messageio = io.MessageIo(bucket, client=s3_client)

    datasets = conftest.TEST_DATASET_NAMES
    msg_types = io.MESSAGE_TYPES
    prefixes = [f"{msg_types[1]}-{dataset}" for dataset in datasets]  # use 'placed' for all datasets
    payloads = ["test_payload" + str(i) for i in range(len(datasets))]
    msg = dict(zip(prefixes, payloads))

    # test bad prefix exception
    bad_prefix = "put-ipppssoot"
    with pytest.raises(ValueError):
        result = messageio.path(bad_prefix)

    # test MessageIo.reset()
    messageio.put(msg)
    result = messageio.get(prefixes)
    assert len(result) == len(msg)

    reset_dataset = datasets[0]
    reset_prefix = prefixes[0]
    messageio.reset(reset_dataset)

    with pytest.raises(ClientError):
        result = messageio.get(reset_prefix)


def test_io_mock_validate_control():
    from calcloud import io

    # test validate_control() exceptions
    CONTROL_KEYWORDS = io.CONTROL_KEYWORDS
    print(sorted(list(CONTROL_KEYWORDS)))

    validate_control = io.validate_control

    none_metadata = None
    assert validate_control(none_metadata) == {}

    not_dict_metadata = "not_dict"
    with pytest.raises(ValueError):
        validate_control(not_dict_metadata)

    bad_metadata_value = {"cancel_type": 1234}  # cancel_type value must be string
    with pytest.raises(ValueError):
        validate_control(bad_metadata_value)

    bad_metadata_keyword = {"bad_keyword": ""}
    with pytest.raises(ValueError):
        validate_control(bad_metadata_keyword)

    # test good metadata
    cancel_type = "dataset"
    job_id = "ipppssoo1"
    memory_bin = 0
    terminated = True
    timeout_scale = 1.0
    dataset = "ipppssoo1"
    bucket = conftest.BUCKET
    job_name = "ipppssoo1"
    good_meta_data = {
        "cancel_type": cancel_type,
        "job_id": job_id,
        "memory_bin": memory_bin,
        "terminated": terminated,
        "timeout_scale": timeout_scale,
        "dataset": dataset,
        "bucket": bucket,
        "job_name": job_name,
    }
    assert validate_control(good_meta_data) == good_meta_data


def test_io_mock_default_meta():
    from calcloud import io

    default_metadata = io.get_default_metadata()
    assert default_metadata["job_id"] == "undefined"


def test_io_mock_reject_cross_env():
    from calcloud import io

    with pytest.raises(RuntimeError):
        # os.environ["BUCKET"] here should be conftest.BUCKET (calcloud-processing-moto), any other buckets should be rejected
        cross_env_bucket = "cross-env-bucket"
        io._reject_cross_env_bucket(cross_env_bucket)


def test_io_mock_iobundle(s3_client):
    from calcloud import io

    # test IoBundle
    bucket = conftest.BUCKET
    comm = io.get_io_bundle(bucket=bucket, client=s3_client)

    # test inputs
    datasets = conftest.TEST_DATASET_NAMES
    n_datasets = len(datasets)

    msg_types = io.MESSAGE_TYPES
    msg_prefixes = [f"{msg_types[1]}-{dataset}" for dataset in datasets]  # use 'placed' for all datasets
    payloads = ["test_payload" + str(i) for i in range(len(datasets))]
    msg = dict(zip(msg_prefixes, payloads))

    input_files = [f"{dataset}.tar.gz" for dataset in datasets]
    input_msg = dict(zip(datasets, input_files))

    output_files = [f"{dataset}/process_metrix.txt" for dataset in datasets]
    output_msg = dict(zip(datasets, output_files))

    controls = [f"{dataset}/env" for dataset in datasets]

    metadata_objs = list()
    for i in range(len(datasets)):
        tmp_metadata = io.get_default_metadata()
        tmp_metadata["job_id"] = datasets[i]
        metadata_objs.append(tmp_metadata)
    metadata_msg = dict(zip(datasets, metadata_objs))

    # "put" everything
    comm.messages.put(msg)
    comm.inputs.put(input_msg)
    comm.outputs.put(output_msg)
    comm.control.put(controls)
    comm.xdata.put(metadata_msg)

    # test list_s3
    assert (
        len(comm.list_s3()) == n_datasets * 5
    )  # there are n_datasets for each of the five Io objects, so this should return 3 x 5 = 15 items

    # test retrieving ids
    assert len(comm.ids()) == n_datasets  # n_datasets submitted, therefore there should be n_datasets ids

    # reset one dataset
    comm.reset(datasets[0])
    assert (
        len(comm.list_s3()) == n_datasets * 5 - 3
    )  # resetting one dataset takes out three items (one each for outputs, messages, and xdata), leaving n_datasets * 5 - 3

    # clean one dataset
    comm.clean(datasets[0])
    assert (
        len(comm.list_s3()) == (n_datasets - 1) * 5
    )  # this should completely clean out one dataset leaving (n_datasets - 1) * 5

    # reset "all"
    comm.reset()
    assert (
        len(comm.list_s3()) == (n_datasets - 1) * 2
    )  # this reset takes out three items (one each for outputs, messages, and xdata) per dataset, leaving only two items for each remaining dataset

    # clean "all"
    comm.clean()
    assert len(comm.list_s3()) == 0  # there should be nothing left after cleaning everything

    # send a 'placed' message for each dataset
    comm.send(msg_types[1], datasets=datasets)

    # send a 'processing' message for 'all' dataset
    comm.inputs.put(
        input_msg
    )  # have to send all dataset to inputs/ first, because send() uses self.inputs.ids() to determine the existing datasets
    comm.send(msg_types[3])

    # test the send() result
    sent_messages = list()
    sent_msg = [msg_types[1], msg_types[3]]
    sent_datasets = datasets
    for i in range(len(sent_msg)):
        for j in range(len(sent_datasets)):
            sent_messages.append(f"{sent_msg[i]}-{sent_datasets[j]}")

    result = comm.messages.listl()
    for i in range(len(sent_messages)):
        assert sent_messages[i] in result
