import shutil
import sqlite3

import dateutil
from io import StringIO

import psycopg2
import requests
from dateutil import parser
import csv
from peewee import *
from prefect import flow, task
from prefect import variables
from prefect.blocks.system import Secret
import tempfile
@task
def download_database():
    fp, path = tempfile.mkstemp()
    with requests.get("http://192.168.1.28:5000/dump/database", stream=True) as r:
        with open(path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    return path
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
        cur.execute('''CREATE TABLE IF NOT EXISTS "raw".pepboy
                        (
                            vehicle_id integer NOT NULL,
                            "time" timestamp without time zone NOT NULL,
                            fuel_level numeric,
                            rpm integer,
                            dst_since_clear numeric,
                            odometer_calibration numeric,
                            lat numeric,
                            lon numeric,
                            voltage numeric,
                            speed numeric,
                            run_time integer,
                            coolant_temp numeric,
                            CONSTRAINT pepboy_pkey PRIMARY KEY (vehicle_id, "time")
                        )''')
@task
def load_database(db_path):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("select vehicle_id, datetime(time, 'unixepoch', 'localtime'), fuel_level, rpm, dst_since_clear, odometer_calibration, lat, lon, voltage, speed from datapoint where time is not null;")

    data = cur.fetchall()
    print(data[0])
    with connect() as p_conn:
        cursor = p_conn.cursor()
        psycopg2.extras.execute_values(cursor, "insert into raw.pepboy (vehicle_id, time, fuel_level, rpm, dst_since_clear, odometer_calibration, lat, lon, voltage, speed) values %s on conflict do nothing;", data, template=None, page_size=100)


@flow(log_prints=True)
def pepboy_master():
    path = download_database()
    create_table()
    load_database(path)
if __name__ == "__main__":
    pepboy_master.serve(name="pepboy-master", cron="0 0 * * *")