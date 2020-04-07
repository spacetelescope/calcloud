import sys
import json
import datetime
import re

jobs = json.load(open(sys.argv[1]))

for job in jobs:
    try:
        if "reason" in job["container"]:
            if re.search(sys.argv[2], job["container"]["reason"]):
                print(job["jobName"])
        else:
            print(job["jobName"], file=sys.stderr)
    except Exception:
        print(f'Search failed for {job["jobName"]}', file=sys.stderr)
