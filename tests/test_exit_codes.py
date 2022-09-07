def test_exit_codes_mock():
    """Doctest for exit_codes.py"""
    import doctest
    from calcloud import exit_codes

    doctest_result = doctest.testmod(exit_codes)
    assert doctest_result[0] == 0, "More than zero doctest errors occurred."  # test errors
    assert doctest_result[1] >= 11, "Too few tests ran,  something is wrong with testing."  # tests run
