import sys
import csv
import math

from . import dynamodb
from . import s3
from . import log

# --------------------------------------------------------------------------------


def load_blackboard(filename, delimiter="|", item_key="dataset"):
    """Loader for dump of on-prem HST blackboard defining known resource usage.

    Returns { row_dict[item_key]: row_dict, ...}

    where `row_dict` is a dictionary with keys that are column names and
    corresponding row values.
    """
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=delimiter)
        columns = tuple(col.strip() for col in reader.__next__())
        db_dict = {}
        for row in reader:
            converted = tuple(dynamodb.convert(v) for v in row)
            item_dict = dict(zip(columns, converted))
            item_dict.pop("", None)
            db_dict[item_dict[item_key]] = {
                item_key: item_dict[item_key],
                "memory_megabytes": math.ceil(item_dict["imageSize"] / 1024),
                "wallclock_seconds": item_dict["jobduration"],
                "cpus": 1,
            }
    return db_dict


# --------------------------------------------------------------------------------

DB = dynamodb.DynamoDB("calcloud-hst-job-info", "dataset")


def load_db(filepath):
    DB.init_db(load_blackboard(filepath))


def get_resources(dataset):
    """Given ipppssoot `dataset`, return:
    (memory_megabytes, cpus, wallclock_seconds)
    """
    raise KeyError("Forced get_resources error for", dataset)
    item = DB.get_item(dataset)
    memory_megabytes = item["memory_megabytes"]
    cpus = item.get("cpus", 1)  # original blackboard doesn't have these
    wallclock_seconds = item["wallclock_seconds"]
    return memory_megabytes, cpus, wallclock_seconds


def set_resources(dataset, memory_megabytes, cpus, wallclock_seconds):
    """Update the resource metrics database for ipppssoot `dataset` with measured
    values for `memory_megabytes`, `cpus` effectively used/available, and
    `walkclock_seconds` of runtime.
    """
    item = DB.get_item(dataset)
    item["memory_megabytes"] = memory_megabytes
    item["cpus"] = cpus
    item["wallclock_seconds"] = wallclock_seconds
    DB.update_item(item)


# --------------------------------------------------------------------------------

# This is throw-away code if the /usr/bin/time metrics turn out to be unusable.
# It might however illustrate loading metrics from S3 in general if it turns out
# that container-based metrics are viable in some form, e.g. based on psutils,
# or aspects of any lambda based on CloudWatch metrics.


def update_resources(s3_batch_path):
    """Extract the process_metrics.txt files from every ipppssoot in a batch and
    use them to overwrite or add a metrics database entry.
    """
    process_metrics_s3 = [
        metric for metric in s3.list_directory(s3_batch_path, max_objects=10 ** 7) if "process_metric" in metric
    ]
    for s3_path in process_metrics_s3:
        log.info("Processing metrics for", s3_path)
        metrics_text = s3.get_object(s3_path)
        dataset = s3_path.split("/")[-3]
        memory, cpus, seconds = parse_time_metrics(metrics_text)
        set_resources(dataset, memory, cpus, seconds)


def parse_time_metrics(metrics_text):
    """Parse the verbose output of GNU /usr/bin/time included in the original
    caldp container to extract the memory resident set size, wallclock time,
    and CPU's utilized.

    For outlier (jcl403010) with 49.6G RAM reported in the blackboard,
    the RSS of approx 8000 reported by "time" was insufficient to run
    the container.  2x or roughly 16000 succeeded.

    Add 2x fudge here so reported numbers are directly usable and
    metric-specific fudge is not hardcoded in the planner or
    provisioner.  (This fudge is property of this measurement).

    Returns memory_megabytes, cpus, wallclock_seconds
    """
    for line in metrics_text.splitlines():
        line = line.strip()
        words = line.split()
        if line.startswith("Percent of CPU"):
            percent = words[-1][:-1]
            cpus = math.ceil(int(percent) / 100)
        elif line.startswith("Maximum resident set size"):
            kilobytes = int(words[-1])
            memory_megabytes = math.ceil(kilobytes / 1024 * 2)
        elif line.startswith("Elapsed (wall clock) time"):
            parts = words[-1].split(":")
            if len(parts) == 2:
                h, m, ss = 0, parts[0], parts[1]
            elif len(parts) == 3:
                h, m, ss = parts
            h, m, ss = map(lambda x: int(float(x)), [h, m, ss])
            wallclock_seconds = h * 3600 + m * 60 + ss
    return memory_megabytes, cpus, wallclock_seconds


# --------------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python -m calcloud.metrics  <blackboard_dump_file>", file=sys.stderr)
        sys.exit(1)
    else:
        load_db(sys.argv[1])
