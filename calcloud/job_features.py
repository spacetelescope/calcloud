"""Shared feature extraction for job metadata used by multiple lambdas."""


INSTR_ACS = 0
INSTR_COS = 1
INSTR_STIS = 2
INSTR_WFC3 = 3

DTYPE_SINGLETON = 0
DTYPE_ASN = 1
DTYPE_NO_VALUE = 2


def get_s3_body(bucket, key):
    """Retrieve the body of an S3 object as a list of lines."""
    obj = bucket.Object(key)
    try:
        body = obj.get()["Body"].read().decode("utf-8").splitlines()
    except Exception as exc:
        body = None
        print(exc)
    return body


def extract_input_features(dataset, input_data):
    """Convert memory model text inputs into normalized numeric features."""
    n_files = 0
    total_mb = 0
    detector = 0
    subarray = 0
    drizcorr = 0
    pctecorr = 0
    crsplit = 0

    for key, value in input_data.items():
        if key == "n_files":
            n_files = int(value)
        if key == "total_mb":
            total_mb = round(float(value), 0)
        if key == "DETECTOR":
            if value in ["UVIS", "WFC"]:
                detector = 1
            else:
                detector = 0
        if key == "SUBARRAY":
            if value == "True":
                subarray = 1
            else:
                subarray = 0
        if key == "DRIZCORR":
            if value == "PERFORM":
                drizcorr = 1
            else:
                drizcorr = 0
        if key == "PCTECORR":
            if value == "PERFORM":
                pctecorr = 1
            else:
                pctecorr = 0
        if key == "CRSPLIT":
            if value == "NaN":
                crsplit = 0
            elif value in ["1", "1.0"]:
                crsplit = 1
            else:
                crsplit = 2

    product_type = input_data.get("product_type")
    if product_type in ("svm", "mvm"):
        dtype = DTYPE_NO_VALUE
        detector_name = input_data["DETECTOR"]
        if detector_name in ("UVIS", "IR"):
            instr = INSTR_WFC3
        elif detector_name in ("WFC", "SBC", "HRC"):
            instr = INSTR_ACS
    else:
        if dataset[-1] == "0":
            dtype = DTYPE_ASN
        else:
            dtype = DTYPE_SINGLETON

        if dataset[0] == "j":
            instr = INSTR_ACS
        elif dataset[0] == "l":
            instr = INSTR_COS
        elif dataset[0] == "o":
            instr = INSTR_STIS
        elif dataset[0] == "i":
            instr = INSTR_WFC3

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
    }
    if product_type:
        features["product_type"] = product_type
    return features