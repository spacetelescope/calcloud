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

    if check_for_kill(comm, "Detected broadcast-kill on entry."):
        return

    broadcasted = comm.messages.pop(f"broadcast-{serial}")

    if len(broadcasted) > 100:
        serial1, serial2 = comm.messages.get_id(), comm.messages.get_id()
        comm.messages.put(f"broadcast-{serial1}", broadcasted[: len(broadcasted) // 2])
        comm.messages.put(f"broadcast-{serial2}", broadcasted[len(broadcasted) // 2 :])
    else:
        for i, msg in enumerate(broadcasted):
            if not i % 10:
                if check_for_kill(comm, "Detected broadcast-kill in put loop"):
                    return
            comm.messages.put(msg)


def check_for_kill(comm, message):
    """Return True IFF a broadcast-kill message has been written to S3."""
    try:
        comm.messages.get("broadcast-kill")  # 12x cheaper than listl
        print(message)
        return True
    except comm.messages.client.exceptions.NoSuchKey:
        return False
