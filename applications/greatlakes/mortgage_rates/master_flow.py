import pprint
import csv
import psycopg2
import requests
from prefect import flow, task, variables
from prefect.blocks.system import Secret
import datetime
from io import StringIO
import json
import requests
import pprint
from common import *
from psycopg2.extensions import AsIs
@task
def create_table(suffix):
    with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute("CREATE schema if not exists raw;")
        cur.execute(f'''CREATE TABLE if not exists raw.avg_mortgage_rates_{suffix} (
                            date timestamp primary key,
                            rate numeric);
		    ''')

@task
def load_database(url, suffix):
    with connect_to_db() as conn:
        cursor = conn.cursor()

#        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
        response = requests.get(url)
        csv_data = StringIO(response.text)
        reader = csv.reader(csv_data)
        next(reader)
        for date, rate in reader:
            if rate in ['.']:
                continue
            insert_query = f"""
                INSERT INTO raw.avg_mortgage_rates_{suffix} (date, rate)
                VALUES (%s, %s)
                ON CONFLICT (date)
                DO UPDATE SET
                    rate = EXCLUDED.rate;
                """
            cursor.execute(insert_query, (date, rate))

        # Commit changes and close connection
        conn.commit()

@flow(log_prints=True)
def amr_master():
    create_table("30y_fixed")
    load_database("https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US", "30y_fixed")
    create_table("15y_fixed")
    load_database("https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE15US", "15y_fixed")
    create_table("30y_fixed_fha")
    load_database("https://fred.stlouisfed.org/graph/fredgraph.csv?id=OBMMIFHA30YF", "30y_fixed_fha")
    create_table("30y_fixed_usda")
    load_database("https://fred.stlouisfed.org/graph/fredgraph.csv?id=OBMMIUSDA30YF", "30y_fixed_usda")
    create_table("30y_fixed_fico_over_740_ltv_under_80")
    load_database("https://fred.stlouisfed.org/graph/fredgraph.csv?id=OBMMIC30YFLVLE80FGE740", "30y_fixed_fico_over_740_ltv_under_80")
    create_table("30y_fixed_fico_over_740_ltv_over_80")
    load_database("https://fred.stlouisfed.org/graph/fredgraph.csv?id=OBMMIC30YFLVGT80FGE740", "30y_fixed_fico_over_740_ltv_over_80")


if __name__ == "__main__":
    amr_master.serve(name="amr-master", cron="0 0 * * *")
#    amr_master()
