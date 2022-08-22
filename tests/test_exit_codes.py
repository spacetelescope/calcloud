def test_exit_codes_mock():
    """Doctest for io.py
    Doctest does not cover lines 138, 187, 257, 402, 574-576, 726-742, 749, 771-781, 791-799, 805-810, 814-819, 826-829, 847, 854-856, 860-861"""
    import doctest
    from calcloud import exit_codes

    doctest_result = doctest.testmod(exit_codes)
    assert doctest_result[0] == 0, "More than zero doctest errors occurred."  # test errors
    assert doctest_result[1] >= 11, "Too few tests ran,  something is wrong with testing."  # tests run
