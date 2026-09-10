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
from calcloud import job_features

# Required to read the models from disk
from sklearn.ensemble import HistGradientBoostingRegressor  # noqa: F401 pylint: disable=unused-import

# mitigation of potential API rate restrictions (esp for Batch API)
retry_config = Config(retries={"max_attempts": 5, "mode": "standard"})
s3 = boto3.resource("s3", config=retry_config)
client = boto3.client("s3", config=retry_config)


# Load the models at container start time
def get_model_path():
    is_lambda_environment = "AWS_LAMBDA_FUNCTION_NAME" in os.environ
    if is_lambda_environment:
        return Path("models")
    else:
        return Path("lambda/JobPredict/models")


memory_model_path = get_model_path() / "memory_model.pkl"
memory_model_saved = joblib.load(memory_model_path)

wallclock_model_path = get_model_path() / "wallclock_model.pkl"
wallclock_saved = joblib.load(wallclock_model_path)


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
        input_data = {}
        body = job_features.get_s3_body(bucket, self.key)
        for line in body:
            k, v = line.split("=", 1)
            input_data[k] = v
        return input_data

    def scrub_keys(self):
        return job_features.extract_input_features(self.ipppssoot, self.input_data)


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


def predict_memory(feature_dict):
    """Predict memory in GB and memory bin for a given feature dict."""
    memory_model = memory_model_saved["model"]
    feature_columns = memory_model_saved["columns"]

    feature_df = build_feature_frame(feature_dict, feature_columns, for_wallclock=False)

    predicted_memory = memory_model.predict(feature_df)[0]

    # 128 of 1024 MB is reserved for ECS.  See locals.tf.
    available_memory = 1 - (128 / 1024)

    memory = predicted_memory * 1.10
    if memory < 2 * available_memory:
        predicted_bin = 0
    elif memory < 8 * available_memory:
        predicted_bin = 1
    elif memory < 16 * available_memory:
        predicted_bin = 2
    else:
        predicted_bin = 3
    return float(predicted_memory), predicted_bin


def predict_wallclock(feature_dict):
    """Predict wallclock time in seconds for a given feature dict."""

    wallclock_model = wallclock_saved["model"]
    feature_columns = wallclock_saved["columns"]

    feature_df = build_feature_frame(feature_dict, feature_columns, for_wallclock=True)

    log_prediction = float(wallclock_model.predict(feature_df)[0])
    prediction = float(np.expm1(log_prediction))
    return prediction


def lambda_handler(event, context):
    """Predict Resource Allocation requirements for memory (GB) and max execution `kill time` / `wallclock` (seconds)
    using HistGradientBoostingRegressor regressions from scikit-learn.  This lambda is invoked from the
    Job Submit lambda which json.dumps the s3 bucket and key to the file containing job input parameters.
    The path to the text file in s3 assumes the following format: `control/ipppssoot/ipppssoot_MemModelFeatures.txt`.

    Returns dictionary with:
    * memBin:    Prediction of which of 4 memory bins needed to process HST dataset (ipppssoot).
                 0: < 2GB
                 1: 2-8GB
                 2: 8-16GB
                 3: >16GB
    * memVal:    Predicted memory value in GB needed to process the HST dataset (ipppssoot).
                 memBin is derived from this.
    * clockTime: Predicted wallclock time in seconds needed to process the HST dataset (ipppssoot).
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
