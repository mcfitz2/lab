import os.path
import re
import shutil
import tarfile
from zipfile import ZipFile

import dropbox
import urllib3
from prefect import flow, task, variables
from prefect.task_runners import ConcurrentTaskRunner
from prefect_aws.s3 import S3Bucket
from prefect import runtime

from common import *

urllib3.disable_warnings()


@task(retries=5, retry_delay_seconds=30)
def extract_and_re_upload_file_local(file):
    file_path = download_from_dropbox(file)
    extracted_dir = extract_archive(file_path)
    upload_sftp_dir(extracted_dir, os.path.join('dumping-ground/instagram', os.path.splitext(os.path.basename(file))[0]))
    upload_sftp_processed(file_path, 'instagram')
       
@flow(task_runner=ConcurrentTaskRunner())
def extract_and_re_upload_dropbox():
    files = find_files_in_dropbox('/Apps/Meta', '.+/instagram-.+.zip')
    for file in files:
        extract_and_re_upload_file_local(file)
        delete_from_dropbox(file)
    cleanup()

@flow(log_prints=True)
def extract_and_re_upload():
    extract_and_re_upload_dropbox()

if __name__ == "__main__":
    extract_and_re_upload.serve(name="extract_and_re_upload")
