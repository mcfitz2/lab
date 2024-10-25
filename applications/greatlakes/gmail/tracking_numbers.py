import base64

from prefect import flow
from prefect.task_runners import ConcurrentTaskRunner
from common import *

@flow(log_prints=True, task_runner=ConcurrentTaskRunner)
def find_tracking_numbers():
    with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute("select message_id, jsonb_array_elements(data['payload']['parts'])->'body'->>'data' from raw.emails limit 10;")
        for message_id, body in cur.fetchall():
            decoded_body = base64.urlsafe_b64decode(body + '=' * (4 - len(body) % 4))
            print(decoded_body)

if __name__ == "__main__":
    find_tracking_numbers.serve(name="find-tracking-numbers", cron="0 */6 * * *")