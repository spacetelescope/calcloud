import os
import sys
import boto3
from botocore.config import Config
import numpy as np
import pandas as pd
import datetime as dt
from datetime import timedelta
import time
from sklearn.preprocessing import PowerTransformer
from . import io

# mitigation of potential API rate restrictions (esp for Batch API)
retry_config = Config(retries={"max_attempts": 5, "mode": "standard"})
s3 = boto3.resource("s3", config=retry_config)
client = boto3.client("s3", config=retry_config)
log_client = boto3.client("logs", "us-east-1")


""" ----- JOBS (MESSAGES) ----- """


def list_messages(bucket_name):
    prefix = "messages"
    paginator = client.get_paginator("list_objects_v2")
    max_objects = 10 ** 30
    config = {"MaxItems": max_objects, "PageSize": 1000}
    messages = []
    print("Searching messages...")
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix, PaginationConfig=config):
        for result in page.get("Contents", []):
            key = result["Key"].split("/")[-1]
            messages.append(key)
    n_running = 0
    for m in messages:
        msg = m.split("-")[0]
        if msg == "processing":
            n_running += 1
    print(f"Found {len(messages)} messages.")

    return messages, n_running


def list_jobs(messages):
    succeeded, processing, errors = [], [], []
    n_errors = 0
    n_ingested = 0
    n_processed = 0
    n_running = 0
    for m in messages:
        msg = m.split("-")[0]
        ipst = m.split("-")[-1]
        if msg == "error":
            errors.append(ipst)
            n_errors += 1
        elif msg == "ingested":
            succeeded.append(ipst)
            n_ingested += 1
        elif msg == "processed":
            ipst = ipst.split(".")[0]
            succeeded.append(ipst)
            n_processed += 1
        else:
            processing.append(ipst)
            n_running += 1
    msg_count = n_errors + n_ingested + n_processed + n_running
    print(f"Found {msg_count} completed job messages.")
    print(f"Found {n_errors} error messages.")
    print(f"Found {n_ingested} ingested jobs.")
    print(f"Found {n_processed} processed jobs.")
    print(f"Jobs still running: {n_running}")
    print(f"Total # successful jobs: {len(succeeded)}")
    if len(succeeded) < 1:
        print("No data found for ingest - exiting program.")
        sys.exit()
    else:
        job_dict = {"succeeded": succeeded, "processing": processing, "errors": errors}
        return job_dict


def scrape_jobs(bucket_proc, bucket_mod, prefix):
    start = time.time()
    print(f"STARTED [jobs]: {dt.datetime.fromtimestamp(start).strftime('%m/%d/%Y - %H:%M:%S')}")
    messages, n_running = list_messages(bucket_proc)
    if n_running > 0:
        print(f"Warning: {n_running} jobs are still processing.")
    jobs = list_jobs(messages)
    job_dict = {"jobs": jobs}
    keys = io.save_to_file(job_dict)
    io.s3_upload(keys, bucket_mod, prefix)
    end = time.time()
    duration = io.proc_time(start, end)
    print(f"FINISHED [jobs]: {dt.datetime.fromtimestamp(end).strftime('%m/%d/%Y - %H:%M:%S')}")
    print(f"Scrape Jobs took {duration}\n")
    return jobs


""" ----- FEATURES ----- """


def get_feature_data(bucket_name, jobs, verbose=0):
    """scrapes memory model feature text files from s3 control bucket for last batch of jobs
    Returns dict of input features for each job (ipst)
    """
    bucket = s3.Bucket(bucket_name)
    input_data = {}
    ctrl_missing = []

    for ipst in jobs:
        key = f"control/{ipst}/{ipst}_MemModelFeatures.txt"
        if ipst not in list(input_data.keys()):
            input_data[ipst] = {}
        obj = bucket.Object(key)
        body = None
        try:
            body = obj.get()["Body"].read().splitlines()
        except Exception:
            ctrl_missing.append(key)
            continue
        if body is not None:
            for line in body:
                k, v = str(line).strip("b'").split("=")
                input_data[ipst][k] = v
        if verbose:
            print(f"{ipst}: {input_data[ipst]}")
    return input_data, ctrl_missing


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


