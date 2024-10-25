

from prefect import flow, task, variables
from prefect.blocks.system import Secret
import requests
import json
import psycopg2
import requests


def connect_to_db():
    print("Connecting to DB")
    user = Secret.load("greatlakes-user").get()
    password = Secret.load("greatlakes-password").get()
    psql = psycopg2.connect(database=variables.get("greatlakes_db"), host=variables.get("greatlakes_host"),
                            port=int(variables.get("greatlakes_port")), user=user, password=password)
    return psql
@task
def create_neighborhoods_table():
    with connect_to_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE if not exists house_search.neighborhoods
                        (
                            primary_name character varying NOT NULL,
                            secondary_name character varying,
                            geom geography(MultiPolygonZ,4326),
                            PRIMARY KEY (primary_name)
                        );''')

@task
def load_neighborhoods():
    URL = "https://data.cityofchicago.org/resource/y6yq-dbs2.json"
    r = requests.get(URL, headers={"X-App-Token": Secret.load('chicago-data-app-token').get()})
    with connect_to_db() as conn:
        cursor = conn.cursor()
        for neighborhood in r.json():
            cursor.execute("INSERT INTO house_search.neighborhoods ( primary_name, secondary_name, geom ) VALUES (%s, %s, ST_Force3D(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))) on conflict do nothing;", (neighborhood['pri_neigh'], neighborhood['sec_neigh'], json.dumps(neighborhood['the_geom'])))
@task
def create_crimes_table():
    with connect_to_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE if not exists house_search.crimes (
                            "id" bigint primary key,
                            "case_number" varchar,
                            "date" timestamp,
                            "block" varchar,
                            "iucr" varchar,
                            "primary_type" varchar,
                            "description" varchar,
                            "location_description" varchar,
                            "arrest" boolean,
                            "domestic" boolean,
                            "beat" varchar,
                            "district" varchar,
                            "ward" varchar,
                            "community_area" varchar,
                            "fbi_code" varchar,
                            "year" bigint,
                            "updated_on" timestamp,
                            "latitude" numeric,
                            "longitude" numeric,
                            "geom" geography
                        );''')

@task
def load_crimes(full=False):
    URL = "https://data.cityofchicago.org/resource/crimes.json"
    offset = 0
    limit = 1000
    with connect_to_db() as conn:
        cursor = conn.cursor()
        while True:
            r = requests.get(URL, headers={"X-App-Token": Secret.load('chicago-data-app-token').get()}, params={"$offset":offset, "$limit":limit})
            if r.status_code != 200:
                print(r.status_code, r.content)
                return
            crimes = r.json()
            if len(crimes) == 0 or (not full and offset > 20000): return
            print(offset, limit, "first crime", crimes[0]['id'], crimes[0]['date'])
            for crime in crimes:
                if int(crime['year']) < 2024:
                    return
                for key in ['latitude', 'longitude', 'location_description', 'description', 'ward']:
                    crime[key] = crime.get(key, None)
                cursor.execute("""INSERT INTO house_search.crimes (
                                                                    id,
                                                                    case_number,
                                                                    date,
                                                                    block,
                                                                    iucr,
                                                                    primary_type,
                                                                    description,
                                                                    location_description,
                                                                    arrest,
                                                                    domestic,
                                                                    beat,
                                                                    district,
                                                                    ward,
                                                                    community_area,
                                                                    fbi_code,
                                                                    year,
                                                                    updated_on,
                                                                    latitude,
                                                                    longitude, 
                                                                    geom) VALUES (
                                                                        %(id)s,
                                                                        %(case_number)s,
                                                                        %(date)s,
                                                                        %(block)s,
                                                                        %(iucr)s,
                                                                        %(primary_type)s,
                                                                        %(description)s,
                                                                        %(location_description)s,
                                                                        %(arrest)s,
                                                                        %(domestic)s,
                                                                        %(beat)s,
                                                                        %(district)s,
                                                                        %(ward)s,
                                                                        %(community_area)s,
                                                                        %(fbi_code)s,
                                                                        %(year)s,
                                                                        %(updated_on)s,
                                                                        %(latitude)s,
                                                                        %(longitude)s, 
                                                                        ST_SetSRID(ST_MakePoint(%(longitude)s, %(latitude)s), 4326)) on conflict do nothing;""", crime)
            conn.commit()
            offset = offset + limit
    
    
    
    

        
def lines_served(stop):
    mapping = {
        "red": 'Red',
        "blue": 'Blue',
        "g": 'Green',
        "brn": 'Brown',
        "p": 'Purple',
        "pexp": 'Purple Express',
        "y": 'Yellow',
        "pnk": 'Pink',
        "o": 'Orange'
    }
    return [mapping[key] for key, value in stop.items() if key in mapping.keys() and value]
                        
    
@task
def create_l_stops_table():
    with connect_to_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE if not exists house_search.l_stops
                        (
                            stop_id integer,
                            direction_id character varying,
                            stop_name character varying,
                            station_name character varying,
                            station_descriptive_name character varying,
                            map_id bigint,
                            ada boolean,
                            lines character varying[],
                            location geography
                        );''')
@task
def load_l_stops():
    URL = "https://data.cityofchicago.org/resource/8pix-ypme.json"
    r = requests.get(URL, headers={"X-App-Token": Secret.load('chicago-data-app-token').get()})
    with connect_to_db() as conn:
        cursor = conn.cursor()
        for l_stop in r.json():
            cursor.execute("INSERT INTO house_search.l_stops ( stop_id, direction_id, stop_name, station_name, station_descriptive_name, map_id, ada, lines, location) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) on conflict do nothing;", (l_stop['stop_id'], l_stop['direction_id'], l_stop['stop_name'], l_stop['station_name'], l_stop['station_descriptive_name'], l_stop['map_id'], l_stop['ada'], lines_served(l_stop), l_stop['location']['longitude'], l_stop['location']['latitude']))

@flow(log_prints=True)
def ingest_neighborhoods():
    create_neighborhoods_table()
    load_neighborhoods()
@flow(log_prints=True)
def ingest_l_stops():
    create_l_stops_table()
    load_l_stops()
@flow(log_prints=True)
def ingest_crimes():
    create_crimes_table()
    load_crimes()
@flow(log_prints=True)
def ingest_master():    
    ingest_crimes()
    ingest_neighborhoods()
    ingest_l_stops()
if __name__ == "__main__":
    ingest_master.serve(name="house-search-ingest-master", cron="0 * * * *")
