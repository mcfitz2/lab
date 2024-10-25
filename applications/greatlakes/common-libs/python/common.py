import io
import os
import pprint
import re
import shutil
import os.path
import re
import shutil
import tarfile
import dropbox
import psycopg2
import requests
import urllib3
from prefect import task, runtime, variables
from prefect.blocks.system import Secret
from prefect_aws import S3Bucket
import paramiko 
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from zipfile import ZipFile
from stat import S_ISDIR, S_ISREG
from googleapiclient.http import MediaIoBaseDownload
from stravalib.client import Client
from stravalib.util.limiter import SleepingRateLimitRule
urllib3.disable_warnings()


def connect_to_db():
    print("Connecting to DB")
    user = Secret.load("greatlakes-user").get()
    password = Secret.load("greatlakes-password").get()
    psql = psycopg2.connect(database=variables.get("greatlakes_db"), host=variables.get("greatlakes_host"),
                            port=int(variables.get("greatlakes_port")), user=user, password=password)
    return psql


def get_temp_dir():
    temp_dir_path = os.path.join(variables.get('tmp_prefix'), runtime.deployment.name, runtime.flow_run.name)
    if not os.path.exists(temp_dir_path):
        os.makedirs(temp_dir_path)
    return temp_dir_path


def strip_temp_dir(path):
    temp_dir = get_temp_dir()
    print(temp_dir, path)
    if path.startswith(temp_dir):
        return path[:len(temp_dir) + 1]
    else:
        return path


@task
def cleanup():
    shutil.rmtree(get_temp_dir())


def list_files(rootdir):
    for folder, subs, files in os.walk(rootdir):
        for filename in files:
            yield os.path.join(folder, filename)



@task(retries=5, retry_delay_seconds=30)
def delete_from_dropbox(path):
    dbx = get_dropbox_client()
    dbx.files_delete_v2(path)


@task(retries=5, retry_delay_seconds=30)
def find_files_in_dropbox(root_folder, pattern):
    dbx = get_dropbox_client()
    all_files = []  # collects all files here
    has_more_files = True  # because we haven't queried yet
    cursor = None  # because we haven't queried yet

    while has_more_files:
        if cursor is None:  # if it is our first time querying
            result = dbx.files_list_folder(root_folder)
        else:
            result = dbx.files_list_folder_continue(cursor)
        all_files.extend(result.entries)
        cursor = result.cursor
        has_more_files = result.has_more
    return [f.path_display for f in all_files if re.match(pattern, f.path_display)]

@task(retries=5, retry_delay_seconds=30)
def delete_from_drive(item):
    service = build_google_service('drive', version='v3')
    body_value = {'trashed': True}
    response = service.files().update(fileId=item['id'], body=body_value).execute()


@task(retries=5, retry_delay_seconds=30)
def find_files_in_drive(pattern):
    service = build_google_service('drive', version='v3')
    results = (
        service.files()
        .list(pageSize=200, q='trashed = false')
        .execute()
    )
    items = results.get("files", [])
    return [item for item in items if re.match(pattern, item['name'])]

def get_oauth_client():
    return OauthClient(base_url=os.environ['OAUTH_URL'])


def get_dropbox_client():
    oauth = get_oauth_client()
    oauth.refresh_token('dropbox')
    tokens = oauth.get_token('dropbox')
    dbx = dropbox.Dropbox(tokens['accessToken'])
    return dbx


@task(retries=5, retry_delay_seconds=30)
def download_from_dropbox(path):
    dbx = get_dropbox_client()
    rel_path = path[1:] if path[0] == '/' else path
    if os.path.exists(os.path.join(get_temp_dir(), rel_path)) and os.path.isdir(os.path.join(get_temp_dir(), rel_path)):
        shutil.rmtree(os.path.join(get_temp_dir(), rel_path))
    elif os.path.exists(os.path.join(get_temp_dir(), rel_path)):
        os.remove(os.path.join(get_temp_dir(), rel_path))

    if not os.path.exists(os.path.dirname(os.path.join(get_temp_dir(), rel_path))):
        os.makedirs(os.path.dirname(os.path.join(get_temp_dir(), rel_path)))
    print("Downloading file from dropbox", path, 'to', os.path.join(get_temp_dir(), rel_path))
    dbx.files_download_to_file(os.path.join(get_temp_dir(), rel_path), path)
    return os.path.join(get_temp_dir(), rel_path)

