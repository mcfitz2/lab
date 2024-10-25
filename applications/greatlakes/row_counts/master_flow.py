import datetime

import psycopg2
from prefect import runtime, flow, variables
from prefect.blocks.system import Secret


def connect_to_db():
    print("Connecting to DB")
    user = Secret.load("greatlakes-user").get()
    password = Secret.load("greatlakes-password").get()
    psql = psycopg2.connect(database=variables.get("greatlakes_db"), host=variables.get("greatlakes_host"),
                            port=int(variables.get("greatlakes_port")), user=user, password=password)
    return psql

@flow(log_prints=True)
def row_count_master():
    with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT table_name, table_schema FROM information_schema.tables WHERE table_schema = 'raw' or table_schema = 'datasets'")

        cur.execute(
            "SELECT table_name, table_schema FROM information_schema.tables WHERE table_schema = 'raw' or table_schema = 'datasets'")
        for table, schema in cur.fetchall():
            cur.execute(f"SELECT count(*) FROM {schema}.{table}")
            count = cur.fetchone()[0]
            print(schema, table, count, datetime.datetime.now())
            cur.execute(
                f'insert into datasets.row_counts ("schema", "table", "rows", "timestamp") values (\'{schema}\', \'{table}\', {count}, \'{datetime.datetime.now()}\')')
        conn.commit()


if __name__ == "__main__":
    row_count_master.serve(name="row-count-master", cron="*/5 * * * *")
