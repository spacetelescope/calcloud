import boto3
import time
import sys
from datetime import datetime
  
client = boto3.client('logs')

log_group = sys.argv[1]
log_stream = sys.argv[2]

pushed_lines = []

while True:
    response = client.describe_log_streams(
        logGroupName=log_group,
        logStreamNamePrefix=log_stream
    )
    try:
        nextToken = response['logStreams'][0]['uploadSequenceToken']
    except KeyError:
        nextToken = None
    with open("/var/log/user-data.log", 'r') as f:
        lines = f.readlines()
        new_lines = []
        for line in lines:
            if line in pushed_lines:
                continue
            timestamp = line.split(" ")[0].strip()
            try:
                dt = datetime.strptime(timestamp, "%Y-%m-%dT%H.%M.%S%z")
                dt_ts = int(dt.timestamp())*1000 #milliseconds
                if nextToken is None:
                    response = client.put_log_events(
                        logGroupName = log_group,
                        logStreamName = log_stream,
                        logEvents = [
                            {
                                'timestamp': dt_ts,
                                'message': line
                            }
                        ]
                    )
                    nextToken = response['nextSequenceToken']
                else:
                    response = client.put_log_events(
                        logGroupName = log_group,
                        logStreamName = log_stream,
                        logEvents = [
                            {
                                'timestamp': dt_ts,
                                'message': line
                            }
                        ],
                        sequenceToken=nextToken
                    )
                    nextToken = response['nextSequenceToken']
            except Exception as e:
                # print(e)
                continue

            pushed_lines.append(line)
            time.sleep(0.21) #AWS throttles at 5 calls/second
    time.sleep(2)