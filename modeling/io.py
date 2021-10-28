import os
import boto3
from botocore.config import Config
import datetime as dt
import json
import csv
import numpy as np
import zipfile
from boto3.dynamodb.conditions import Attr
import pickle
import json
from decimal import Decimal

# mitigation of potential API rate restrictions (esp for Batch API)
retry_config = Config(retries={"max_attempts": 5})
client = boto3.client("s3", config=retry_config)
dynamodb = boto3.resource("dynamodb", config=retry_config, region_name="us-east-1")

""" ----- FILE I/O OPS ----- """


def get_paths(timestamp):
    if timestamp == "now":
        train_time = dt.datetime.now()
    elif isinstance(timestamp, str):
        if len(timestamp) <= 14:
            train_time = dt.datetime.fromtimestamp(int(timestamp))
        else:
            train_time = dt.datetime.fromisoformat(timestamp)
    elif isinstance(timestamp, int) or isinstance(timestamp, float):
        train_time = dt.datetime.fromtimestamp(timestamp)
    else:
        print(
            f"Timestamp type must be a string (datetime, isoformat) or int/float (timestamp). You passed {type(timestamp)}."
        )
        raise ValueError
    t0 = train_time.timestamp()
    data_path = f"{dt.date.fromtimestamp(t0).isoformat()}-{str(int(t0))}"
    return data_path


def proc_time(start, end):
    duration = np.round((end - start), 2)
    proc_time = np.round((duration / 60), 2)
    if duration > 3600:
        return f"{np.round((proc_time / 60), 2)} hours."
    elif duration > 60:
        return f"{proc_time} minutes."
    else:
        return f"{duration} seconds."


def get_keys(items):
    keys = set([])
    for item in items:
        keys = keys.union(set(item.keys()))
    return keys


def make_fxp(attr):
    """
    Generates filter expression based on attributes dict to retrieve a subset of the database using conditional operators and keyword pairs. Returns dict containing filter expression which can be passed into the dynamodb table.scan() method.
    Args:
    `name` : one of db column names ('timestamp', 'mem_bin', etc.)
    `method`: begins_with, between, eq, gt, gte, lt, lte
    `value`: str, int, float or low/high list of values if using 'between' method
    Ex: to retrieve a subset of data with 'timestamp' col greater than 1620740441:
    setting attr={'name':'timestamp', 'method': 'gt', 'value': 1620740441}
    returns dict: {'FilterExpression': Attr('timestamp').gt(0)}
    """
    # table.scan(FilterExpression=Attr('mem_bin').gt(2))
    n = attr["name"]
    m = attr["method"]

    if attr["type"] == "int":
        v = [int(a.strip()) for a in attr["value"].split(",")]
    elif attr["type"] == "float":
        v = [float(a.strip()) for a in attr["value"].split(",")]
    else:
        v = [str(a.strip()) for a in attr["value"].split(",")]

    print(f"DDB Subset: {n} - {m} - {v}")

    if m == "eq":
        fxp = Attr(n).eq(v[0])
    elif m == "gt":
        fxp = Attr(n).gt(v[0])
    elif m == "gte":
        fxp = Attr(n).gte(v[0])
    elif m == "lt":
        fxp = Attr(n).lt(v[0])
    elif m == "lte":
        fxp = Attr(n).lte(v[0])
    elif m == "begins_with":
        fxp = Attr(n).begins_with(v[0])
    elif m == "between":
        fxp = Attr(n).between(np.min(v), np.max(v))

    return {"FilterExpression": fxp}


def ddb_download(table_name, attr=None):
    """retrieves data from dynamodb
    Args:
    table_name: dynamodb table name
    p_key: (default is 'ipst') primary key in dynamodb table
    attr: (optional) retrieve a subset using an attribute dictionary
    If attr is none, returns all items in database.
    """
    table = dynamodb.Table(table_name)
    key_set = ["ipst"]  # primary key
    if attr:
        scan_kwargs = make_fxp(attr)
        raw_data = table.scan(**scan_kwargs)
    else:
        raw_data = table.scan()
    if raw_data is None:
        return None
    items = raw_data["Items"]
    fieldnames = set([]).union(get_keys(items))

    while raw_data.get("LastEvaluatedKey"):
        print("Downloading ", end="")
        if attr:
            raw_data = table.scan(ExclusiveStartKey=raw_data["LastEvaluatedKey"], **scan_kwargs)
        else:
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

def save_json(data, name):
    with open(name, "w") as fp:
        json.dump(data, fp)
    print(f"\nJSON file saved:\n {os.path.abspath(name)}")


def save_dataframe(df, df_key):
    df["ipst"] = df.index
    df.to_csv(df_key, index=False)
    print(f"Dataframe saved as: {df_key}")
    df.set_index("ipst", drop=True, inplace=True)


def save_to_pickle(data_dict, target_col=None, df_key=None):
    keys = []
    for k, v in data_dict.items():
        if target_col is not None:
            os.makedirs(f"{target_col}", exist_ok=True)
            key = f"{target_col}/{k}"
        else:
            key = k
        with open(key, "wb") as file_pi:
            pickle.dump(v, file_pi)
            print(f"{k} saved as {key}")
            keys.append(key)
    if df_key is not None:
        keys.append(df_key)
    print(f"File keys:\n {keys}")
    return keys


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


def format_row_item(row):
    row["timestamp"] = int(row["timestamp"])
    row["x_files"] = float(row["x_files"])
    row["x_size"] = float(row["x_size"])
    row["bin_pred"] = float(row["bin_pred"])
    row["mem_pred"] = float(row["mem_pred"])
    row["wall_pred"] = float(row["wall_pred"])
    row["wc_mean"] = float(row["wc_mean"])
    row["wc_std"] = float(row["wc_std"])
    row["wc_err"] = float(row["wc_err"])
    return json.loads(json.dumps(row, allow_nan=True), parse_int=Decimal, parse_float=Decimal)


def write_to_dynamo(rows, table_name):
    try:
        table = dynamodb.Table(table_name)
    except Exception as e:
        print("Error loading DynamoDB table. Check if table was created correctly and environment variable.")
        print(e)
    try:
        print("Writing batch to DDB...")
        with table.batch_writer() as batch:
            for i in range(len(rows)):
                batch.put_item(Item=rows[i])
    except Exception as e:
        print("Error executing batch_writer")
        print(e)


def batch_ddb_writer(key, table_name):
    input_file = csv.DictReader(open(key))

    batch_size = 100
    batch = []

    for row in input_file:
        item = format_row_item(row)

        if len(batch) >= batch_size:
            write_to_dynamo(batch, table_name)
            batch.clear()
            print("Batch uploaded.")

        batch.append(item)
    if batch:
        write_to_dynamo(batch, table_name)
    return {"statusCode": 200, "body": json.dumps("Uploaded to DynamoDB Table")}
