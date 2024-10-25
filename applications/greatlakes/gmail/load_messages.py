import pprint
from common import *
import imaplib

from prefect import flow, task, variables
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
from prefect.task_runners import ConcurrentTaskRunner


@task(retries=5, retry_delay_seconds=5, tags=["db_insert"])
def insert_message(service, message_id):
    try:
        msg = service.users().messages().get(userId="me", id=message_id).execute()
        with connect_to_db() as conn:
            cur = conn.cursor()
            print('inserting message', msg['id'])
            cur.execute("update raw.emails set data=%s where message_id=%s;",
                        (json.dumps(msg), msg['id']))
            conn.commit()
    except HttpError as e:
        print(e.error_details)
        for detail in e.error_details:
            if detail.get('reason') and detail['reason'] == 'notFound':
                with connect_to_db() as conn:
                    cur = conn.cursor()
                    print(f"Deleting msg ID {message_id}")
                    cur.execute("delete from raw.emails where message_id=%s;", (message_id,))
                    conn.commit()
                break


@task(retries=5, retry_delay_seconds=5, tags=["db_insert"])
def insert_message_id(msg_ids):
    with connect_to_db() as conn:
        cur = conn.cursor()
        for msg_id in msg_ids:
            print('inserting message id', msg_id)
            cur.execute("INSERT INTO raw.emails(message_id) VALUES (%s) on conflict do nothing;", (msg_id,))
            conn.commit()


@flow(log_prints=True, task_runner=ConcurrentTaskRunner)
def get_messages(service):
    with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute('select message_id from raw.emails where data is null')
        for row in cur.fetchall():
            insert_message(service, row[0])


@flow(log_prints=True, task_runner=ConcurrentTaskRunner)
def gather_msg_ids(service):
    msg_list_params = {
        'userId': 'me',
        'q': 'newer: 100d',
        'includeSpamTrash': True
    }
    message_list_api = service.users().messages()
    message_list_req = message_list_api.list(**msg_list_params)
    while message_list_req is not None:
        gmail_msg_list = message_list_req.execute()
        if gmail_msg_list.get('messages'):
            insert_message_id.submit([gmail_message['id'] for gmail_message in gmail_msg_list['messages']])
            message_list_req = message_list_api.list_next(message_list_req, gmail_msg_list)
        else:
            message_list_req = None
       