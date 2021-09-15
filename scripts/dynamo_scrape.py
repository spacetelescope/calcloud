import argparse
import boto3
from botocore.config import Config
import csv

# mitigation of potential API rate restrictions (esp for Batch API)
retry_config = Config(retries={"max_attempts": 5})
client = boto3.client("s3", config=retry_config)
dynamodb = boto3.resource("dynamodb", config=retry_config, region_name="us-east-1")

def get_keys(items):
    keys = set([])
    for item in items:
        keys = keys.union(set(item.keys()))
    return keys


def ddb_download(table_name):
    """retrieves data from dynamodb
    Args:
    table_name: dynamodb table name
    p_key: (default is 'ipst') primary key in dynamodb table
    attr: (optional) retrieve a subset using an attribute dictionary
    If attr is none, returns all items in database.
    """
    table = dynamodb.Table(table_name)
    key_set = ["ipst"]  # primary key
    raw_data = table.scan()
    if raw_data is None:
        return None
    items = raw_data["Items"]
    fieldnames = set([]).union(get_keys(items))

    while raw_data.get("LastEvaluatedKey"):
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--table", help="ddb table", type=str)
    parser.add_argument("-k", "--key", help="output csv filename", type=str)
    args = parser.parse_args()
    if args.table:
        table_name = args.table
    else:
        table_name = 'calcloud-model-ops'
    if args.key:
        key = args.key
    else:
        key = "latest.csv"
    ddb_data = ddb_download(table_name)
    write_to_csv(ddb_data, key)
