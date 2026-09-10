"""Shared feature extraction for job metadata used by multiple lambdas."""

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

    dataset_type = input_data.get("dataset_type")
    if dataset_type == "svm":
        if dataset.startswith("acs"):
            instr = 0  # ACS
        elif dataset.startswith("wfc3"):
            instr = 3  # WFC3
    else:
        if dataset[-1] == "0":
            dtype = 0
        else:
            dtype = 1

        if dataset[0] == "j":
            instr = 0  # ACS
        elif dataset[0] == "l":
            instr = 1  # COS
        elif dataset[0] == "o":
            instr = 2  # STIS
        elif dataset[0] == "i":
            instr = 3  # WFC3

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
    if dataset_type == "svm":
        features = {"n_files": n_files,
                    "total_mb": total_mb,
                    "instr": instr,
                    "detector": detector}
    elif dataset_type == "mvm":
        features = {"n_files": n_files,
                    "total_mb": total_mb}

    if dataset_type:
        features["dataset_type"] = dataset_type
    return features