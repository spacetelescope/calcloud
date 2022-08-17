from . import conftest
import pytest
from botocore.exceptions import ClientError

_fakeout = conftest


def test_io_mock(s3_client):
    """Doctest for io.py
    Missing lines 138, 187, 257, 402, 574-576, 726-742, 749, 771-781, 791-799, 805-810, 814-819, 826-829, 847, 854-856, 860-861"""
    import doctest
    from calcloud import io

    doctest_result = doctest.testmod(io)
    assert doctest_result[0] == 0, "More than zero doctest errors occurred."  # test errors
    assert doctest_result[1] > 80, "Too few tests ran,  something is wrong with testing."  # tests run


def test_io_mock_s3io(s3_client):
    from calcloud import io

    bucket = conftest.BUCKET
    s3io = io.S3Io(bucket, client=s3_client)

    test_ipsts = ["ipppssoo1", "ipppssoo2", "ipppssoo3"]
    msg_types = io.MESSAGE_TYPES
    prefixes = [f"{msg_types[1]}-{ipst}" for ipst in test_ipsts]  # use 'placed' for all ipsts
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


def test_io_mock_payload3io(s3_client):
    from calcloud import io

    bucket = conftest.BUCKET
    payloadio = io.JsonIo(
        bucket, client=s3_client
    )  # need to use JsonIo becuase PayloadIo's dumper and loader is set to None

    test_ipsts = ["ipppssoo1", "ipppssoo2", "ipppssoo3"]
    msg_types = io.MESSAGE_TYPES
    prefixes = [f"{msg_types[1]}-{ipst}" for ipst in test_ipsts]  # use 'placed' for all ipsts
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

    test_ipsts = ["ipppssoo1", "ipppssoo2", "ipppssoo3"]
    msg_types = io.MESSAGE_TYPES
    prefixes = [f"{msg_types[1]}-{ipst}" for ipst in test_ipsts]  # use 'placed' for all ipsts
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

    reset_ipst = test_ipsts[0]
    reset_prefix = prefixes[0]
    messageio.reset(
        reset_ipst
    )  # input message ids, usually ipppssoots, or other message tails (e.g. in the case of broascast- messages)

    with pytest.raises(ClientError):
        result = messageio.get(reset_prefix)  # need a string, not list, as input to trigger line 575


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

    good_meta_data = {"cancel_type": "ipppssoot"}
    assert validate_control(good_meta_data) == good_meta_data


def test_io_mock_default_meta():
    from calcloud import io

    default_metadata = io.get_default_metadata()
    assert default_metadata["job_id"] == "undefined"