def convert_feature_data(input_data):
    feature_inputs = {}
    X_data = {}
    for ipst, data in input_data.items():
        if len(data) > 0:
            inputs = scrub_keys(ipst, data)
            feature_inputs[ipst] = inputs
            X_values = transformer(inputs)
            X_data[ipst] = X_values

    feature_data = {}
    for ipst, inputs in feature_inputs.items():
        X = inputs
        feature_data[ipst] = {
            "n_files": X[0],
            "total_mb": X[1],
            "drizcorr": X[2],
            "pctecorr": X[3],
            "crsplit": X[4],
            "subarray": X[5],
            "detector": X[6],
            "dtype": X[7],
            "instr": X[8],
        }

    return feature_data, X_data, feature_inputs


def make_features(feature_data, X_data):
    raw = pd.DataFrame(feature_data.values(), index=list(feature_data.keys()))[["n_files", "total_mb"]]
    normalized = pd.DataFrame(X_data.values(), index=list(X_data.keys()))
    df = pd.concat([raw, normalized], axis=1)
    drop_zeros = df.loc[df["n_files"] == 0].index
    df.drop(drop_zeros, axis=0, inplace=True)
    key = "features.csv"
    io.save_dataframe(df, key)
    return df, key


def scrape_features(bucket_proc, bucket_mod, jobs, prefix):
    start = time.time()
    print(f"STARTED [features]: {dt.datetime.fromtimestamp(start).strftime('%m/%d/%Y - %H:%M:%S')}")
    input_data, ctrl_missing = get_feature_data(bucket_proc, jobs, verbose=1)
    feature_data, X_data, inputs = convert_feature_data(input_data)
    df, df_key = make_features(feature_data, X_data)
    feature_dict = {"input_data": input_data, "ctrl_missing": ctrl_missing, "feature_inputs": inputs}
    feat_keys = io.save_dict(feature_dict, df_key)
    io.s3_upload(feat_keys, bucket_mod, prefix)
    end = time.time()
    duration = io.proc_time(start, end)
    print(f"FINISHED [features]: {dt.datetime.fromtimestamp(end).strftime('%m/%d/%Y - %H:%M:%S')}")
    print(f"Scrape features took {duration}\n")
    return df


""" ----- TARGETS ----- """


def make_loglist(jobs):
    """Returns list of metrics log files for completed jobs in s3 outputs bucket
    ['outputs/j6d508o6q/preview_metrics.txt', 'outputs/j6d508o6q/process_metrics.txt']
    """
    log_files = []
    for ipst in jobs:
        log_files.append(f"outputs/{ipst}/preview_metrics.txt")
        log_files.append(f"outputs/{ipst}/process_metrics.txt")
    print("LogFiles: ", len(log_files))
    return log_files


def get_target_data(bucket_name, log_files, verbose=1):
    """scrapes actual wallclock (sec) and memory (kb) from all metrics log files in s3 outputs bucket for the last batch of jobs.
    Returns dict of actual wallclock time (seconds) and memory usage (GB) for each job (ipst).
    {'j6d508o6q': {'wallclock': 44.0, 'memory': 0.481348}}
    """
    bucket = s3.Bucket(bucket_name)
    target_data = {}
    log_missing = []
    log_errors = []
    err = None
    for key in log_files:  # 'outputs/j6d508o6q/preview_metrics.txt'
        ipst = key.split("/")[-2]
        if ipst not in list(target_data.keys()):
            target_data[ipst] = {"wallclock": [], "memory": []}
            count = 1
        else:
            count = 2
        obj = bucket.Object(key)
        body = None
        try:
            body = obj.get()["Body"].read().splitlines()
        except Exception as e:
            log_missing.append(ipst)
            err = e
        if body is not None:
            status = str(body[-1]).split(":")[-1]
            if "0" in status:
                clockstring = str(body[4]).strip("b'\\t")
                wallclock = str(clockstring).replace("Elapsed (wall clock) time (h:mm:ss or m:ss): ", "")
                target_data[ipst]["wallclock"].append(wallclock)
                kbstring = str(body[9]).strip("b'\\t")
                kb = str(kbstring).replace("Maximum resident set size (kbytes): ", "")
                target_data[ipst]["memory"].append(kb)
                if verbose and count == 2:
                    print(f"{ipst}:{target_data[ipst]}")
            else:
                log_errors.append(ipst)
                if ipst in target_data:
                    del target_data[ipst]
    for ipst in log_missing:
        if ipst in target_data:
            del target_data[ipst]
    if err is not None:
        print(err)
    return target_data, log_errors, log_missing


