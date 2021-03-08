"""These numerical values are returned by CALDP as process exit status.

This file should be shared/coordinated *verbatim* with CALCLOUD to ensure that
CALCLOUD correctly identifies and handles exit status coming from CALDP.

The intent of these codes is to identify specific error cases defined by CALDP.

Any errors not explicitly handled by CALDP are intended to be mapped to
generic values of 0 or 1 to prevent conflicts with these codes.
"""
import sys

_EXIT_CODES = dict(
    SUCCESS=0,
    GENERIC_ERROR=1,
    CMDLINE_ERROR=2,
    INPUT_TAR_FILE_ERROR=21,
    ASTROQUERY_ERROR=22,
    STAGE1_ERROR=23,
    STAGE2_ERROR=24,
    S3_UPLOAD_ERROR=25,
    S3_DOWNLOAD_ERROR=26,
    BESTREFS_ERROR=27,
    CREATE_PREVIEWS_ERROR=28,
    SUBPROCESS_MEMORY_ERROR=31,  # See caldp-process for this
    CALDP_MEMORY_ERROR=32,
    CONTAINER_MEMORY_ERROR=33,
)


_NAME_EXPLANATIONS = dict(
    SUCCESS="Processing completed successfully.",
    GENERIC_ERROR="An error with no specific CALDP handling occurred somewhere.",
    CMDLINE_ERROR="The program command line invocation was incorrect.",
    INPUT_TAR_FILE_ERROR="An error occurred locating or untarring the inputs tarball.",
    ASTROQUERY_ERROR="An error occurred downloading astroqery: inputs",
    STAGE1_ERROR="An error occurred in this instrument's stage1 processing step. e.g. calxxx",
    STAGE2_ERROR="An error occurred in this instrument's stage2 processing step, e.g astrodrizzle",
    S3_UPLOAD_ERROR="An error occurred uploading the outputs tarball to S3.",
    S3_DOWNLOAD_ERROR="An error occurred downloading inputs from S3.",
    BESTREFS_ERROR="An error occurred computing or downloading CRDS reference files.",
    CREATE_PREVIEWS_ERROR="An error occurrred creating preview files for processed data.",
    # Potentially see caldp-process bash script for this
    SUBPROCESS_MEMORY_ERROR="A Python MemoryError was detected by scanning the process.txt log.",
    CALDP_MEMORY_ERROR="CALDP generated a Python MemoryError during processing or preview creation.",
    # This is never directly returned.  It's intended to be used to trigger a container memory limit
    CONTAINER_MEMORY_ERROR="The Batch/ECS container runtime killed the job due to memory limits.",
)

_CODE_TO_NAME = dict()

# Set up original module global variables / named constants
for (name, code) in _EXIT_CODES.items():
    globals()[name] = code
    _CODE_TO_NAME[code] = name
    _CODE_TO_NAME[str(code)] = name
    assert name in _NAME_EXPLANATIONS


def explain(exit_code):
    """Return the text explanation for the specified `exit_code`.

    >>> explain(SUCCESS)
    'EXIT SUCCESS[0]: Processing completed successfully.'

    >>> explain("SUCCESS")
    'EXIT SUCCESS[0]: Processing completed successfully.'

    >>> explain(GENERIC_ERROR)
    'EXIT GENERIC_ERROR[1]: An error with no specific CALDP handling occurred somewhere.'

    >>> explain(SUBPROCESS_MEMORY_ERROR)
    'EXIT SUBPROCESS_MEMORY_ERROR[31]: A Python MemoryError was detected by scanning the process.txt log.'
    """
    if exit_code in _CODE_TO_NAME:
        name = _CODE_TO_NAME[exit_code]
        explanation = _NAME_EXPLANATIONS[name]
    elif exit_code in _NAME_EXPLANATIONS:
        name = exit_code
        exit_code = globals()[name]
        explanation = _NAME_EXPLANATIONS[name]
    else:
        raise ValueError("Invalid exit_code: " + repr(exit_code))
    return f"EXIT {name}[{exit_code}]: {explanation}"


def print_explanations(error_codes):
    """Print out the text explanation of each error code in `error_codes`.

    >>> print_explanations([32])
    EXIT CALDP_MEMORY_ERROR[32]: CALDP generated a Python MemoryError during processing or preview creation.
    """
    for code in error_codes:
        print(explain(code))


def is_memory_error(exit_code):
    """Return  True IFF `exit_code` indicates some kind of memory error.

    exit_code may be specified as a name string or integer exit code.

    >>> is_memory_error(GENERIC_ERROR)
    False

    >>> is_memory_error(SUBPROCESS_MEMORY_ERROR)
    True

    >>> is_memory_error(CALDP_MEMORY_ERROR)
    True

    >>> is_memory_error(CONTAINER_MEMORY_ERROR)
    True

    >>> is_memory_error("GENERIC_ERROR")
    False

    >>> is_memory_error("SUBPROCESS_MEMORY_ERROR")
    True
    """
    memory_error_names = ["SUBPROCESS_MEMORY_ERROR", "CALDP_MEMORY_ERROR", "CONTAINER_MEMORY_ERROR"]
    return (exit_code in [globals()[name] for name in memory_error_names]) or (exit_code in memory_error_names)


def test():
    import doctest

    try:
        from caldp import exit_codes
    except ImportError:
        from calcloud import exit_codes
    return doctest.testmod(exit_codes)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "test":
        print(test())
    elif len(sys.argv) >= 2 and sys.argv[1] == "explain":
        print_explanations(sys.argv[2:])
    else:
        print("usage: python -m caldp.exit_codes [test|explain] [explain_codes...]")
        sys.exit(globals()["CMDLINE_ERROR"])  # the things we do for flake8...
