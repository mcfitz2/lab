import decimal
import json
import re

import ijson
from prefect import flow, task, runtime, variables
from prefect_aws import S3Bucket
from psycopg2.extras import execute_values

from common import *


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super().default(o)


@task
def find_location_files():
    return find_files_sftp('dumping-ground/takeout', '.+/takeout-.+/Takeout/Location History \(Timeline\)/Records.json')

def mk_batch(iterable, n=1):
    batch = []
    for i in iterable:
        batch.append(i)
        if len(batch) >= n:
            yield batch
            batch = []


@task
def load_raw(json_file):
    with open(json_file, 'r') as f:
        for batch in mk_batch(ijson.items(f, "locations.item"), n=50000):
            handle_record_batch(batch)


@task
def create_table():
    with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute("CREATE schema if not exists raw;")
        cur.execute(
            "CREATE TABLE if not exists raw.takeout_location_records(timestamp timestamp PRIMARY KEY NOT NULL,data jsonb NOT NULL);")


def handle_record_batch(records):
    with connect_to_db() as conn:
        cur = conn.cursor()
        filtered = filter(lambda x: x.get('timestamp'), records)
        tuples = [(record.get('timestamp'), json.dumps(record, cls=DecimalEncoder)) for record in filtered]
        execute_values(cur,
                       "INSERT INTO raw.takeout_location_records(timestamp, data) VALUES %s on conflict do nothing;",
                       tuples)
        conn.commit()
        print(f"Commited {len(tuples)}")




@flow(log_prints=True)
def load_location_history():
    files = find_location_files()
    create_table()
    for file in files:
        path = download_object(file['Key'])
        load_raw(path)
        upload_sftp_trash(path, 'location_history')
    if len(files) > 0:
        copy_google_locations_to_dataset()
    cleanup()


if __name__ == "__main__":
    load_location_history.serve(name="test")
