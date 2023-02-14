from calcloud import lambda_submit
from calcloud import io
from calcloud import s3


def lambda_handler(event, context):
    bucket_name, dataset = s3.parse_s3_event(event)

    comm = io.get_io_bundle(bucket_name)

    overrides = comm.messages.get(f"placed-{dataset}")

    comm.xdata.delete(dataset)  # biggest difference between "placed" and "rescue"

    # comm.messages.delete(f"placed-{dataset}")

    lambda_submit.main(comm, dataset, bucket_name, overrides)
