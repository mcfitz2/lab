import requests
import os
from peewee import *
from pymongo import MongoClient
import datetime
import psycopg2
import pprint
from common import *
from prefect import flow, task, variables
from prefect.task_runners import ConcurrentTaskRunner

@flow(log_prints=True, task_runner=ConcurrentTaskRunner)
def geocode_timeline():
    with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT latitude, longitude FROM datasets.timeline where country is null and latitude is not null and longitude is not null limit 50000") 
        records = cur.fetchall()
        for latitude, longitude in records:
            r = requests.get("http://192.168.1.201:8080/reverse", params={"lat":latitude, "lon":longitude})
            print(latitude, longitude, r.status_code)
            if r.status_code == 200:
                result = r.json().get('address')
                if not result:
                    print("No address found")
                    pprint.pprint(r.json()) 
                    continue
                cur.execute(f'update datasets.timeline set house_number=%(house_number)s, street=%(street)s, city=%(city)s, zip_code=%(zip_code)s, county=%(county)s, state=%(state)s, country=%(country)s where latitude = %(latitude)s and longitude = %(longitude)s', {
                    "house_number":result.get('house_number'),
                    "street":result.get('road'),
                    "city":result.get('city'),
                    "zip_code":result.get('postcode'),
                    "county":result.get("county"),
                    "state":result.get("state"),
                    "country":result.get("country"),
                    "latitude":latitude,
                    "longitude":longitude
                })
                print("committing changes")
                conn.commit()
@flow(log_prints=True)
def fix_country_names():
    
    mapping = {
        'Mauritius / Maurice': 'Mauritius',
        'Österreich': 'Austria',
        'Deutschland': 'Germany',
        'España': 'Spain'
    }
    
    with connect_to_db() as conn:
        cur = conn.cursor()
        for bad, good in mapping.items():
            cur.execute("update datasets.timeline set country = %s where country = %s", (good, bad))
        conn.commit()
              
@flow(log_prints=True)
def geocoding_master():
    fix_country_names()
    geocode_timeline()

if __name__ == "__main__":
    geocoding_master.serve(name="geocoding-master", cron="0 */6 * * *")