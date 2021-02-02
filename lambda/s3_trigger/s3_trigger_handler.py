def lambda_handler(event, context):
    import os
    from calcloud import lambda_submit
    print(event)

    # events should only enter this lambda if their prefix is correct in s3
    # so we don't need any message validation here. In theory
    message = event['Records'][0]['s3']['object']['key']
    ipst = message.split('-')[-1]
    print(message)

    ipst_file = f'/tmp/{ipst}.txt'
    with open(ipst_file, 'w') as f:
        f.write(f"{ipst}\n")

    lambda_submit.main(ipst_file)
    # print(f"submit {ipst_file} here")

    os.remove(ipst_file)

    return None