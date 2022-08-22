import os
from . import conftest


def test_s3_mock(s3_client):

    from calcloud import s3

    bucket = conftest.BUCKET
    s3_bucket = "s3://" + bucket

    # create temporary local file to upload
    path = "./"
    tmpfile = "tmpfile.txt"
    filepath = os.path.join(path, tmpfile)
    filecontent = "This is a test S3 file"

    with open(filepath, "w") as fp:
        fp.write(filecontent)
        pass

    # upload tmpfile to s3
    s3_filepath = os.path.join(s3_bucket, tmpfile)
    s3.upload_filepath(filepath, s3_filepath, client=s3_client)

    # download tmpfile from s3, name it tmpfile_2.txt
    tmpfile2 = "tmpfile_2.txt"
    filepath2 = os.path.join(path, tmpfile2)
    s3.download_filepath(filepath2, s3_filepath, client=s3_client)
    with open(filepath2, "r") as f:
        firstline = f.readline().rstrip()
        assert (
            firstline == filecontent
        )  # assert that the content of the downloaded file is the same as the uploaded file

    # remove temporary local files
    os.remove(filepath)
    os.remove(filepath2)
