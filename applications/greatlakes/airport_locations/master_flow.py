import logging
import os
import re

import psycopg2
import xmltodict
import logging
import os
import shutil
import datetime
import requests
import zipfile
import os
from peewee import *
import datetime

from prefect import variables, task, flow
from prefect.blocks.system import Secret
from psycopg2.extras import execute_values


@task
def create_table():
    with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute("CREATE schema if not exists raw;")
        cur.execute("CREATE TABLE if not exists raw.airport_locations(icao_code varchar PRIMARY KEY NOT NULL, iata_code varchar, name varchar, city varchar, country varchar, altitude numeric, latitude numeric, longitude numeric);")
def connect_to_db():
    print("Connecting to DB")
    user = Secret.load("greatlakes-user").get()
    password = Secret.load("greatlakes-password").get()
    psql = psycopg2.connect(database=variables.get("greatlakes_db"), host=variables.get("greatlakes_host"),
                            port=int(variables.get("greatlakes_port")), user=user, password=password)
    return psql
@task
def import_locations():
    with open("airport_db.zip", 'wb') as zip_file:
        resp = requests.get(variables.get('airport_db_url'))
        if resp.status_code > 399:
            print(resp.status_code, resp.content)
        zip_file.write(resp.content)
    operations = []
    with zipfile.ZipFile("airport_db.zip") as zf:
        with zf.open("GlobalAirportDatabase.txt", 'r') as f:
            for line in f.readlines():
                icao_code, iata_code, name, city, country = map(lambda x: x.decode('utf-8'), line.split(b':')[0:5])
                altitude, latitude, longitude = map(float, line.split(b':')[13:16])
                location = (icao_code, iata_code, name, city, country, latitude, altitude, longitude)
                operations.append(location)

    print(f"Applying {len(operations)} changes to DB")
    with connect_to_db() as conn:
        cur = conn.cursor()
        execute_values(cur,
                       "INSERT INTO raw.airport_locations(icao_code, iata_code, name, city, country, latitude, longitude, altitude) VALUES %s on conflict do nothing;",
                       operations)

    os.remove("airport_db.zip")
@flow(log_prints=True)
def airport_locations_master():
    create_table()
    import_locations()

if __name__ == "__main__":
    airport_locations_master.serve(name="airport-locations-master")

