from calcloud import lambda_submit
from calcloud import io


def lambda_handler(event, context):

    print(event)

    # events should only enter this lambda if their prefix is correct in s3
    # so we don't need any message validation here. In theory

    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    message = event["Records"][0]["s3"]["object"]["key"]
    ipst = message.split("-")[-1]
    print(bucket_name, message, ipst)

    comm = io.get_io_bundle(bucket_name)
    comm.control.delete("all-" + ipst)
    comm.messages.delete("all-" + ipst)
    comm.outputs.delete("all-" + ipst)

    lambda_submit.main(ipst)

    return None
