import os.path
import re
import shutil
import tarfile

import dropbox
import urllib3
from prefect import flow, task, variables
from prefect_aws.s3 import S3Bucket
from prefect import runtime

from common import *
urllib3.disable_warnings()




@task(retries=5, retry_delay_seconds=30)
def extract_and_re_upload_file_dropbox(file):
    file_path = download_from_dropbox(file)
    extracted_dir = extract_archive(file_path)
    upload_sftp_dir(extracted_dir, os.path.join('dumping-ground/takeout', os.path.splitext(os.path.basename(file))[0]))
    upload_sftp_processed(file_path, 'takeout')

@task(retries=5, retry_delay_seconds=30)
def extract_and_re_upload_file_drive(file):
    file_path = download_from_drive(file)
    extracted_dir = extract_archive(file_path)
    upload_sftp_dir(extracted_dir, os.path.join('dumping-ground/takeout', os.path.splitext(file['name'])[0]))
    upload_sftp_processed(file_path, 'takeout')

@flow(log_prints=True)
def extract_and_re_upload_dropbox():
    files = find_files_in_dropbox('/Apps/Google Download Your Data', '.+/takeout-.+.(tgz|zip)')
    print(files)
    for file in files:
        extract_and_re_upload_file_dropbox(file)
        delete_from_dropbox(file)
    cleanup()
@flow(log_prints=True)
def extract_and_re_upload_drive():
    files = find_files_in_drive('takeout-.+.(tgz|zip)')
    for file in files:
        extract_and_re_upload_file_drive(file)
        delete_from_drive(file)
    cleanup()

@flow(log_prints=True)
def extract_and_re_upload():
    oauth = get_oauth_client()
    oauth.refresh_token('dropbox')
    oauth.refresh_token('google')
    extract_and_re_upload_dropbox()
    extract_and_re_upload_drive()

if __name__ == "__main__":
    extract_and_re_upload.serve(name="extract_and_re_upload")