def convert_target_data(target_data):
    targets = {}
    for ipst, _ in target_data.items():
        if ipst not in list(targets.keys()):
            targets[ipst] = {"wallclock": 0, "memory": 0.0}
        clock, kb = 0, 0
        for timestr in target_data[ipst]["wallclock"]:
            clocktime = reversed(timestr.split(".")[0].split(":"))
            clock += sum(x * int(t) for x, t in zip([1, 60, 3600], clocktime))
        for memstr in target_data[ipst]["memory"]:
            kb += np.float(memstr)
        targets[ipst]["wallclock"] = clock + 1
        targets[ipst]["memory"] = kb / (10 ** 6)
    return targets


def make_targets(targets):
    # make dataframe and memory bins
    df = pd.DataFrame.from_dict(targets, orient="index")
    # 0-2 GB
    df.loc[(list(df.loc[df["memory"] < 1.792].index)), "mem_bin"] = 0
    # 2-8 GB
    df.loc[(list(df.loc[(df["memory"] >= 1.792) & (df["memory"] < 7.168)].index)), "mem_bin"] = 1
    # 8-16 GB
    df.loc[(list(df.loc[(df["memory"] >= 7.168) & (df["memory"] < 14.336)].index)), "mem_bin"] = 2
    # 16+ GB
    df.loc[(list(df.loc[df["memory"] >= 14.336].index)), "mem_bin"] = 3
    # scrub NaNs (failed jobs/missing target data)
    nans = list(df.loc[df["mem_bin"].isna()].index)
    df.drop(nans, axis=0, inplace=True)
    key = "targets.csv"
    io.save_dataframe(df, key)
    return df, key


def scrape_targets(bucket_proc, bucket_mod, jobs, prefix):
    start = time.time()
    print(f"STARTED [targets]: {dt.datetime.fromtimestamp(start).strftime('%m/%d/%Y - %H:%M:%S')}")
    log_files = make_loglist(jobs)
    target_data, log_errors, log_missing = get_target_data(bucket_proc, log_files, verbose=1)
    targets = convert_target_data(target_data)
    df, df_key = make_targets(targets)
    target_dict = {
        "log_files": log_files,
        "log_missing": log_missing,
        "log_errors": log_errors,
        "target_data": target_data,
    }
    target_keys = io.save_dict(target_dict, df_key)
    io.s3_upload(target_keys, bucket_mod, prefix)
    end = time.time()
    duration = io.proc_time(start, end)
    print(f"FINISHED [targets]: {dt.datetime.fromtimestamp(end).strftime('%m/%d/%Y - %H:%M:%S')}")
    print(f"Scrape targets took {duration}\n")
    return df


""" ----- PREDICTIONS ----- """


def get_timestamps(t0, mins, delta=5):
    """
    t0 : starting timestamp of first log query
    mins: 840
    """
    start = int(t0)
    intervals = [start]
    for i in list(range(delta, mins, delta)):
        t = int((dt.datetime.fromtimestamp(t0) + timedelta(minutes=i)).timestamp())
        intervals.append(t)
    timestamps = []
    for i, t in enumerate(intervals):
        if i < len(intervals) - 1:
            idx1 = i
            idx2 = i + 1
            timestamps.append((intervals[idx1], intervals[idx2]))
    return timestamps


def get_query_id(start, end, log_group):
    query = "fields @message | filter 'like memBin'"
    start_query_response = log_client.start_query(
        logGroupName=log_group, startTime=start, endTime=end, queryString=query, limit=10000
    )
    return start_query_response["queryId"]


def get_query_response(query_id):
    response = None
    while response is None or response["status"] == "running":
        time.sleep(1)
        response = log_client.get_query_results(queryId=query_id)
    return response["results"]


def make_preds(results):
    predictions = []
    for res in results:
        val = res[0]["value"]
        if "memBin" in val:
            predictions.append(val)

    partial_pred = {}
    for p in predictions:
        ipst = p.split(":")[1].split(",")[0].strip(" ' ")
        partial_pred[ipst] = {
            "bin_pred": int(p.split(",")[1].split(":")[1]),
            "mem_pred": float(p.split(",")[2].split(":")[1]),
            "wall_pred": int(p.split(",")[3].replace("}", "").split(":")[1].strip("\n")),
        }
    df_preds = pd.DataFrame.from_dict(partial_pred, orient="index")
    return df_preds


def combine_preds(pred_dict):
    df = pd.DataFrame()
    for data in pred_dict.values():
        df = df.append(data)
    # drop duplicates
    df["ipst"] = df.index
    df.set_index("ipst", inplace=True, drop=False)
    df = df.drop_duplicates(subset="ipst", keep="last", inplace=False)
    return df


