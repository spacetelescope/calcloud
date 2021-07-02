import boto3
from botocore.config import Config
import sys
import os
import numpy as np
import datetime as dt
import time
import json
from decimal import Decimal
from pprint import pprint
from sklearn.preprocessing import PowerTransformer
import urllib.parse

# mitigation of potential API rate restrictions (esp for Batch API)
retry_config = Config(retries={"max_attempts": 5, "mode": "standard"})
s3 = boto3.resource("s3", config=retry_config)
client = boto3.client("s3", config=retry_config)
dynamodb = boto3.resource("dynamodb", config=retry_config, region_name="us-east-1")


def proc_time(start, end):
    duration = np.round(end - start)
    proc_time = np.round(duration / 60)
    if duration > 3600:
        return f"{proc_time} hours."
    elif duration > 60:
        return f"{proc_time} minutes."
    else:
        return f"{duration} seconds."


def print_timestamp(ts, name, value):
    if value == 0:
        info = "STARTED"
    elif value == 1:
        info = "FINISHED"
    else:
        info = ""
    timestring = dt.datetime.fromtimestamp(ts).strftime("%m/%d/%Y - %H:%M:%S")
    print(f"{info} [{name}]: {timestring}")


""" ----- FEATURES ----- """


def download_inputs(ipst, bucket_name):
    """scrapes memory model feature text files from s3 control bucket for last batch of jobs
    Returns dict of input features for each job (ipst)
    """
    bucket = s3.Bucket(bucket_name)
    key = f"control/{ipst}/{ipst}_MemModelFeatures.txt"
    obj = bucket.Object(key)
    input_data = {}
    try:
        body = obj.get()["Body"].read().splitlines()
    except Exception as e:
        body = None
        print(e)
    if body is not None:
        for line in body:
            k, v = str(line).strip("b'").split("=")
            input_data[k] = v
        print(f"{ipst}: {input_data}")
        return input_data
    else:
        print("Unable to download inputs")
        sys.exit(3)


def scrub_keys(ipst, input_data):
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
            elif v == "1.0":
                crsplit = 1
            else:
                crsplit = 2

    i = ipst
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

    inputs = np.array([n_files, total_mb, drizcorr, pctecorr, crsplit, subarray, detector, dtype, instr])
    return inputs


def transformer(inputs):
    """applies yeo-johnson power transform to first two indices of array (n_files, total_mb) using lambdas, mean and standard deviation calculated for each variable prior to model training.

    Returns: X inputs as 2D-array for generating predictions
    """
    X = inputs
    n_files = X[0]
    total_mb = X[1]
    # apply power transformer normalization to continuous vars
    x = np.array([[n_files], [total_mb]]).reshape(1, -1)
    pt = PowerTransformer(standardize=False)
    # TODO: get pt.lambdas vals from s3 calcloud-modeling/latest
    pt.lambdas_ = np.array([-1.51, -0.12])
    xt = pt.transform(x)
    # normalization (zero mean, unit variance)
    f_mean, f_sigma = 0.5682815234265285, 0.04222565843608133
    s_mean, s_sigma = 1.6250374589283951, 1.0396138451086632
    x_files = np.round(((xt[0, 0] - f_mean) / f_sigma), 5)
    x_size = np.round(((xt[0, 1] - s_mean) / s_sigma), 5)
    # print(f"Power Transformed variables: {x_files}, {x_size}")
    X_values = {
        "x_files": x_files,
        "x_size": x_size,
        "n_files": n_files,
        "total_mb": total_mb,
        "drizcorr": X[2],
        "pctecorr": X[3],
        "crsplit": X[4],
        "subarray": X[5],
        "detector": X[6],
        "dtype": X[7],
        "instr": X[8],
    }
    # X = np.array([x_files, x_size, X[2], X[3], X[4], X[5], X[6], X[7], X[8]])
    return X_values


def scrape_features(ipst, bucket_name):
    start = time.time()
    print_timestamp(start, "features", 0)
    input_data = download_inputs(ipst, bucket_name)
    if len(input_data) > 0:
        inputs = scrub_keys(ipst, input_data)
        features = transformer(inputs)
    else:
        features = None
    print("Features:\n ", features)
    end = time.time()
    duration = proc_time(start, end)
    print_timestamp(end, "features", 1)
    print(f"Scrape features took {duration}\n")
    return features


""" ----- TARGETS ----- """


