"""This module is the primary path for ingesting job metadata into dynamodb (which is later used to train the resource allocation models). The model-ingest lambda is triggered when a job's message status changes to "processed-{ipppssoot}.trigger".

See ModelIngest/lambda_scrape.py for more information on how model data is ingested to DDB.
"""

import boto3
import sys
import numpy as np
import datetime as dt
import time
import json
from decimal import Decimal
from pprint import pprint
from . import common

s3 = boto3.resource("s3", config=common.retry_config)
client = boto3.client("s3", config=common.retry_config)
dynamodb = boto3.resource("dynamodb", config=common.retry_config, region_name="us-east-1")


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


class Scraper:
    def __init__(self, ipst, bucket_name):
        self.ipst = ipst
        self.bucket = s3.Bucket(bucket_name)
        self.job_data = None

    def scrape_job_data(self):
        """Calls scrape functions for retrieving feature and target data.
        Returns dictionary of data to be ingested for a given ipst/job"""
        features = Features(self.ipst, self.bucket).scrape_features()
        targets = Targets(self.ipst, self.bucket).scrape_targets()
        self.job_data = {"ipst": self.ipst, "features": features, "targets": targets}
        return self.job_data


class Features(Scraper):
    def __init__(self, ipst, bucket):
        self.ipst = ipst
        self.bucket = bucket
        self.features = None

    def scrape_features(self):
        self.input_data = self.download_inputs()
        self.features = self.scrub_keys()
        return self.features

    def download_inputs(self):
        """scrapes memory model feature text files from s3 control bucket for last batch of jobs
        Returns dict of input features for each job (ipst)
        """
        key = f"control/{self.ipst}/{self.ipst}_MemModelFeatures.txt"
        obj = self.bucket.Object(key)
        input_data = {}
        try:
            body = obj.get()["Body"].read().splitlines()
        except Exception as e:
            body = None
            print(e)
        if body is None:
            print(f"Unable to download inputs: {self.ipst}")
            input_data = None
            sys.exit(3)
        else:
            for line in body:
                k, v = str(line).strip("b'").split("=")
                input_data[k] = v
            print(f"{self.ipst}: {input_data}")
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
                elif v in ["1", "1.0"]:
                    crsplit = 1
                else:
                    crsplit = 2

        i = self.ipst
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
        }
        return features


class Targets(Scraper):
    def __init__(self, ipst, bucket):
        self.ipst = ipst
        self.bucket = bucket
        self.process_log = f"outputs/{self.ipst}/process_metrics.txt"
        self.preview_log = f"outputs/{self.ipst}/preview_metrics.txt"
        self.targets = None

    def scrape_targets(self):
        self.target_data = self.get_target_data()
        self.targets = self.convert_target_data()
        return self.targets

    def get_target_data(self):
        """scrapes actual wallclock (sec) and memory (kb) from log files in s3 outputs bucket. Returns string-formatted list of scraped data.
        {'wallclock': ['1:32.79', '0:30.26'], 'memory': ['423876', '236576']}
        """
        log_files = [self.process_log, self.preview_log]
        target_data = {"wallclock": [], "memory": []}
        log_error = 0
        for key in log_files:
            obj = self.bucket.Object(key)
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
        if log_error < 0:
            print("Missing logs: cannot save target data.")
            sys.exit(-1)
        elif log_error > 0:
            print("Logs have Non-zero status: cannot save target data.")
            sys.exit(log_error)
        else:
            print(f"{self.ipst}: {target_data}")
            return target_data

    def convert_target_data(self):
        """Converts string-formatted lists into numeric values for each target.
        Returns dict of actual wallclock time (seconds) and memory usage (GB) for a given job (ipst).
        """
        targets = {"wallclock": 0, "memory": 0.0, "mem_bin": None}
        clock, kb = 0, 0
        for timestr in self.target_data["wallclock"]:
            clocktime = reversed(timestr.split(".")[0].split(":"))
            clock += sum(x * int(t) for x, t in zip([1, 60, 3600], clocktime))
            print(clock)
        for memstr in self.target_data["memory"]:
            kb += float(memstr)
            print(kb)
        targets["wallclock"] = clock + 1
        targets["memory"] = kb / (10**6)
        targets["mem_bin"] = self.calculate_bin(targets["memory"])
        print("Targets:\n", targets)
        return targets

    def calculate_bin(self, memory):
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


# ******** DYNAMODB INGEST


def create_payload(job_data, timestamp):
    """Converts numpy values into JSON-friendly formatting."""
    ipst = str(job_data["ipst"])
    features = job_data["features"]
    targets = job_data["targets"]
    data = {
        "ipst": ipst,
        "timestamp": int(timestamp),
        "total_mb": float(features["total_mb"]),
        "n_files": int(features["n_files"]),
        "drizcorr": int(features["drizcorr"]),
        "pctecorr": int(features["pctecorr"]),
        "crsplit": int(features["crsplit"]),
        "subarray": int(features["subarray"]),
        "detector": int(features["detector"]),
        "dtype": int(features["dtype"]),
        "instr": int(features["instr"]),
        "memory": float(targets["memory"]),
        "wallclock": float(targets["wallclock"]),
        "mem_bin": int(targets["mem_bin"]),
    }
    ddb_payload = json.loads(json.dumps(data, allow_nan=True), parse_int=Decimal, parse_float=Decimal)
    pprint(ddb_payload, indent=2)
    return ddb_payload


def put_job_data(ddb_payload, table_name):
    """Gets (or creates) DynamoDB table and puts JSON-formatted job data into the database."""
    table = dynamodb.Table(table_name)
    response = table.put_item(Item=ddb_payload)
    return response


def ddb_ingest(ipst, bucket_name, table_name):
    start_time = time.time()
    print_timestamp(start_time, "all", 0)
    scraper = Scraper(ipst, bucket_name)
    job_data = scraper.scrape_job_data()
    ddb_payload = create_payload(job_data, start_time)
    job_resp = put_job_data(ddb_payload, table_name)
    print("Put job data succeeded:")
    pprint(job_resp, indent=2)
    end_time = time.time()
    print_timestamp(end_time, "SCRAPE and INGEST", 1)
    duration = proc_time(start_time, end_time)
    print(f"Data ingest took {duration}\n")
