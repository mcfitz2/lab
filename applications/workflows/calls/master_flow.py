import os

import dropbox
import xmltodict
import logging
import datetime
import json
import pprint
import re
import xml

from prefect import task, flow, runtime

from common import *

log = logging.getLogger(__name__)
@task
def create_table():
    with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute("CREATE schema if not exists raw;")
        cur.execute("CREATE TABLE if not exists raw.calls(timestamp timestamp PRIMARY KEY NOT NULL,data jsonb NOT NULL);")

@task
def find_call_exports_in_dropbox():
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
    return [f.path_display for f in all_files if re.match(r'.+/calls-\d{14}.xml', f.path_display)]
def handle_calls(local_file):
    with connect_to_db() as conn:
        cur = conn.cursor()
        with open(local_file, 'rb') as f:
            o = xmltodict.parse(f)
            if type(o['calls']['call']) == list:
                for call in o['calls']['call']:
                    timestamp = datetime.datetime.fromtimestamp(float(call['@date'])/1000)
                    print(f"Inserting call record from {timestamp}")
                    cur.execute("INSERT INTO raw.calls(timestamp, data) VALUES (%s, %s) on conflict do nothing;", (timestamp, json.dumps(call)))
            else:
                call = o['calls']['call']
                timestamp = datetime.datetime.fromtimestamp(float(call['@date'])/1000)
                print(f"Inserting call record from {timestamp}")
                cur.execute("INSERT INTO raw.calls(timestamp, data) VALUES (%s, %s) on conflict do nothing;", (timestamp, json.dumps(call)))
        conn.commit()

@flow(log_prints=True)
def calls_master():
    files = find_call_exports_in_dropbox()

    print(f"Found {len(files)} files")
    print("Ensuring tables are present")
    create_table()
    for file in files:
        local_file = download_from_dropbox(file)
        handle_calls(local_file)
        upload_sftp_processed(local_file, 'calls')
        delete_from_dropbox(file)

if __name__ == "__main__":
    calls_master.serve(name="calls-master", cron="0 8 * * *")
