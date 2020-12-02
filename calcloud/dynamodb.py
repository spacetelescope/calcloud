"""This module handles initializing and using the calcloud job database
which tracks metadata like memory consumption and compute duration.
"""
import sys

import boto3

# --------------------------------------------------------------------------------


def convert(v):
    """Type converter from str to int, float, str in that order."""
    v = v.strip()
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return str(v)
    return v


# --------------------------------------------------------------------------------


class DynamoDB:
    """Handle Dynamo API calls more naturally."""

    def __init__(self, table_name, primary_key):
        """Initialize DynamoDB w/o creating or opening actual database."""
        self.table_name = table_name
        self.primary_key = primary_key
        self.dynamodb = boto3.resource("dynamodb")
        self.table = (
            self.open_db()
        )  #  Assume it's terraform'ed already and fail if not.

        # try:
        #     self.table = self.open_db()
        # except exceptions.ResourceNotExists:
        #     print(f"Creating dynamodb '{table_name}' with primary key '{primary_key}'")
        #     self.table = self.create_db()

    def create_db(self):
        """Create a dynamodb corresponding to this object's table_name and primary_key."""
        table = self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[{"AttributeName": self.primary_key, "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": self.primary_key, "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.meta.client.get_waiter("table_exists").wait(TableName=self.table_name)
        return table

    def open_db(self):
        """Open an existing db."""
        return self.dynamodb.Table(self.table_name)

    def to_db(self, item_dict):
        """Convert the values of item_dict for storage in dynamodb."""
        return {key: str(val) for (key, val) in item_dict.items()}

    def from_db(self, item_dict):
        """Convert values coming from dynamodb back to Python types."""
        return {key: convert(val) for (key, val) in item_dict.items()}

    def put_item(self, item_dict):
        """Create a new item corresponding to `item_dict`."""
        self.table.put_item(Item=self.to_db(item_dict))

    def init_db(self, db_dict):
        """Initialize the simpledb using database dictionary `db_dict` of the form:

        db_dict   dict(dict...)   { item_name: item_dict, ...}

        where e.g. item_name == "i9zf11010" and item_dict == {'dataset':'i9zf11010', "imageSize":2048, "jobDuration": 4398.4, ...}

        Returns None
        """
        with self.table.batch_writer() as batch:
            for i, (_item_name, item_dict) in enumerate(db_dict.items()):
                if i % 1000 == 0:
                    print(i)
                    sys.stdout.flush()
                batch.put_item(self.to_db(item_dict))

    def get_item(self, item_name):
        """Fetch attribute dictionary of item with primary key value `item_name`.

        item_name:  str             e.g.  name of dataset 'i9zf11010'

        returns dict(item attributes...)
        """
        resp = self.table.get_item(Key={self.primary_key: item_name})
        try:
            return self.from_db(resp["Item"])
        except KeyError:
            raise KeyError(f"Item '{item_name}' not found.")

    def del_item(self, item_name):
        """Delete the item with primary key value `item_name`."""
        self.table.delete_item(Key={self.primary_key: item_name})

    def update_item(self, item_dict):
        """Update the item identified in `item_dict` with the values of `item_dict`."""
        self.del_item(item_dict[self.primary_key])
        self.put_item(item_dict)

    def del_db(self):
        """Delete this database destroying the persistent copy."""
        self.table.delete()
