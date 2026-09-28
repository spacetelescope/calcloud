"""This module is the primary path for ingesting job metadata into dynamodb (which is later used to train the resource allocation models). The model-ingest lambda is triggered when a job's message status changes to "processed-{ipppssoot}.trigger".

See ModelIngest/lambda_scrape.py for more information on how model data is ingested to DDB.
"""

import boto3
import datetime as dt
import json
import sys
import time
from decimal import Decimal
from pprint import pformat
from . import common, hst, job_features, log

logger = log.configure_logging()

s3 = boto3.resource("s3", config=common.retry_config)
client = boto3.client("s3", config=common.retry_config)
dynamodb = boto3.resource("dynamodb", config=common.retry_config, region_name="us-east-1")


def proc_time(start, end):
    duration = round(end - start)
    proc_time = round(duration / 60)
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
    logger.info("%s [%s]: %s", info, name, timestring)


class Scraper:
    def __init__(self, ipst, bucket_name):
        self.ipst = ipst
        self.bucket = s3.Bucket(bucket_name)
        self.job_data = None

    def scrape_job_data(self):
        """Calls scrape functions for retrieving feature and target data.
        Returns dictionary of data to be ingested for a given ipst/job"""
        feature_scraper = Features(self.ipst, self.bucket)
        features = feature_scraper.scrape_features()
        if features is None:
            return None

        targets = Targets(self.ipst, self.bucket).scrape_targets()
        dataset_type = hst.get_dataset_type(self.ipst)
        self.job_data = {
            "ipst": self.ipst,
            "features": features,
            "targets": targets,
            "store_data": dataset_type == "ipst" or feature_scraper.incoming_dataset_type_present,
        }
        return self.job_data


class Features(Scraper):
    def __init__(self, ipst, bucket):
        self.ipst = ipst
        self.bucket = bucket
        self.features = None
        self.input_feature_keys = []
        self.incoming_dataset_type_present = False

    def scrape_features(self):
        self.input_data = self.download_inputs()
        if self.input_data is None:
            return None
        self.input_feature_keys = list(self.input_data.keys())
        self.incoming_dataset_type_present = any(key.lower() == "dataset_type" for key in self.input_feature_keys)
        self.features = job_features.extract_input_features(self.ipst, self.input_data)
        return self.features

    def download_inputs(self):
        """scrapes memory model feature text files from s3 control bucket for last batch of jobs
        Returns dict of input features for each job (ipst)
        """
        key = f"control/{self.ipst}/{self.ipst}_MemModelFeatures.txt"
        input_data = {}
        body = job_features.get_s3_body_str_lines(self.bucket, key)
        if body is None:
            logger.info("Unable to download inputs: %s", self.ipst, extra={"dataset": self.ipst})
            return None
        else:
            for line in body:
                k, v = line.split("=", 1)
                input_data[k] = v
            logger.debug("%s: %s", self.ipst, input_data, extra={"dataset": self.ipst})
            return input_data


