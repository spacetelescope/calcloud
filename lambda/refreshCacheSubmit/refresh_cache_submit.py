def lambda_handler(event, context):
    from calcloud import common
    import boto3
    import os
    import dateutil.parser
    from collections import OrderedDict

    gateway = boto3.client("storagegateway", config=common.retry_config)

    print(event)

    event_time = event["time"]
    dt = dateutil.parser.isoparse(event_time)

    # run every time
    rapid_fileshares = OrderedDict(
        [
            ("crds", os.environ["FS_CRDS"]),
            ("messages", os.environ["FS_MESSAGES"]),
            ("outputs", os.environ["FS_OUTPUTS"]),
        ]
    )

    # ~once per hour
    # inputs is never written from the cloud
    # the only file someone may want quickly on-prem is the memModel features,
    # but that one is written on-prem so doesn't need a refresh to be visible
    infrequent_fileshares = OrderedDict(
        [
            ("inputs", os.environ["FS_INPUTS"]),
            ("control", os.environ["FS_CONTROL"]),
            ("blackboard", os.environ["FS_BLACKBOARD"]),
        ]
    )

    for fs_name in rapid_fileshares.keys():
        print(f"{'*'*10} refreshing cache for {fs_name} {'*'*10}")
        try:
            response = gateway.refresh_cache(FileShareARN=rapid_fileshares[fs_name], Recursive=True)
            print(response)
        except Exception as exc:
            print(f"refresh cache failed for {fs_name} with exception")
            print(str(exc))

    # may run twice but it's better than missing an entire hour
    if do_infrequent_refresh(dt, os.environ["CALCLOUD_ENVIRONMENT"]):
        for fs_name in infrequent_fileshares.keys():
            print(f"{'*'*10} refreshing cache for {fs_name} {'*'*10}")
            try:
                response = gateway.refresh_cache(FileShareARN=infrequent_fileshares[fs_name], Recursive=True)
                print(response)
            except Exception as exc:
                print(f"refresh cache failed for {fs_name} with exception")
                print(str(exc))


def do_infrequent_refresh(timestamp, env):
    # dev and test may require quick turnaround on runs and so are refreshed each time
    override_envs = ["-dev", "-test"]

    time_test = str(timestamp.minute)[0] in ("3")
    env_test = any([s in env for s in override_envs])

    return time_test or env_test
