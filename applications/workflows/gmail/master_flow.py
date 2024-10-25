from common import *

from prefect import flow, task, variables
from prefect.task_runners import ConcurrentTaskRunner
from load_messages import get_messages, gather_msg_ids

@task
def create_table():
    with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute("CREATE schema if not exists raw;")
        cur.execute("CREATE TABLE if not exists raw.emails(message_id varchar PRIMARY KEY NOT NULL,data jsonb);")

@flow(log_prints=True, task_runner=ConcurrentTaskRunner)
def gmail_master():
    create_table()
    service = build_google_service("gmail")
    gather_msg_ids(service)
    get_messages(service)


if __name__ == "__main__":
    gmail_master.serve(name="gmail-master", cron="0 */6 * * *")