@task(retries=5, retry_delay_seconds=30)
def download_from_drive(item):
    service = build_google_service('drive', version='v3')
    drive_file = service.files().get_media(fileId=item['id'])
    
    print("Downloading file from drive", item['name'], 'to', get_temp_dir())
    with open(os.path.join(get_temp_dir(), item['name']), 'wb') as f:
        downloader = MediaIoBaseDownload(f, drive_file)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}.")

    return os.path.join(get_temp_dir(), item['name'])


class OauthClient:
    def __init__(self, base_url="http://oauth:4002"):
        self.base_url = base_url

    def get_token(self, slug):
        r = requests.get(f'{self.base_url}/auth/{slug}/token')
        return r.json()

    def refresh_token(self, slug):
        r = requests.post(f'{self.base_url}/auth/{slug}/refresh')
        return r.json()


def chunks(l, n):
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        # Create an index range for l of n items:
        yield l[i:i + n]



def create_sftp_client():
    ssh_client = paramiko.SSHClient()
    user = Secret.load("storage-user").get()
    password = Secret.load("storage-password").get()
    host = variables.get('storage_host')
    port = 22
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host, port=port, username=user, password=password)

    print('connection established successfully')
    return ssh_client


def get_remote_root():
    return variables.get('remote_root')


def mkdir_p(sftp, remote_directory):
    """Change to this directory, recursively making new folders if needed.
    Returns True if any folders were created."""
    if remote_directory == '/':
        # absolute path so change directory to root
        sftp.chdir('/')
        return
    if remote_directory == '':
        # top-level relative directory must exist
        return
    try:
        sftp.chdir(remote_directory)
    except IOError:
        dirname, basename = os.path.split(remote_directory.rstrip('/'))
        mkdir_p(sftp, dirname)
        sftp.mkdir(basename)
        sftp.chdir(basename)
        return True


def upload_sftp(local_file, relative_remote_path, ftp=None):
    if not ftp:
        ssh = create_sftp_client()
        ftp = ssh.open_sftp()
    remote_path = os.path.join(get_remote_root(), relative_remote_path, os.path.basename(local_file))
    remote_dir = os.path.dirname(remote_path)
    mkdir_p(ftp, remote_dir)
    print(f"Uploading {local_file} to {remote_dir}")
    ftp.put(local_file, os.path.basename(local_file))

def upload_sftp_dir(local_dir, relative_remote_path):
    ssh = create_sftp_client()
    ftp = ssh.open_sftp()
    print(f"Uploading directory {local_dir} to {relative_remote_path}")
    for local_file in list_files(local_dir):
        relative_path = local_file[len(local_dir)+1:]
        print(local_file, relative_remote_path, relative_path)
        upload_sftp(local_file, os.path.join(relative_remote_path, relative_path), ftp=ftp)

def upload_sftp_processed(local_file, category):
    relative_remote_path = f'processed/{category}/{runtime.flow_run.name}'
    print(f"Uploading {local_file} to {relative_remote_path}")
    upload_sftp(local_file, relative_remote_path)

def upload_sftp_backups(local_file, category):
    relative_remote_path = f'backups/{category}/{runtime.flow_run.name}'
    print(f"Uploading {local_file} to {relative_remote_path}")
    upload_sftp(local_file, relative_remote_path)

def upload_sftp_trash(local_file, category):
    relative_remote_path = f'trash/{category}/{runtime.flow_run.name}'
    print(f"Uploading {local_file} to {relative_remote_path}")
    upload_sftp(local_file, relative_remote_path)

def build_google_service(service_name, version="v1"):
    oauth_client = get_oauth_client()
    tokens = oauth_client.get_token('google')
    refresh_token = tokens['refreshToken']
    access_token = tokens['accessToken']
    creds = Credentials(access_token, refresh_token=refresh_token, token_uri='https://oauth2.googleapis.com/token',
                        client_id=Secret.load('google-client-id').get(),
                        client_secret=Secret.load('google-client-secret').get())
    creds.token = access_token
    return build(service_name, version, credentials=creds)


