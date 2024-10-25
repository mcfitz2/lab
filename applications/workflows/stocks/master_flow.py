import pprint
import time

import psycopg2
import requests
from prefect import flow, task, variables
from prefect.blocks.system import Secret
import peewee
import datetime


def connect():
    print("Connecting to DB")
    user = Secret.load("greatlakes-user").get()
    password = Secret.load("greatlakes-password").get()
    psql = psycopg2.connect(database=variables.get("greatlakes_db"), host=variables.get("greatlakes_host"),
                            port=int(variables.get("greatlakes_port")), user=user, password=password)
    return psql


@task
def create_table():
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("CREATE schema if not exists raw;")
        cur.execute('''CREATE TABLE IF NOT EXISTS "raw".stocks (
                                                  "timestamp" timestamp with time zone,
                                                  "ticker" varchar,
                                                  "price" double precision)''')


@task
def load_database():
    stocks = ['AVGO']
    api_key = Secret.load("polygon-api-key").get()

    for stock in stocks:
        r = requests.get(f"https://api.polygon.io/v2/aggs/ticker/{stock}/prev",
                         params={"adjusted": "true", "apiKey": api_key})
        fetch = datetime.datetime.utcnow()
        price = float(r.json()['results'][0]['c'])


        with connect() as p_conn:
            cursor = p_conn.cursor()
            cursor.execute("insert into raw.stocks(timestamp, ticker, price) values (%s, %s, %s) on conflict do nothing;", (fetch, stock, price))


@flow(log_prints=True)
def stocks_master():
    create_table()
    load_database()


if __name__ == "__main__":
    stocks_master.serve(name="stocks-master", cron="0 12 * * *")
