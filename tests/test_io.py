import pytest
from . import conftest
from botocore.exceptions import ClientError


def test_io_mock(s3_client):
    """Doctest for io.py
    Doctest does not cover lines 138, 187, 257, 402, 574-576, 726-742, 749, 771-781, 791-799, 805-810, 814-819, 826-829, 847, 854-856, 860-861"""
    import doctest
    from calcloud import io

    doctest_result = doctest.testmod(io)
    assert doctest_result[0] == 0, "More than zero doctest errors occurred."  # test errors
    assert doctest_result[1] > 80, "Too few tests ran,  something is wrong with testing."  # tests run


def test_io_mock_s3io(s3_client):
    from calcloud import io

    bucket = conftest.BUCKET
    s3io = io.S3Io(bucket, client=s3_client)

    ipsts = ["ipppssoo1", "ipppssoo2", "ipppssoo3"]
    prefixes = ipsts
    payloads = ["test_payload1", "test_payload2", "test_payload3"]
    msg = dict(zip(prefixes, payloads))

    # test line 138
    s3io.put(msg)
    result = s3io.get(prefixes)
    for i in range(len(result)):
        assert list(result.keys())[i] == prefixes[i]
        assert list(result.values())[i] == payloads[i]

    # test line 187
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

    ipsts = ["ipppssoo1", "ipppssoo2", "ipppssoo3"]
    prefixes = ipsts
    payloads = ["test_payload1", "test_payload2", "test_payload3"]
    msg = dict(zip(prefixes, payloads))

    # test line 257
    payloadio.put(msg)
    result = payloadio.get(prefixes)
    assert len(result) == len(msg)


def test_io_mock_messageio(s3_client):
    from calcloud import io

    bucket = conftest.BUCKET
    messageio = io.MessageIo(bucket, client=s3_client)

    ipsts = ["ipppssoo1", "ipppssoo2", "ipppssoo3"]
    msg_types = io.MESSAGE_TYPES
    prefixes = [f"{msg_types[1]}-{ipst}" for ipst in ipsts]  # use 'placed' for all ipsts
    payloads = ["test_payload1", "test_payload2", "test_payload3"]
    msg = dict(zip(prefixes, payloads))

    # test line 402
    bad_prefix = "put-ipppssoot"
    with pytest.raises(ValueError):
        result = messageio.path(bad_prefix)

    # test lines 574-576
    messageio.put(msg)
    result = messageio.get(prefixes)
    assert len(result) == len(msg)

    reset_ipst = ipsts[0]
    reset_prefix = prefixes[0]
    messageio.reset(
        reset_ipst
    )  # input message ids, usually ipppssoots, or other message tails. Must be a string here, not list, as input to trigger line 575

    with pytest.raises(ClientError):
        result = messageio.get(reset_prefix)


def test_io_mock_validate_control():
    from calcloud import io

    # test lines 736-741
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
    cancel_type = "ipppssoot"
    job_id = "ipppssoo1"
    memory_bin = 0
    terminated = True
    timeout_scale = 1.0
    ipppssoot = "ipppssoo1"
    bucket = conftest.BUCKET
    job_name = "ipppssoo1"
    good_meta_data = {
        "cancel_type": cancel_type,
        "job_id": job_id,
        "memory_bin": memory_bin,
        "terminated": terminated,
        "timeout_scale": timeout_scale,
        "ipppssoot": ipppssoot,
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

    bucket = conftest.BUCKET

    # test lines 755 - 829
    comm = io.get_io_bundle(bucket=bucket, client=s3_client)

    # test inputs, three ipppssoots for each Io object in the bundle
    ipsts = ["ipppssoo1", "ipppssoo2", "ipppssoo3"]

    msg_types = io.MESSAGE_TYPES
    msg_prefixes = [f"{msg_types[1]}-{ipst}" for ipst in ipsts]  # use 'placed' for all ipsts
    payloads = ["test_payload1", "test_payload2", "test_payload3"]
    msg = dict(zip(msg_prefixes, payloads))

    input_files = ["fake_input_file1", "fake_input_file2", "fake_input_file3"]
    input_msg = dict(zip(ipsts, input_files))

    output_files = ["fake_output_file1", "fake_output_file2", "fake_output_file3"]
    output_msg = dict(zip(ipsts, output_files))

    controls = [f"{ipst}/env" for ipst in ipsts]

    metadata_objs = list()
    for i in range(len(ipsts)):
        tmp_metadata = io.get_default_metadata()
        tmp_metadata["job_id"] = ipsts[i]
        metadata_objs.append(tmp_metadata)
    metadata_msg = dict(zip(ipsts, metadata_objs))

    # "put" everything
    comm.messages.put(msg)
    comm.inputs.put(input_msg)
    comm.outputs.put(output_msg)
    comm.control.put(controls)
    comm.xdata.put(metadata_msg)

    # test list_s3
    assert (
        len(comm.list_s3()) == 15
    )  # there are three ipppssoots for each of the five Io objects, so this should return 3 x 5 = 15 items

    # test retrieving ids
    assert len(comm.ids()) == 3  # three ipsts submitted, therefore there should be three ids

    # reset one ipppssoot
    comm.reset(ipsts[0])
    assert (
        len(comm.list_s3()) == 12
    )  # resetting one ipppssoot takes out three items (one each for outputs, messages, and xdata), leaving 12

    # clean one ipppssoot
    comm.clean(ipsts[0])
    assert len(comm.list_s3()) == 10  # this should leave only 2 x 5 items left for the second and third ipppssoot

    # reset "all"
    comm.reset()
    assert (
        len(comm.list_s3()) == 4
    )  # this reset takes out six items (two each for outputs, messages, and xdata), leaving 4

    # clean "all"
    comm.clean()
    assert len(comm.list_s3()) == 0  # there should be nothing left after cleaning everything

    # send a 'placed' message for each ipppssoot
    comm.send(msg_types[1], ipppssoots=ipsts)

    # send a 'processing' message for 'all' ipppssoot
    comm.inputs.put(
        input_msg
    )  # have to send all ipppssoot to inputs/ first, because send() uses self.inputs.ids() to determine the existing ipppssoots
    comm.send(msg_types[3])

    # test the send() result
    sent_messages = list()
    sent_msg = [msg_types[1], msg_types[3]]
    sent_ipsts = ipsts
    for i in range(len(sent_msg)):
        for j in range(len(sent_ipsts)):
            sent_messages.append(f"{sent_msg[i]}-{sent_ipsts[j]}")

    result = comm.messages.listl()
    for i in range(len(sent_messages)):
        assert sent_messages[i] in result
