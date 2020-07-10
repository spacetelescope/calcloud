import re

# -----------------------------------------------------------------------------

IPPPSSOOT_RE = re.compile(r"^[IJLOijlo][A-Z0-9]{8,8}$")

# Note: only ACS, COS, STIS, and WFC3 are initially supported
IPPPSSOOT_INSTR = {
    "J": "acs",
    "U": "wfpc2",
    "V": "hsp",
    "W": "wfpc",
    "X": "foc",
    "Y": "fos",
    "Z": "hrs",
    "E": "eng",
    "F": "fgs",
    "I": "wfc3",
    "N": "nicmos",
    "O": "stis",
    "L": "cos",
}

INSTRUMENTS = set(IPPPSSOOT_INSTR.values())


def get_instrument(ipppssoot):
    """Given an `ipppssoot` ID, return the corresponding instrument name.

    Parameters
    ----------
    ipppssoot : str
        HST-style dataset name,  'i' character identifies instrument:
            J  --  acs
            U  --  wfpc2
            I  --  wfc3
            O  --  stis
            L  --  cos

    Returns
    -------
    instrument : str
        Name of the instrument in lowercase corresponding to `ipppssoot`, e.g. 'acs'
    """
    if ipppssoot.lower() in INSTRUMENTS:
        return ipppssoot.lower()
    else:
        return IPPPSSOOT_INSTR.get(ipppssoot.upper()[0])

# -----------------------------------------------------------------------------


def get_output_path(output_uri,  ipppssoot):
    """Given an `output_uri` string which nominally defines an S3 bucket and
    directory base path,  and an `ipppssoot` dataset name,  generate a full
    S3 output path where outputs from processing `ipppssoot` should be stored.

    Parameters
    ----------
    output_uri : str
        A combination of S3 bucket and object directory prefix
    ipppssoot : str
        HST-style dataset name for which outputs will be stored.

    Returns
    -------
    full_s3_object_path : str
        A fully specified S3 object, including bucket, directory, and filename.

    >>> get_output_path("s3://temp/batch-2020-02-13T10:33:00", "IC0B02020")
    's3://temp/batch-2020-02-13T10:33:00/wfc3/IC0B02020'
    """
    return output_uri + "/" + get_instrument(ipppssoot) + "/" + ipppssoot