class Targets(Scraper):
    def __init__(self, ipst, bucket):
        self.ipst = ipst
        self.bucket = bucket
        self.process_log = f"outputs/{self.ipst}/process_metrics.txt"
        self.preview_log = f"outputs/{self.ipst}/preview_metrics.txt"
        self.disk_log = f"outputs/{self.ipst}/disk_metrics.txt"
        self.targets = None

    def scrape_targets(self):
        self.target_data = self.get_target_data()
        self.targets = self.convert_target_data()
        return self.targets

    def get_wallclock_and_memory_lists(self) -> tuple[int, list[str], list[str]]:
        """Return log_error, wallclock values, and memory values from the process and preview logs."""
        log_files = [self.process_log, self.preview_log]
        wallclock_list = []
        memory_list = []
        log_error = 0
        for key in log_files:
            body = job_features.get_s3_body_str_lines(self.bucket, key)
            if body is not None:
                status = body[-1].split(":")[-1]
                if "0" in status:
                    clockstring = body[4].strip()
                    wallclock = clockstring.replace("Elapsed (wall clock) time (h:mm:ss or m:ss): ", "")
                    wallclock_list.append(wallclock)

                    kbstring = body[9].strip()
                    kb = kbstring.replace("Maximum resident set size (kbytes): ", "")
                    memory_list.append(kb)
                else:
                    logger.warning("log status has non-zero value: %s", status, extra={"dataset": self.ipst})
                    log_error += 1
            else:
                log_error = -1
        return log_error, wallclock_list, memory_list

    def get_max_disk_usage(self) -> int | None:
        """Returns the maximum disk usage recorded in the disk_metrics log, in GB."""
        max_disk = 0
        body = job_features.get_s3_body_str_lines(self.bucket, self.disk_log)
        if body:
            for line in body:
                items = line.split()
                if len(items) == 6 and len(items[2]) > 1 and items[2][-1] == "G":
                    value_str = items[2][:-1]
                    if value_str.isdigit():
                        max_disk = max(max_disk, int(value_str))
        return max_disk or None

    def get_target_data(self):
        """scrapes actual wallclock (sec) and memory (kb) from log files in s3 outputs bucket. Returns string-formatted list of scraped data.
        {'wallclock': ['1:32.79', '0:30.26'], 'memory': ['423876', '236576']}
        """

        target_data = {"wallclock": [], "memory": []}
        log_error, wallclock_list, memory_list = self.get_wallclock_and_memory_lists()
        target_data["wallclock"] = wallclock_list
        target_data["memory"] = memory_list

        max_disk = self.get_max_disk_usage()
        if max_disk is not None:
            target_data["max_disk"] = max_disk

        if log_error < 0:
            logger.error("Missing logs: cannot save target data.", extra={"dataset": self.ipst})
            sys.exit(-1)
        elif log_error > 0:
            logger.error("Logs have Non-zero status: cannot save target data.", extra={"dataset": self.ipst})
            sys.exit(log_error)
        else:
            logger.info("%s: %s", self.ipst, target_data, extra={"dataset": self.ipst})
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
            logger.debug("clock=%s", clock)
        for memstr in self.target_data["memory"]:
            kb += float(memstr)
            logger.debug("kb=%s", kb)
        targets["wallclock"] = clock + 1
        targets["memory"] = kb / (10**6)
        targets["mem_bin"] = self.calculate_bin(targets["memory"])
        if "max_disk" in self.target_data:
            max_disk = self.target_data["max_disk"]
            logger.debug("max_disk=%s", max_disk)
            targets["max_disk"] = max_disk
        logger.info("Targets:\n%s", targets, extra={"dataset": self.ipst})
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
        "ipst": ipst,  # Historical tag, new data use "dataset"
        "dataset": ipst,
        "timestamp": timestamp,
        "total_mb": features["total_mb"],
        "n_files": features["n_files"],
        "drizcorr": features.get("drizcorr"),
        "pctecorr": features.get("pctecorr"),
        "crsplit": features.get("crsplit"),
        "subarray": features.get("subarray"),
        "detector": features.get("detector"),
        "dtype": features.get("dtype"),
        "instr": features.get("instr"),
        "dataset_type": features.get("dataset_type"),
        "memory": targets["memory"],
        "wallclock": targets["wallclock"],
        "mem_bin": targets["mem_bin"],
        "max_disk": targets.get("max_disk"),
    }
    data = {k: v for k, v in data.items() if v is not None}

    ddb_payload = json.loads(json.dumps(data, allow_nan=True), parse_int=Decimal, parse_float=Decimal)
    logger.debug("%s", pformat(ddb_payload, indent=2), extra={"dataset": ipst})
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
    if job_data is None:
        # If HSTSDP wants to bypass processing in the cloud, it does not upload the _MemModelFeatures.txt file
        # and creates a "processed-<dataset>.trigger" file.  The trigger file causes lambda_scrape to run, but
        # no processing was actually done.  In this case, skip model_ingest.py without error.
        print(f"No job data found for {ipst}, skipping model_ingest.py")
        return

    # Prior to HSTDP-2026.3.0, the on-premises code sends the same dummy feature file for all SVMs and MVMs.
    # We do not want to store this dummy data in DynamoDB.
    # After we deploy HSTDP-2026.3.0 to Ops, the on-premises code will be sending real data about SVMs and MVMs, and so
    # we should remove the job_data["store_data"] condition and store all data in DynamoDB.
    if job_data["store_data"]:
        ddb_payload = create_payload(job_data, start_time)
        job_resp = put_job_data(ddb_payload, table_name)
        logger.info(
            "Put job data succeeded:\n%s",
            pformat(job_resp, indent=2),
            extra={"dataset": ipst},
        )
        end_time = time.time()
        print_timestamp(end_time, "SCRAPE and INGEST", 1)
        duration = proc_time(start_time, end_time)
        logger.info("Data ingest took %s", duration, extra={"dataset": ipst})
    else:
        logger.info(
            "Not storing data for %s %s - no dataset_type in features",
            job_data["features"].get("dataset_type"),
            ipst,
            extra={"dataset": ipst},
        )
