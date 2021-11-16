from . import conftest

_fakeout = conftest


def test_io_mock(s3_client):
    import doctest
    from calcloud import io

    doctest_result = doctest.testmod(io)
    assert doctest_result[0] == 0, "More than zero doctest errors occurred."  # test errors
    assert doctest_result[1] > 80, "Too few tests ran,  something is wrong with testing."  # tests run
