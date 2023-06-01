import os
import urllib.parse
from calcloud import model_ingest
from calcloud import hst


def lambda_handler(event, context=None):
    table_name = os.environ.get("DDBTABLE", "calcloud-model-sb")
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"], encoding="utf-8"
    )  # messages/processed-iaao11ofq.trigger
    # ipst = key.split("-")[-1].split(".")[0]
    # model_ingest.ddb_ingest(ipst, bucket_name, table_name)
    dataset = "-".join(key.split("-")[1:]).split(".")[0]
    dataset_type = hst.get_dataset_type(dataset)
    if dataset_type == "ipst":
        model_ingest.ddb_ingest(dataset, bucket_name, table_name)
    else:
        # Don't do anything with HAP datasets for now
        pass
