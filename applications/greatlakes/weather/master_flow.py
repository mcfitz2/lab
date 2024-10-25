import pprint

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
        cur.execute('''CREATE TABLE IF NOT EXISTS "raw".weather (
                                                  "last_updated_epoch" bigint primary key,
                                                  "last_updated" text,
                                                  "temp_c" double precision,
                                                  "temp_f" double precision,
                                                  "is_day" bigint,
                                                  "wind_mph" double precision,
                                                  "wind_kph" double precision,
                                                  "wind_degree" bigint,
                                                  "wind_dir" text,
                                                  "pressure_mb" double precision,
                                                  "pressure_in" double precision,
                                                  "precip_mm" double precision,
                                                  "precip_in" double precision,
                                                  "humidity" bigint,
                                                  "cloud" bigint,
                                                  "feelslike_c" double precision,
                                                  "feelslike_f" double precision,
                                                  "vis_km" double precision,
                                                  "vis_miles" double precision,
                                                  "uv" double precision,
                                                  "gust_mph" double precision,
                                                  "gust_kph" double precision)''')


@task
def load_database():
    weather_api_token = Secret.load("weather-api-key").get()
    r = requests.get("http://api.weatherapi.com/v1/current.json", params={'key':weather_api_token, 'q': '5400 McCandless St, Austin TX 78756'})
    current = r.json()['current']


    with connect() as p_conn:
        cursor = p_conn.cursor()

        psycopg2.extras.execute_values(cursor,
                                       "insert into raw.weather(last_updated_epoch,last_updated,temp_c,temp_f,is_day,wind_mph,wind_kph,wind_degree,wind_dir,pressure_mb,pressure_in,precip_mm,precip_in,humidity,cloud,feelslike_c,feelslike_f,vis_km,vis_miles,uv,gust_mph,gust_kph) values %s on conflict do nothing;",
                                       [current],
                                       template='(%(last_updated_epoch)s,%(last_updated)s,%(temp_c)s,%(temp_f)s,%(is_day)s,%(wind_mph)s,%(wind_kph)s,%(wind_degree)s,%(wind_dir)s,%(pressure_mb)s,%(pressure_in)s,%(precip_mm)s,%(precip_in)s,%(humidity)s,%(cloud)s,%(feelslike_c)s,%(feelslike_f)s,%(vis_km)s,%(vis_miles)s,%(uv)s,%(gust_mph)s,%(gust_kph)s)',
                                       page_size=100)


@flow(log_prints=True)
def weather_master():
    create_table()
    load_database()


if __name__ == "__main__":
    weather_master.serve(name="weather-master", cron="*/10 * * * *")
