def lambda_handler(event, context):
    from calcloud import common
    import boto3
    import os

    gateway = boto3.client("storagegateway", config=common.retry_config)
    # we only get two concurrent refresh cache operations, but we'll use them both to get some parallelization
    # refresh every 5 minutes via EventBridge
    refresh_1 = ["/messages/", "/inputs/", "/blackboard/"]
    refresh_2 = ["/outputs/", "/control/", "/crds_env_vars/"]

    print(event)

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
