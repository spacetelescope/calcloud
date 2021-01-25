def lambda_handler(event, context):
    import calcloud
    from calcloud import lambda_submit
    import os
    import boto3
    
    s3_client = boto3.resource('s3')
    # bucket name will need to be env variable?
    bucket = s3_client.Bucket('calcloud-hst-pipeline-outputs-sandbox')
    
    ipst_file = '/tmp/ipppssoots.txt'
    with open(ipst_file, 'w') as f:
        for object_summary in bucket.objects.filter(Prefix="messages/placed-").limit(1000):
            ipst = object_summary.key.split('-')[-1]
            f.write(f"{ipst}\n")
        
    lambda_submit.main(ipst_file)

    return event