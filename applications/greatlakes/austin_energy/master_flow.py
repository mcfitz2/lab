import dateutil
from io import StringIO
import requests
from dateutil import parser
import csv
from prefect import flow, task
from prefect import variables
from prefect.blocks.system import Secret
from common import chunks, connect_to_db

from psycopg2.extras import execute_values

@task
def create_table():
    with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute("CREATE schema if not exists raw;")
        cur.execute("CREATE TABLE if not exists raw.austinenergyreading(date timestamp PRIMARY KEY NOT NULL,acct_num varchar NOT NULL, kwh numeric not null);")

class AustinEnergy:
    def __init__(self, username, password, acct_num):
        self.s = None
        self.username = username
        self.password = password
        self.acctNum = acct_num

    def login(self):
        self.s = requests.Session()
        r = self.s.get("https://austinenergyapp.com/aware/loginToken",
                       params={"email": self.username, "password": self.password, "confirm": "",
                               "userNamespace": "Austin Energy"})
        access_token = r.json()['token']
        self.s.cookies.set("austin", access_token)

    def get_15min_data(self):
        r = self.s.get("https://austinenergyapp.com/Aware/DataDownload",
                       params={"acctNum": self.acctNum, "filename": "DataExport.0418713187.900000.csv", "format": "CSV",
                               "interval": "900000"})
        print("Retrieved CSV", r.status_code)
        f = StringIO(r.content.decode('utf8'))
        reader = csv.reader(f, delimiter=',')
        next(reader)  # skip header
        readings = list(reader)[::-1]
        print("Read %d readings" % len(readings))
        # chunk_list = list(reversed(list(chunks(readings, 10000))))
        # print("Split readings into %d chunks" % len(chunk_list))
        written = 0
        with connect_to_db() as conn:
            cur = conn.cursor()
            for reading in readings:
                # tuples = [(dateutil.parser.parse(row[0], tzinfos={"CST": -6 * 3600, "CDT": -5 * 3600}),self.acctNum, float(row[1])) for row in chunk]
                # execute_values(cur, "INSERT INTO raw.austinenergyreading(date, acct_num, kwh) VALUES %s on conflict (date) do update set kwh = EXCLUDED.kwh;", tuples)
                cur.execute("INSERT INTO raw.austinenergyreading(date, acct_num, kwh) VALUES (%s, %s, %s) on conflict (date) do update set kwh = EXCLUDED.kwh;", (dateutil.parser.parse(reading[0], tzinfos={"CST": -6 * 3600, "CDT": -5 * 3600}),self.acctNum, float(reading[1])))
                conn.commit()
                written += 1
                print("%d readings written to DB" % written)


@task(retries=2, retry_delay_seconds=30)
def download_and_import(coa_username, coa_password, coa_acct_num):
    ae = AustinEnergy(coa_username, coa_password, coa_acct_num)
    ae.login()
    ae.get_15min_data()


@flow(log_prints=True)
def austin_energy_master():
    user = Secret.load("greatlakes-user").get()
    password = Secret.load("greatlakes-password").get()
    coa_username = Secret.load("coa-username").get()
    coa_password = Secret.load("coa-password").get()
    coa_acct_num = Secret.load("coa-acct-num").get()
    download_and_import(coa_username, coa_password, coa_acct_num)


if __name__ == "__main__":
    austin_energy_master.serve(name="austin-energy-master", cron="0 5 * * *")
