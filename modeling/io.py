import os
import boto3
from botocore.config import Config
import datetime as dt
from datetime import timedelta
import json
import csv
import numpy as np
import zipfile

# mitigation of potential API rate restrictions (esp for Batch API)
retry_config = Config(retries={"max_attempts": 5})
client = boto3.client("s3", config=retry_config)
dynamodb = boto3.resource("dynamodb", config=retry_config, region_name="us-east-1")

""" ----- FILE I/O OPS ----- """


def get_paths(scrapetime, hr_delta):
    if scrapetime == "now":
        end_time = dt.datetime.now()
    elif isinstance(scrapetime, str):
        end_time = dt.datetime.fromisoformat(scrapetime)
    elif isinstance(int) or isinstance(float):
        end_time = dt.datetime.fromtimestamp(scrapetime)
    else:
        print(
            f"scrapetime type must be a string (datetime, isoformat) or int/float (timestamp). You passed {type(scrapetime)}."
        )
        raise ValueError
    t0 = (end_time - timedelta(hours=hr_delta)).timestamp()
    data_path = f"{dt.date.fromtimestamp(t0).isoformat()}-{str(int(t0))}"
    return t0, data_path


def proc_time(start, end):
    duration = np.round(end - start)
    proc_time = np.round(duration / 60)
    if duration > 3600:
        return f"{proc_time} hours."
    elif duration > 60:
        return f"{proc_time} minutes."
    else:
        return f"{duration} seconds."


def get_keys(items):
    keys = set([])
    for item in items:
        keys = keys.union(set(item.keys()))
    return keys


def ddb_download(table_name):
    """retrieves data from dynamodb
    Default subset is None: download all data
    To filter the query, pass a timestamp (int) to subset arg
    """
    table = dynamodb.Table(table_name)
    key_set = ["ipst"]
    raw_data = table.scan()
    if raw_data is None:
        return None
    items = raw_data["Items"]
    fieldnames = set([]).union(get_keys(items))

    while raw_data.get("LastEvaluatedKey"):
        print("Downloading ", end="")
        raw_data = table.scan(ExclusiveStartKey=raw_data["LastEvaluatedKey"])
        items.extend(raw_data["Items"])
        fieldnames - fieldnames.union(get_keys(items))

    print("\nTotal downloaded records: {}".format(len(items)))
    for f in fieldnames:
        if f not in key_set:
            key_set.append(f)
    ddb_data = {"items": items, "keys": key_set}
    return ddb_data


def write_to_csv(ddb_data, filename=None):
    if filename is None:
        filename = "batch.csv"
    with open(filename, "w") as csvfile:
        writer = csv.DictWriter(csvfile, delimiter=",", fieldnames=ddb_data["keys"], quotechar='"')
        writer.writeheader()
        writer.writerows(ddb_data["items"])
    print(f"DDB data saved to: {filename}")


def save_to_file(data_dict):
    keys = []
    for filename, data in data_dict.items():
        key = f"{filename}.txt"
        keys.append(key)
        with open(f"{key}", "w") as f:
            for item in data:
                f.writelines(f"{item}\n")
    print(f"Saved file keys:\n {keys}")
    return keys


def save_dict(data_dict, df_key=None):
    keys = []
    for key, data in data_dict.items():
        filename = f"{key}.txt"
        with open(filename, "w") as f:
            try:
                json.dump(data, f)
            except Exception as e:
                print(e)
                f.writelines(data)
        keys.append(filename)
    if df_key is not None:
        keys.append(df_key)
    print(f"File keys:\n {keys}")
    return keys


def save_dataframe(df, df_key):
    df["ipst"] = df.index
    df.to_csv(df_key, index=False)
    print(f"Dataframe saved as: {df_key}")
    df.set_index("ipst", drop=True, inplace=True)


def s3_upload(keys, bucket_name, prefix):
    err = None
    for key in keys:
        obj = f"{prefix}/{key}"  # training/date-timestamp/filename
        try:
            with open(f"{key}", "rb") as f:
                client.upload_fileobj(f, bucket_name, obj)
                print(f"Uploaded: {obj}")
        except Exception as e:
            err = e
            continue
    if err is not None:
        print(err)


def s3_download(keys, bucket_name, prefix):
    err = None
    for key in keys:
        obj = f"{prefix}/{key}"  # latest/master.csv
        print("s3 key: ", obj)
        try:
            with open(f"{key}", "wb") as f:
                client.download_fileobj(bucket_name, obj, f)
        except Exception as e:
            err = e
            continue
    if err is not None:
        print(err)


def zip_models(path_to_models, zipname="models.zip"):
    file_paths = []
    for root, _, files in os.walk(path_to_models):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)
    print("Zipping model files:")
    with zipfile.ZipFile(zipname, "w") as zip_ref:
        for file in file_paths:
            zip_ref.write(file)
            print(file)
