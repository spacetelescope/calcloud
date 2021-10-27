import json
import boto3
import os
import argparse
import csv
from decimal import Decimal
import sys

s3 = boto3.resource("s3")
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")


def format_row_item(row):
    row["timestamp"] = int(row["timestamp"])
    row["x_files"] = float(row["x_files"])
    row["x_size"] = float(row["x_size"])
    row["drizcorr"] = int(row["drizcorr"])
    row["pctecorr"] = int(row["pctecorr"])
    row["crsplit"] = int(row["crsplit"])
    row["subarray"] = int(row["subarray"])
    row["detector"] = int(row["detector"])
    row["dtype"] = int(row["dtype"])
    row["instr"] = int(row["instr"])
    row["wallclock"] = float(row["wallclock"])
    row["memory"] = float(row["memory"])
    # row["mem_bin"] = float(row["mem_bin"])
    row["n_files"] = float(row["n_files"])
    row["total_mb"] = float(row["total_mb"])
    # row["bin_pred"] = float(row["bin_pred"])
    # row["mem_pred"] = float(row["mem_pred"])
    # row["wall_pred"] = float(row["wall_pred"])
    return json.loads(json.dumps(row, allow_nan=True), parse_int=Decimal, parse_float=Decimal)


def write_to_dynamo(rows, table_name):
    try:
        table = dynamodb.Table(table_name)
    except:
        print("Error loading DynamoDB table. Check if table was created correctly and environment variable.")
    try:
        print("Writing batch to DDB...")
        with table.batch_writer() as batch:
            for i in range(len(rows)):
                batch.put_item(Item=rows[i])
    except:
        import traceback

        traceback.print_exc()
        sys.exit()
        print("Error executing batch_writer")


def main(key, table_name):
    input_file = csv.DictReader(open(key))
    batch_size = 100
    batch = []

    for row in input_file:
        try:
            item = format_row_item(row)
        except Exception as e:
            import traceback

            traceback.print_exc()
            print(e)
            print(row)
            import sys

            sys.exit()
        if len(batch) >= batch_size:
            write_to_dynamo(batch, table_name)
            batch.clear()
            print("Batch uploaded.")

        batch.append(item)
    if batch:
        write_to_dynamo(batch, table_name)
    return {"statusCode": 200, "body": json.dumps("Uploaded to DynamoDB Table")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--table", help="ddb table", type=str)
    parser.add_argument("-k", "--key", help="local csv filepath", type=str)
    args = parser.parse_args()
    if args.table:
        table_name = args.table
    else:
        table_name = "calcloud-model-sb"
    if args.key:
        key = args.key
    else:
        key = "latest.csv"
    main(key, table_name)
