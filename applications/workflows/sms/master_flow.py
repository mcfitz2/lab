import dropbox
import xmltodict
import logging
import datetime
import json
import pprint
import re
import xml

from prefect import task, flow

from common import *

log = logging.getLogger(__name__)

@task
def create_table():
    with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute("CREATE schema if not exists raw;")
        cur.execute("CREATE TABLE if not exists raw.sms(timestamp timestamp PRIMARY KEY NOT NULL,data jsonb NOT NULL);")

@task
def find_sms_exports_in_dropbox():
    dbx = get_dropbox_client()
    all_files = []  # collects all files here
    has_more_files = True  # because we haven't queried yet
    cursor = None  # because we haven't queried yet

    while has_more_files:
        if cursor is None:  # if it is our first time querying
            result = dbx.files_list_folder('/Apps/SMSBackupRestore')
        else:
            result = dbx.files_list_folder_continue(cursor)
        all_files.extend(result.entries)
        cursor = result.cursor
        has_more_files = result.has_more
    return [f.path_display for f in all_files if re.match(r'.+/sms-\d{14}.xml', f.path_display)]
@task
def handle_sms(local_file):
    with connect_to_db() as conn:
        cur = conn.cursor()
        with open(local_file, 'rb') as f:
            try:
                o = xmltodict.parse(f)
                if o['smses'].get('mms') and type(o['smses']['mms']) == list:
                    for sms in o['smses']['mms']:
                        sms['message_type'] = "mms"
                        timestamp = datetime.datetime.fromtimestamp(float(sms['@date'])/1000)
                        print(f"Inserting sms from {timestamp}")
                        cur.execute("INSERT INTO raw.sms(timestamp, data) VALUES (%s, %s) on conflict do nothing;", (timestamp, json.dumps(sms)))
                elif o['smses'].get('mms') and type(o['smses']['mms']) != list:
                    sms = o['smses']['mms']
                    sms['message_type'] = "mms"
                    timestamp = datetime.datetime.fromtimestamp(float(sms['@date'])/1000)
                    print(f"Inserting sms from {timestamp}")
                    cur.execute("INSERT INTO raw.sms(timestamp, data) VALUES (%s, %s) on conflict do nothing;", (timestamp, json.dumps(sms)))
                if o['smses'].get('sms') and type(o['smses']['sms']) == list:
                    for sms in o['smses']['sms']:
                        sms['message_type'] = "sms"
                        timestamp = datetime.datetime.fromtimestamp(float(sms['@date'])/1000)
                        print(f"Inserting sms from {timestamp}")
                        cur.execute("INSERT INTO raw.sms(timestamp, data) VALUES (%s, %s) on conflict do nothing;", (timestamp, json.dumps(sms)))
                elif o['smses'].get('sms') and type(o['smses']['sms']) != list:
                    sms = o['smses']['sms']
                    sms['message_type'] = "sms"
                    timestamp = datetime.datetime.fromtimestamp(float(sms['@date'])/1000)
                    print(f"Inserting sms from {timestamp}")
                    cur.execute("INSERT INTO raw.sms(timestamp, data) VALUES (%s, %s) on conflict do nothing;", (timestamp, json.dumps(sms)))
            except xml.parsers.expat.ExpatError:
                print(f"Failed to parse {local_file}")
        conn.commit()
@flow(log_prints=True)
def sms_master():
    files = find_sms_exports_in_dropbox()

    print(f"Found {len(files)} files")
    print("Ensuring tables are present")
    create_table()
    for file in files:
        local_file = download_from_dropbox(file)
        handle_sms(local_file)
        upload_sftp_processed(local_file, 'sms')
        delete_from_dropbox(file)

if __name__ == "__main__":
    sms_master.serve(name="sms-master", cron="0 8 * * *")