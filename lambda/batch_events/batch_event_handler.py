from calcloud import io


def lambda_handler(event, context):

    print(event)

    ipppssoot = event["detail"]["container"]["command"][1]
    bucket = event["detail"]["container"]["command"][2].split("/")[2]
    job_id = event["detail"]["jobId"]
    job_name = event["detail"]["jobName"]  # appears to be ipppssoot
    fail_reason = event["detail"]["attempts"][0]["container"]["reason"]
    exit_code = event["detail"]["attempts"][0]["container"]["exitCode"]

    comm = io.get_io_bundle(bucket)

    try:
        ctrl_msg = comm.control.get(ipppssoot)
    except comm.control.client.exceptions.NoSuchKey:
        ctrl_msg = dict()

    ctrl_msg["ipppssoot"] = ipppssoot
    ctrl_msg["bucket"] = bucket
    ctrl_msg["job_id"] = job_id
    ctrl_msg["job_name"] = job_name
    ctrl_msg["fail_reason"] = fail_reason
    ctrl_msg["exit_code"] = exit_code

    #  XXXXX Automatic rescue with increasing memory retry count
    if "memory_retries" not in ctrl_msg:
        ctrl_msg["memory_retries"] = 0
    if fail_reason.startswith("OutOfMemoryError:") and ctrl_msg["memory_retries"] < 4:
        ctrl_msg["memory_retries"] += 1
        comm.control.put(ipppssoot, ctrl_msg)  # XXXX control setup must precede rescue message
        print("Automatic rescue with retry count", ctrl_msg["memory_retries"])
        comm.messages.put("rescue-" + ipppssoot)
    else:
        comm.control.put(ipppssoot, ctrl_msg)

    print(ctrl_msg)
