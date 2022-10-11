def test_log_mock():
    """Testing log.py using available doctests
    Still missing lines 95-101, 123, 129, 160-161, 167-171, 190, 215-216, 244, 254,
    259, 281-283, 287, 299, 302, 311, 314, 333, 344-348, 357-360, 367-370, 374"""
    import doctest
    from calcloud import log

    doctest_result = doctest.testmod(log)
    assert doctest_result[0] == 0, "More than zero doctest errors occurred."  # test errors
    assert doctest_result[1] >= 17, "Too few tests ran,  something is wrong with testing."  # tests run
