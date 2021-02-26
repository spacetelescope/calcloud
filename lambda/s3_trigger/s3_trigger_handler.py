from calcloud import lambda_submit
from calcloud import io
from calcloud import s3


def lambda_handler(event, context):

    bucket_name, ipst = s3.parse_s3_event(event)

    comm = io.get_io_bundle(bucket_name)

    comm.xdata.delete(ipst)  # biggest difference between "placed" and "rescue"

    lambda_submit.main(comm, ipst, bucket_name)