@task
def extract_archive(path):
    file_name, ext = os.path.splitext(path)
    if 'tgz' in ext:
        file = tarfile.open(path)
        if os.path.exists(file_name) and os.path.isdir(file_name):
            shutil.rmtree(file_name)
        file.extractall(file_name)
        file.close()
        return file_name
    elif 'zip' in ext:
        file = ZipFile(path, 'r')
        if os.path.exists(file_name) and os.path.isdir(file_name):
            shutil.rmtree(file_name)
        file.extractall(file_name)
        file.close()
        return file_name

def find_files_sftp(remote_dir, pattern):
    remote_dir = os.path.join(get_remote_root(), remote_dir)
    return find_files_sftp_helper(remote_dir, pattern)
def find_files_sftp_helper(remotedir, pattern, sftp=None):
    if not sftp:
        ssh = create_sftp_client()
        sftp = ssh.open_sftp()
    results  = []
    for entry in sftp.listdir_attr(remotedir):
        remotepath = remotedir + "/" + entry.filename
        mode = entry.st_mode
        if S_ISDIR(mode):
            results.extend(find_files_sftp_helper(remotepath, pattern, sftp=sftp))
        elif S_ISREG(mode):
            results.append(remotepath)
    return [f for f in results if re.match(pattern, f)]

def get_strava_client():
    oauth = get_oauth_client()
    tokens = oauth.refresh_token('strava')
    client = Client(access_token=tokens['accessToken'], rate_limiter=SleepingRateLimitRule('low'))
    return client



@task()
def copy_google_locations_to_dataset():
    with connect_to_db() as conn:
        cur = conn.cursor()        
        cur.execute("insert into datasets.timeline (timestamp, latitude, longitude, location_accuracy, altitude_accuracy, velocity, altitude, heading) select timestamp, (data['latitudeE7']::numeric)/10000000 as latitude, (data['longitudeE7']::numeric)/10000000 as longitude, data['accuracy']::numeric as location_accuracy, data['vertical_accuracy']::numeric as altitude_accuracy, data['velocity']::numeric as velocity, data['altitude']::numeric as altitude, data['heading']::numeric as heading from raw.takeout_location_records on conflict (timestamp) do update set latitude=EXCLUDED.latitude, longitude=EXCLUDED.longitude where timeline.latitude is null or timeline.longitude is null;")
        conn.commit()
@task()
def copy_owntracks_locations_to_dataset():
    with connect_to_db() as conn:
        cur = conn.cursor()        
        cur.execute("insert into datasets.timeline (timestamp, location_accuracy, longitude, latitude) select time as timestamp, (attributes->>'gps_accuracy')::numeric as location_accuracy, ST_X(ST_TRANSFORM(location,4674)) AS longitude, ST_Y(ST_TRANSFORM(location,4674)) AS latitude  from ltss where entity_id = 'person.micah_fitzgerald' on conflict (timestamp) do update set latitude=EXCLUDED.latitude, longitude=EXCLUDED.longitude where timeline.latitude is null or timeline.longitude is null;")
        conn.commit()        
@task()
def copy_strava_locations_to_dataset():
    with connect_to_db() as conn:
        cur = conn.cursor()        
        cur.execute('''insert into datasets.timeline (timestamp, latitude, longitude) 
                        select  timestamp, 
                                avg(latitude) as latitude, 
                                avg(longitude) as longitude from 
                                    (select distinct (a.data->>'start_date')::timestamp + jsonb_array_elements(s.data->'time'->'data')::numeric * interval '1 second' as timestamp, 
                                    (jsonb_array_elements(s.data->'latlng'->'data')->>0)::numeric as latitude, 
                                    (jsonb_array_elements(s.data->'latlng'->'data')->>1)::numeric as longitude 
                                from raw.strava_activity_streams s 
                                inner join raw.strava_activities a 
                                on s.activity_id = a.activity_id) a
                        where latitude is not null and longitude is not null
                        group by timestamp
		        on conflict (timestamp) do update set latitude=EXCLUDED.latitude, longitude=EXCLUDED.longitude where timeline.latitude is null or timeline.longitude is null;''')
        conn.commit()