def run_queries(timestamps, log_group):
    pred_dict = {}
    n_preds = 0
    for (start, end) in timestamps:
        q = get_query_id(start, end, log_group=log_group)
        results = get_query_response(q)
        df_preds = make_preds(results)
        pred_dict[str(start)] = df_preds
        print(f"{str(start)}:{len(df_preds)}")
        n_preds += len(df_preds)
    print("N Preds: ", n_preds)
    df = combine_preds(pred_dict)
    io.save_dataframe(df, "preds.csv")

    return df, "preds.csv"


def scrape_predictions(bucket_mod, log_group, prefix, t0, mins):
    start = time.time()
    print(f"STARTED [predictions]: {dt.datetime.fromtimestamp(start).strftime('%m/%d/%Y - %H:%M:%S')}")
    timestamps = get_timestamps(t0, mins, delta=5)
    df, df_key = run_queries(timestamps, log_group)
    io.s3_upload([df_key], bucket_mod, prefix)
    end = time.time()
    duration = io.proc_time(start, end)
    print(f"FINISHED [predictions]: {dt.datetime.fromtimestamp(end).strftime('%m/%d/%Y - %H:%M:%S')}")
    print(f"Scrape preds took {duration}\n")
    return df


def scrape_all(bucket_mod, bucket_proc, prefix, log_group, t0, mins):
    start = time.time()
    print(f"STARTED [all]: {dt.datetime.fromtimestamp(start).strftime('%m/%d/%Y - %H:%M:%S')}")
    # STEP 1: SCRAPE JOBS (messages)
    jobs = scrape_jobs(bucket_proc, bucket_mod, prefix)
    # STEP 2: SCRAPE FEATURES (control)
    features = scrape_features(bucket_proc, bucket_mod, jobs["succeeded"], prefix)
    # STEP 3: SCRAPE TARGETS (outputs)
    targets = scrape_targets(bucket_proc, bucket_mod, jobs["succeeded"], prefix)
    # STEP 4: SCRAPE PREDS (cloudwatch logs)
    try:
        preds = scrape_predictions(bucket_mod, log_group, prefix, t0, mins)
    except Exception as e:
        print(e)
        preds = pd.DataFrame()
        io.save_dataframe(preds, "preds.csv")
        io.s3_upload(["preds.csv"], bucket_mod, prefix)
    end = time.time()
    print(f"FINISHED [all]: {dt.datetime.fromtimestamp(end).strftime('%m/%d/%Y - %H:%M:%S')}")
    return features, targets, preds


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scrape = sys.argv[1]
        scrape_args = ["all", "features", "targets", "preds"]
        if scrape not in scrape_args:
            print(f"Scrape arg invalid: {scrape} - use `all` (default), `features`, `targets`, or `preds`.")
    else:
        scrape = "all"
    bucket_mod = os.environ.get("S3MOD", "calcloud-modeling-sb")
    bucket_proc = os.environ.get("S3PROC", "calcloud-processing-sb")
    scrapetime = os.environ.get("SCRAPETIME", "now")  # final log event time
    hr_delta = int(os.environ.get("HRDELTA", 1))  # how far back in time to start
    log_group = os.environ.get("LOGPRED", "/aws/lambda/calcloud-job-predict-sb")
    mins = int(os.environ.get("MINS", 20))  # num minutes forward to scrape
    t0, data_path = io.get_paths(scrapetime, hr_delta)
    home = os.path.join(os.getcwd(), data_path)
    prefix = f"{data_path}/data"
    os.makedirs(prefix, exist_ok=True)
    os.chdir(prefix)
    print("URIs: ", bucket_mod, bucket_proc, log_group)
    print("OPTIONS: ", scrapetime, hr_delta, mins)
    print(f"Scraping {scrape} to {prefix}")
    if scrape == "all":
        F, T, P = scrape_all(bucket_mod, bucket_proc, prefix, log_group, t0, mins)
    elif scrape == "features":
        jobs = scrape_jobs(bucket_proc, bucket_mod, prefix)
        F = scrape_features(bucket_proc, bucket_mod, jobs["succeeded"], prefix)
    elif scrape == "targets":
        jobs = scrape_jobs(bucket_proc, bucket_mod, prefix)
        T = scrape_targets(bucket_proc, bucket_mod, jobs["succeeded"], prefix)
    elif scrape == "preds":
        try:
            P = scrape_predictions(bucket_mod, log_group, prefix, t0, mins)
        except Exception as e:
            print(e)
            P = pd.DataFrame()
            io.save_dataframe(P, "preds.csv")
            io.s3_upload(["preds.csv"], bucket_mod, prefix)
    os.chdir(home)
