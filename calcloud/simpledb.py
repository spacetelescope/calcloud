"""This module handles initializing and using the calcloud job database
which tracks metadata like memory consumption and compute duration.
"""
import sys
import csv

import boto3

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
            converted = tuple(convert(v) for v in row)
            item_dict = dict(zip(columns, converted))
            item_dict.pop('', None)
            db_dict[item_dict[item_key]] = item_dict
    return db_dict


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


class SimpleDB:
    """Handle sdb API calls."""

    def __init__(self, domain_name):
        """Create an access API for the simple db named `domain_name`."""
        self.domain_name = domain_name
        self.client = boto3.client("sdb")

    @classmethod
    def list_dbs(self):
        """Return up to the first 100 names of all simple dbs in this account."""
        client = boto3.client("sdb")
        resp = client.list_domains()
        return resp["DomainNames"]

    def create_db(self):
        """Make a new simpledb corresponding to `self.domain_name`."""
        self.client.create_domain(DomainName=self.domain_name)

    def init_db(self, db_dict):
        """Initialize the simpledb using database dictionary `db_dict` of the form:

        { item_name: item_dict, ...}

        where e.g. item_name == "i9zf11010"  and item_dict == {"imageSize":2048, "jobDuration": 4398.4, ...}

        Returns None
        """
        for i, (id_name, row_dict) in enumerate(db_dict.items()):
            if i % 1000 == 0:
                sys.stdout.write(".")
                sys.stdout.flush()
            self.put_attrs(id_name, row_dict)

    def get_attrs(self, item_name, attr_names=[], consistent_read=False):
        """Fetch attributes `attr_names` for single entry `item_name`.

        item_name:  str             e.g.  name of dataset 'i9zf11010'
        attr_names:  [ str, ...]    attribute names of item to fetch
        consistent_read             use True to require consistent replications before fetching

        Values returned from sdb are type converted to the most restrictive
        type:  int, float, or str.

        returns { attr_name1: value1, attr_name2: value2, ...}
        """
        resp = self.client.get_attributes(
            DomainName=self.domain_name,
            ItemName=item_name,
            AttributeNames=attr_names,
            ConsistentRead=consistent_read,
        )
        return {attr["Name"]: convert(attr["Value"]) for attr in resp["Attributes"]}

    def put_attrs(self, item_name, attr_dict):
        """Set the attributes of `item_name` defined in `attr_dict` to the given values.

        item_name:    str     name of the database record (e.g. dataset)
        attr_dict:    dict    dictionary of attributes with values of types int, float, str only.

        Attributes are always replaced.
        All values are converted to strings for storage in sdb.

        Returns None
        """
        attr_list = []
        for item in attr_dict.items():
            attr_list.append({"Name": item[0], "Value": str(item[1]), "Replace": True})
        self.client.put_attributes(
            DomainName=self.domain_name, ItemName=item_name, Attributes=attr_list
        )

    def del_item(self, item_name):
        self.client.delete_attributes(self.domain_name, item_name)

    def del_db(self):
        self.client.delete_domain(self.domain_name)

    def get_metadata(self):
        return self.client.domain_metadata(self.domain_name)

    def select(self, what="*", where=None, consistent_read=False):
        """Query the simple db using simple SQL which is formatted like:

        SELECT {what} FROM {self.domain_name} WHERE {where}

        and yield tuples of the form:

            (('Name', name), (attr_name1, attr_val1), (attr_name2, attr_val2), ...)

        If `where` is None,  the WHERE clause is omitted entirely.

        See https://docs.aws.amazon.com/AmazonSimpleDB/latest/DeveloperGuide/SimpleQueriesSelect.html
        """
        query = f"SELECT {what} FROM `{self.domain_name}`"
        if where is not None:
            query += f" WHERE {where}"
        paginator = self.client.get_paginator('select')
        response_iterator = paginator.paginate(
            SelectExpression=query,
            ConsistentRead=consistent_read,
        )
        for resp in response_iterator:
            for item in resp["Items"]:
                yield (('Name', item["Name"]),) + \
                    tuple((attr["Name"], convert(attr["Value"])) for attr in item["Attributes"])
