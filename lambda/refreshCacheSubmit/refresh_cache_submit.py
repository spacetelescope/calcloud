def lambda_handler(event, context):
    from calcloud import common
    import dateutil.parser
    import boto3
    import os

    gateway = boto3.client("storagegateway", config=common.retry_config)
    # we only get two concurrent refresh cache operations, but we'll use them both to get some parallelization
    # we want to refresh these every time
    refresh_1 = ["/messages/"]
    refresh_2 = ["/outputs/", "/blackboard/"]

    print(event)
    event_time = event["time"]
    dt = dateutil.parser.isoparse(event_time)

    if str(dt.minute)[0] in ("3", "6"):
        # these can be refreshed far less often
        refresh_1.append("/control/")
        refresh_2.append("/inputs/")

    try:
        response = gateway.refresh_cache(FileShareARN=os.environ["FILESHARE"], FolderList=refresh_1, Recursive=True)
        print(response)
    except Exception as exc:
        print(f"refresh cache failed for {refresh_1} with exception")
        print(str(exc))

    try:
        response = gateway.refresh_cache(FileShareARN=os.environ["FILESHARE"], FolderList=refresh_2, Recursive=True)
        print(response)
    except Exception as exc:
        print(f"refresh cache failed for {refresh_2} with exception")
        print(str(exc))
