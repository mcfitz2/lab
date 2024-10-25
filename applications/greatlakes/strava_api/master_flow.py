from dateutil import parser
import sys
from prefect import variables, flow, task
from prefect.blocks.system import Secret
import pprint
import os
import datetime
from common import *
import json
import stravalib
@flow(log_prints=True)
def create_tables():
    with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute("CREATE schema if not exists raw;")
        cur.execute("CREATE TABLE if not exists raw.strava_activities(activity_id varchar PRIMARY KEY NOT NULL, data jsonb);")
        cur.execute("CREATE TABLE if not exists raw.strava_activity_streams(activity_id varchar PRIMARY KEY NOT NULL, data jsonb);")



@flow(log_prints=True)
def get_activities():
    client = get_strava_client()
    activities = client.get_activities()
    with connect_to_db() as conn:
        cur = conn.cursor()
        for activity in activities:
            cur.execute("INSERT INTO raw.strava_activities(activity_id, data) VALUES (%s, %s) on conflict do nothing;", (activity.id, json.dumps(activity.dict(), default=str)))
            conn.commit()
        
@flow(log_prints=True)
def get_activity_streams():
    client = get_strava_client()
    activities = client.get_activities()
    with connect_to_db() as conn:
        cur = conn.cursor()
        for activity in activities:
            try:
                stream = client.get_activity_streams(activity_id=activity.id, types=['time', 'latlng', 'distance', 'altitude', 'velocity_smooth', 'heartrate', 'cadence', 'watts', 'temp', 'moving', 'grade_smooth'])
                data = {stream_type: stream_data.dict() for stream_type, stream_data in stream.items()}
                cur.execute("INSERT INTO raw.strava_activity_streams(activity_id, data) VALUES (%s, %s) on conflict do nothing;", (activity.id, json.dumps(data, default=str)))
                conn.commit()
            except stravalib.exc.ObjectNotFound:
                continue



@flow(log_prints=True)
def strava_master():
    create_tables()
    get_activities()
    get_activity_streams()
    copy_strava_locations_to_dataset()
if __name__ == "__main__":
    strava_master.serve(name="strava-master", cron="0 10 * * *")