def get_target_data(ipst, bucket_name):
    """scrapes actual wallclock (sec) and memory (kb) from log files in s3 outputs bucket. Returns string-formatted list of scraped data.
    {'wallclock': ['1:32.79', '0:30.26'], 'memory': ['423876', '236576']}
    """
    bucket = s3.Bucket(bucket_name)
    log_files = [f"outputs/{ipst}/process_metrics.txt", f"outputs/{ipst}/preview_metrics.txt"]
    target_data = {"wallclock": [], "memory": []}
    log_error = 0
    for key in log_files:
        obj = bucket.Object(key)
        try:
            body = obj.get()["Body"].read().splitlines()
        except Exception as e:
            body = None
            print(e)
        if body is not None:
            status = str(body[-1]).split(":")[-1]
            if "0" in status:
                # get wallclock time duration strings
                clockstring = str(body[4]).strip("b'\\t")
                wallclock = str(clockstring).replace("Elapsed (wall clock) time (h:mm:ss or m:ss): ", "")
                target_data["wallclock"].append(wallclock)
                # get memory usage strings
                kbstring = str(body[9]).strip("b'\\t")
                kb = str(kbstring).replace("Maximum resident set size (kbytes): ", "")
                target_data["memory"].append(kb)
            else:
                print(f"log status has non-zero value: {status}")
                log_error += 1  # processing error status (bad data)
        else:
            log_error = -1  # log file missing or inaccessible

    print(f"{ipst}: {target_data}")
    return target_data, log_error


def calculate_bin(memory):
    """Calculates the memory bin (EC2 Instance type) according to the amount of memory in gigabytes needed to process the job."""
    if memory < 1.792:
        mem_bin = 0
    elif memory < 7.168:
        mem_bin = 1
    elif memory < 14.336:
        mem_bin = 2
    elif memory >= 14.336:
        mem_bin = 3
    else:
        mem_bin = "nan"
    return mem_bin


def convert_target_data(target_data):
    """Converts string-formatted lists into numeric values for each target.
    Returns dict of actual wallclock time (seconds) and memory usage (GB) for a given job (ipst).
    """
    targets = {"wallclock": 0, "memory": 0.0, "mem_bin": None}
    clock, kb = 0, 0
    for timestr in target_data["wallclock"]:
        clocktime = reversed(timestr.split(".")[0].split(":"))
        clock += sum(x * int(t) for x, t in zip([1, 60, 3600], clocktime))
    for memstr in target_data["memory"]:
        kb += np.float(memstr)
    targets["wallclock"] = clock + 1
    targets["memory"] = kb / (10 ** 6)
    targets["mem_bin"] = calculate_bin(targets["memory"])
    return targets


def scrape_targets(ipst, bucket_proc):
    start = time.time()
    print_timestamp(start, "targets", 0)
    target_data, log_error = get_target_data(ipst, bucket_proc)
    if log_error < 0:
        print("Missing logs: cannot save target data.")
        sys.exit(-1)
    elif log_error > 0:
        print("Logs have Non-zero status: cannot save target data.")
        sys.exit(log_error)
    else:
        targets = convert_target_data(target_data)
    end = time.time()
    duration = proc_time(start, end)
    print_timestamp(end, "targets", 1)
    print(f"Scrape targets took {duration}\n")
    return targets


# ******** DYNAMODB


def create_payload(ipst, features, targets, timestamp):
    """Converts numpy values into JSON-friendly formatting."""
    data = {
        "ipst": str(ipst),
        "timestamp": int(timestamp),
        "x_files": float(features["x_files"]),
        "x_size": float(features["x_size"]),
        "total_mb": float(features["total_mb"]),
        "n_files": int(features["n_files"]),
        "drizcorr": int(features["drizcorr"]),
        "pctecorr": int(features["drizcorr"]),
        "crsplit": int(features["pctecorr"]),
        "subarray": int(features["subarray"]),
        "detector": int(features["detector"]),
        "dtype": int(features["dtype"]),
        "instr": int(features["instr"]),
        "memory": float(targets["memory"]),
        "wallclock": float(targets["wallclock"]),
        "mem_bin": int(targets["mem_bin"]),
    }

    ddb_payload = json.loads(json.dumps(data, allow_nan=True), parse_int=Decimal, parse_float=Decimal)
    pprint(ddb_payload, sort_dicts=False, indent=2)
    return ddb_payload


def put_job_data(ddb_payload, table_name):
    """Gets (or creates) DynamoDB table and puts JSON-formatted job data into the database."""
    table = dynamodb.Table(table_name)
    response = table.put_item(Item=ddb_payload)
    return response


def lambda_handler(event, context=None):
    start = time.time()
    table_name = os.environ.get("DDBTABLE", "calcloud-hst-db")
    # table = get_ddb_table("calcloud-hst-data")
    print_timestamp(start, "all", 0)
    # print("Received event: " + json.dumps(event, indent=2))
    event_time = event["Records"][0]["eventTime"].split(".")[0]
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )  # messages/processed-iaao11ofq.trigger
    ipst = key.split("-")[-1].split(".")[0]
    timestamp = dt.datetime.fromisoformat(event_time).timestamp()
    features = scrape_features(ipst, bucket_name)
    targets = scrape_targets(ipst, bucket_name)
    ddb_payload = create_payload(ipst, features, targets, timestamp)
    job_resp = put_job_data(ddb_payload, table_name)
    print("Put job data succeeded:")
    pprint(job_resp, sort_dicts=False)
    end = time.time()
    duration = proc_time(start, end)
    print_timestamp(end, "all", 1)
    print(f"Data ingest took {duration}\n")
