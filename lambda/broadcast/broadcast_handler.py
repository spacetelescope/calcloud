"""The broadcaset lambda is used to process 'broadcast' messages
whose payloads deine a list of messages to send.

The purpose of the broadcast lambda is to avoid the latency of
sending thousands of messages serially.   Imagine for instance trying
to cancel 100k jobs.

For large payloads the broadcast message is first deleted and two new
broadcast messages are sent each containing half the original payload.

For small payloads,  the broadcast message iterates over the payload
and directly putting each message.
"""
from calcloud import io
from calcloud import s3


def lambda_handler(event, context):

    bucket_name, serial = s3.parse_s3_event(event)

    comm = io.get_io_bundle(bucket_name)

    broadcasted = comm.messages.pop(f"broadcast-{serial}")

    if len(broadcasted) > 100:
        serial1, serial2 = comm.messages.get_id(), comm.messages.get_id()
        comm.messages.put(f"broadcast-{serial1}", broadcasted[: len(broadcasted) // 2])
        comm.messages.put(f"broadcast-{serial2}", broadcasted[len(broadcasted) // 2 :])
    else:
        for msg in broadcasted:
            comm.messages.put(msg)
