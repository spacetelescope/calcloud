import os
import glob
from . import conftest


def test_s3_upload_download(s3_client):
    """Test s3.py functions upload_filepath(), download_filepath(), download_objects
    This test creates temporary files locally and upload to S3, then download the files from S3,
    may leave temporary files/directories in the local environment if this test fails"""
    from calcloud import s3

    bucket = conftest.BUCKET
    s3_bucket = "s3://" + bucket

    # create temporary local directory for files to upload
    current_directory = os.getcwd()

    local_upload_dir = "tmpUploadDir"
    local_upload_path = os.path.join(current_directory, local_upload_dir)

    local_download_dir = "tmpDownloadDir"
    local_download_path = os.path.join(current_directory, local_download_dir)

    s3_test_dir = "s3_test_dir"
    s3_test_path = os.path.join(s3_bucket, s3_test_dir)

    if not os.path.exists(local_upload_path):
        os.makedirs(local_upload_path)

    if not os.path.exists(local_download_path):
        os.makedirs(local_download_path)

    n_files = 5
    tmpfiles = list()
    filepaths = list()
    filecontents = list()

    for i in range(n_files):
        # create local file to upload
        tmpfile = f"tmpfile{str(i)}.txt"
        filepath = os.path.join(local_upload_path, tmpfile)
        filecontent = f"This is test S3 file number {str(i)}"

        with open(filepath, "w") as fp:
            fp.write(filecontent)

        # upload file to s3
        s3_filepath = os.path.join(s3_test_path, tmpfile)
        s3.upload_filepath(filepath, s3_filepath, client=s3_client)

        tmpfiles.append(tmpfile)
        filepaths.append(filepath)
        filecontents.append(filecontent)

    # remove temporary local upload files and directory
    for filepath in filepaths:
        os.remove(filepath)
    os.rmdir(local_upload_path)

    # download one of the tmpfiles from s3
    file_num = 0  # which file to download
    download_filepath = os.path.join(local_download_path, tmpfiles[file_num])
    s3_filepath = os.path.join(s3_test_path, tmpfiles[file_num])

    s3.download_filepath(download_filepath, s3_filepath, client=s3_client)

    with open(download_filepath, "r") as f:
        firstline = f.readline().rstrip()
        # assert that the content of the downloaded file is the same as the uploaded file
        assert firstline == filecontents[file_num]
        print(firstline)

    # remove temporary local download file and directory
    os.remove(download_filepath)

    # download entire test directory from s3
    s3.download_objects(local_download_path, s3_test_path, max_objects=1000, client=s3_client)

    downloaded_files = glob.glob(f"{local_download_path}/*")

    for downloaded_file in downloaded_files:
        # assert that each of the downloaded file names is in the list of uploaded file names
        assert downloaded_file.split("/")[-1] in tmpfiles
        os.remove(downloaded_file)

    os.rmdir(local_download_path)
