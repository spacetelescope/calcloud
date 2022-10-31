import re

# -----------------------------------------------------------------------------

IPPPSSOOT_RE = re.compile(r"^[IJLOijlo][a-zA-Z0-9]{8,8}$")
SVM_RE = re.compile(r"[a-zA-Z0-9]{3,4}_[a-zA-Z0-9]{3}_[a-zA-Z0-9]{2}")
MVM_RE = re.compile(r"skycell-p[0-9]{4}x[0-9]{2}y[0-9]{2}")

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

SVM_INSTRUMENTS = ["acs", "wfc3"]


def get_dataset_type(dataset):
    """Given a dataset name, determine if it's an ipppssoot, SVM, or MVM dataset.

    Parameters
    ----------
    dataset : str
        Valid Options:
            ipppssoot (e.g. ieloc4yzq)
            SVM dataset - starts with the instrument name, currently 'acs' or 'wfc3' (e.g. acs_8ph_01)
            MVM dataset - starts with 'skycell' (e.g. skycell-p0797x14y06)

    Returns
    -------
    dataset type : str
        'ipst', 'svm', or 'mvm'
    """
    if IPPPSSOOT_RE.match(dataset):
        dataset_type = "ipst"
    elif SVM_RE.match(dataset) and dataset.split("_")[0] in SVM_INSTRUMENTS:
        dataset_type = "svm"
    elif MVM_RE.match(dataset):
        dataset_type = "mvm"
    else:
        raise ValueError("Invalid dataset name, dataset must be an ipppssoot, SVM, or MVM dataset")
    return dataset_type


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
# 10/12/2022 - Removed get_output_path since it is not used anywhere and appear to be deprecated

# def get_output_path(output_uri, ipppssoot):
#    """Given an `output_uri` string which nominally defines an S3 bucket and
#    directory base path,  and an `ipppssoot` dataset name,  generate a full
#    S3 output path where outputs from processing `ipppssoot` should be stored.
#
#    Parameters
#    ----------
#    output_uri : str
#        A combination of S3 bucket and object directory prefix
#    ipppssoot : str
#        HST-style dataset name for which outputs will be stored.
#
#    Returns
#    -------
#    full_s3_object_path : str
#        A fully specified S3 object, including bucket, directory, and filename.
#
#    >>> get_output_path("s3://temp/batch-2020-02-13T10:33:00", "IC0B02020")
#    's3://temp/batch-2020-02-13T10:33:00/wfc3/IC0B02020'
#    """
#    # This function does not appear to be used anywhere, may have been deprecated
#    return output_uri + "/" + get_instrument(ipppssoot) + "/" + ipppssoot
