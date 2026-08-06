"""This module loads a pre-trained ANN to predict job resource requirements for HST.
# 1 - load job metadata inputs from text file in s3
# 2 - encode strings as int/float values in numpy array
# 3 - load models and generate predictions
# 4 - return preds as json to parent lambda function
"""

import os
from pathlib import Path

import boto3
import joblib
import numpy as np
import pandas as pd
from botocore.config import Config

# Required to read the models from disk
from sklearn.ensemble import HistGradientBoostingRegressor  # pylint: disable=unused-import

# mitigation of potential API rate restrictions (esp for Batch API)
retry_config = Config(retries={"max_attempts": 5, "mode": "standard"})
s3 = boto3.resource("s3", config=retry_config)
client = boto3.client("s3", config=retry_config)


class Preprocess:
    def __init__(self, ipppssoot, bucket_name, key):
        self.ipppssoot = ipppssoot
        self.bucket_name = bucket_name
        self.key = key
        self.input_data = None
        self.inputs = None

    def import_data(self):
        """import job metadata file from s3 bucket"""
        bucket = s3.Bucket(self.bucket_name)
        obj = bucket.Object(self.key)
        input_data = {}
        body = obj.get()["Body"].read().splitlines()
        for line in body:
            k, v = str(line).strip("b'").split("=")
            input_data[k] = v
        return input_data

    def scrub_keys(self):
        n_files = 0
        total_mb = 0
        detector = 0
        subarray = 0
        drizcorr = 0
        pctecorr = 0
        crsplit = 0

        for k, v in self.input_data.items():
            if k == "n_files":
                n_files = int(v)
            if k == "total_mb":
                total_mb = int(np.round(float(v), 0))
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
                elif v in ["1.0", "1"]:
                    crsplit = 1
                else:
                    crsplit = 2

        i = self.ipppssoot
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

        inputs = {
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
        return inputs


def build_feature_frame(feature_dict, feature_columns, for_wallclock=False):
    """Recreate training-time preprocessing for one-row prediction."""
    categorical_cols = ["instr", "dtype", "detector", "drizcorr", "pctecorr", "crsplit", "subarray"]

    df = pd.DataFrame([feature_dict]).copy()

    if for_wallclock:
        df["log_n_files"] = np.log1p(df["n_files"])
        df["log_total_mb"] = np.log1p(df["total_mb"])
    else:
        df["n_files"] = df["n_files"].astype(float)
        df["total_mb"] = df["total_mb"].astype(float)

    for col in categorical_cols:
        df[col] = feature_dict[col]

    df = pd.get_dummies(df, columns=categorical_cols, drop_first=False)

    # Match the exact training feature order and fill unseen categories with 0.
    feature_df = df.reindex(columns=feature_columns, fill_value=0.0)
    return feature_df.astype(float)


def get_model_path():
    is_lambda_environment = "AWS_LAMBDA_FUNCTION_NAME" in os.environ
    if is_lambda_environment:
        return Path("models")
    else:
        return Path("lambda/JobPredict/models")


def predict_memory(feature_dict):
    """Predict memory in GB and memory bin for a given feature dict."""
    model_path = get_model_path() / "memory_model.pkl"
    saved = joblib.load(model_path)
    memory_model = saved["model"]
    feature_columns = saved["columns"]

    feature_df = build_feature_frame(feature_dict, feature_columns, for_wallclock=False)

    predicted_memory = memory_model.predict(feature_df)[0]

    memory = predicted_memory * 1.10
    if memory < 2:
        predicted_bin = 0
    elif memory < 8:
        predicted_bin = 1
    elif memory < 16:
        predicted_bin = 2
    else:
        predicted_bin = 3
    return predicted_memory, predicted_bin


def predict_wallclock(feature_dict):
    """Predict wallclock time in seconds for a given feature dict."""

    model_path = get_model_path() / "wallclock_model.pkl"
    saved = joblib.load(model_path)
    wallclock_model = saved["model"]
    feature_columns = saved["columns"]

    feature_df = build_feature_frame(feature_dict, feature_columns, for_wallclock=True)

    log_prediction = float(wallclock_model.predict(feature_df)[0])
    prediction = float(np.expm1(log_prediction))
    return prediction


def lambda_handler(event, context):
    """Predict Resource Allocation requirements for memory (GB) and max execution `kill time` / `wallclock` (seconds) using three pre-trained neural networks. This lambda is invoked from the Job Submit lambda which json.dumps the s3 bucket and key to the file containing job input parameters. The path to the text file in s3 assumes the following format: `control/ipppssoot/ipppssoot_MemModelFeatures.txt`.

    MEMORY BIN: classifier predicts which of 4 memory bins is most likely to be needed to process an HST dataset (ipppssoot) successfully. The probabilities of each bin are output to Cloudwatch logs and the highest bin probability is returned to the Calcloud job submit lambda invoking this one. Bin sizes are as follows:

    Memory Bins:
    0: < 2GB
    1: 2-8GB
    2: 8-16GB
    3: >16GB

    WALLCLOCK REGRESSION: regression generates estimate for specific number of seconds needed to process the dataset using the same input data. This number is then tripled in Calcloud for the sake of creating an extra buffer of overhead in order to prevent larger jobs from being killed unnecessarily.

    MEMORY REGRESSION: A third regression model is used to estimate the actual value of memory needed for the job. This is mainly for the purpose of logging/future analysis and is not currently being used for allocating memory in calcloud jobs.
    """
    bucket_name = event["Bucket"]
    key = event["Key"]
    ipppssoot = event["Ipppssoot"]

    prep = Preprocess(ipppssoot, bucket_name, key)
    prep.input_data = prep.import_data()
    prep.inputs = prep.scrub_keys()

    memval, membin = predict_memory(prep.inputs)
    clocktime = predict_wallclock(prep.inputs)

    print(f"ipppssoot: {ipppssoot} keys: {prep.input_data}")
    print(f"ipppssoot: {ipppssoot} features: {prep.inputs}")
    predictions = {"ipppssoot": ipppssoot, "memBin": membin, "memVal": memval, "clockTime": clocktime}
    print(predictions)
    return {"memBin": membin, "memVal": memval, "clockTime": clocktime}
