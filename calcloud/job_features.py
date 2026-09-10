"""Shared feature extraction for job metadata used by multiple lambdas."""

from . import hst


def get_s3_body(bucket, key):
    """Retrieve the body of an S3 object as a list of lines."""
    obj = bucket.Object(key)
    try:
        body = obj.get()["Body"].read().decode("utf-8").splitlines()
    except Exception as exc:
        body = None
        print(exc)
    return body


def get_features_for_ipst(dataset, input_data):
    """Extract features for ipppssoot."""
    n_files = 0
    total_mb = 0
    detector = 0
    subarray = 0
    drizcorr = 0
    pctecorr = 0
    crsplit = 0

    for k, v in input_data.items():
        if k == "n_files":
            n_files = int(v)
        if k == "total_mb":
            total_mb = round(float(v), 0)
        if k == "DETECTOR":
            if v in ["UVIS", "WFC"]:
                detector = 1
            else:
                detector = 0
        if k == "SUBARRAY":
            if v == "True":
                subarray = 1
            else:
                subarray = 0
        if k == "DRIZCORR":
            if v == "PERFORM":
                drizcorr = 1
            else:
                drizcorr = 0
        if k == "PCTECORR":
            if v == "PERFORM":
                pctecorr = 1
            else:
                pctecorr = 0
        if k == "CRSPLIT":
            if v == "NaN":
                crsplit = 0
            elif v in ["1", "1.0"]:
                crsplit = 1
            else:
                crsplit = 2

    i = dataset
    # dtype (asn or singleton)
    if i[-1] == "0":
        dtype = 1
    else:
        dtype = 0
    # instr encoding cols
    if i[0] == "j":
        instr = 0
    elif i[0] == "l":
        instr = 1
    elif i[0] == "o":
        instr = 2
    elif i[0] == "i":
        instr = 3

    features = {
        "n_files": n_files,
        "total_mb": total_mb,
        "drizcorr": drizcorr,
        "pctecorr": pctecorr,
        "crsplit": crsplit,
        "subarray": subarray,
        "detector": detector,
        "dtype": dtype,
        "instr": instr,
        "dataset_type": "ipst",
    }
    return features


def get_features_for_svm(dataset, input_data):
    """Extract features for svm."""
    n_files = int(input_data.get("n_files", 0))
    total_mb = round(float(input_data.get("total_mb", 0)), 0)
    detector = 1 if input_data.get("DETECTOR") in ["UVIS", "WFC"] else 0
    if dataset.startswith("acs"):
        instr = 0  # ACS
    elif dataset.startswith("wfc3"):
        instr = 3  # WFC3

    return {"n_files": n_files, "total_mb": total_mb, "detector": detector, "instr": instr, "dataset_type": "svm"}


def get_features_for_mvm(input_data):
    """Extract features for mvm."""
    n_files = int(input_data.get("n_files", 0))
    total_mb = round(float(input_data.get("total_mb", 0)), 0)
    return {"n_files": n_files, "total_mb": total_mb, "dataset_type": "mvm"}


def extract_input_features(dataset, input_data):
    """Convert memory model text inputs into normalized numeric features."""
    dataset_type = hst.get_dataset_type(dataset)

    if dataset_type == "ipst":
        return get_features_for_ipst(dataset, input_data)
    elif dataset_type == "svm":
        return get_features_for_svm(dataset, input_data)
    elif dataset_type == "mvm":
        return get_features_for_mvm(input_data)
    else:
        raise ValueError(f"Unsupported dataset_type: {dataset_type}")
