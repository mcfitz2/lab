import oauthlib
import datetime
import logging
import sys
import os
import time

from common import OauthClient
from dateutil import parser
import sys
import fitbit
from peewee import *
from prefect import variables, flow, task
from prefect.blocks.system import Secret

log = logging.getLogger(__name__)
from playhouse.postgres_ext import *
import pprint
import psycopg2
import requests
import base64
import pprint
import os
import datetime
from requests.auth import HTTPBasicAuth


data_definitions = [
    {'dataset': 'activities/steps', 'table': 'fitbitstepsseries'},
    {'dataset': 'activities/heart', 'table': 'fitbitheartseries'},
    {'dataset': 'activities/distance', 'table': 'fitbitdistanceseries'},
    {'dataset': 'activities/floors', 'table': 'fitbitfloorsseries'},
    {'dataset': 'body/bmi', 'table': 'fitbitbmiseries'},
    {'dataset': 'body/weight', 'table': 'fitbitweightseries'},
    {'dataset': 'body/fat', 'table': 'fitbitfatseries'},
    {'get_func': 'sleep', 'table': 'fitbitsleep'},
    {'get_func': 'bp', 'table': 'fitbitbp'}, {'get_func': 'activities', 'table': 'fitbitactivities'},
    {'get_func': 'foods_log_water', 'table': 'fitbitfoodslogwater'},
    {'get_func': 'foods_log', 'table': 'fitbitfoodslog'}

]


def connect():
    user = Secret.load("greatlakes-user").get()
    password = Secret.load("greatlakes-password").get()
    psql = psycopg2.connect(database=variables.get("greatlakes_db"), host=variables.get("greatlakes_host"),
                            port=int(variables.get("greatlakes_port")), user=user, password=password)
    return psql




class TokenManager(object):
    def __init__(self):
        self.oauth_client = OauthClient()
        self.client_id = Secret.load('fitbit-client-id').get()
        self.client_secret = Secret.load('fitbit-client-secret').get()
        self.load_token()

    def load_token(self):
        tokens = self.oauth_client.get_token('fitbit')
        self.refresh_token = tokens['refreshToken']
        self.access_token = tokens['accessToken']

    def get_refreshed_client(self):
        self.get_new_token()
        return self.get_client()

    def get_client(self):
        return fitbit.Fitbit(self.client_id, self.client_secret, access_token=self.access_token,
                             refresh_token=self.refresh_token)
    def get_new_token(self):
        tokens = self.oauth_client.refresh_token('fitbit')
        self.load_token()
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def buildDateList(start, end):
    delta = end - start
    return [(start + datetime.timedelta(i)).replace(hour=0, minute=0, second=0, microsecond=0).date() for i in
            range(delta.days + 1)]


@task
def missing_days(table, fb):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            f"select day from raw.{table};")
        days_in_db = [i[0] for i in cur.fetchall()]
    try:
        user = fb.user_profile_get()['user']
    except fitbit.exceptions.HTTPTooManyRequests as e:
        print(
            f"hit rate limit, retry in {e.retry_after_secs + 60} ({int(e.retry_after_secs + 60 / 60.0)} min). ({datetime.datetime.now() + datetime.timedelta(seconds=e.retry_after_secs + 60)})")
        return []
    print("getting missing days for %s" % table)
    print("days in db: %d" % (len(days_in_db)))
    join_date = parser.parse(user['memberSince'])
    days_since_joining = buildDateList(join_date, datetime.datetime.today())
    days_to_pull = sorted(list(set(days_since_joining).difference(days_in_db)))
    print("join date: %s" % join_date)
    print("days to pull: %s" % (len(days_to_pull)))
    return days_to_pull


@task
def puller(table, dl, func, fb):
    for i, d in enumerate(dl):
        if d == datetime.datetime.today().date():
            continue
        while True:
            try:
                print(f"Pulling data for {table}::{d}")
                func(d, fb)
                break
            except fitbit.exceptions.HTTPTooManyRequests as e:
                print(
                    f"hit rate limit, retry in  {e.retry_after_secs + 60} ({int(e.retry_after_secs + 60 / 60.0)} min) ({datetime.datetime.now() + datetime.timedelta(seconds=e.retry_after_secs + 60)}). {len(dl) - i} days to go")
                return
    return False


def time_series(dataset, table):
    def func(d, fb):
        data = fb.intraday_time_series(dataset, base_date=d)
        with connect() as conn:
            cur = conn.cursor()
            cur.execute(
                f"insert into raw.{table} (day, data) values (%(day)s, %(data)s) on conflict (day) do update set data = EXCLUDED.data;",
                {"day": d, "data": json.dumps(data)})
            conn.commit()

    return func


def other(get_func, table):
    def func(d, fb):
        data = getattr(fb, get_func)(d)
        with connect() as conn:
            cur = conn.cursor()
            cur.execute(
                f"insert into raw.{table} (day, data) values (%(day)s, %(data)s) on conflict (day) do update set data = EXCLUDED.data;",
                {"day": d, "data": json.dumps(data)})
            conn.commit()

    return func





@flow(log_prints=True)
def fitbit_master():
    token_manager = TokenManager()
    fb = token_manager.get_refreshed_client()

    for definition in data_definitions:
        if definition.get('dataset'):
            r = puller(definition.get('table'), missing_days(definition.get('table'), fb), time_series(definition.get('dataset'), definition.get('table')), fb)
        elif definition.get('get_func'):
            r = puller(definition.get('table'), missing_days(definition.get('table'), fb), other(definition.get('get_func'), definition.get('table')), fb)


if __name__ == "__main__":
    fitbit_master.serve(name="fitbit-master", cron="0 */6 * * *")
