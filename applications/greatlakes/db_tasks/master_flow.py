import os

import dropbox
import xmltodict
import logging
import datetime
import json
import pprint
import re
import xml

from prefect import task, flow, runtime

from common import *

@task
def run_metric_query(query):
     with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute('''insert into raw.finance_metrics '''+query)

@task()
def update_geom_column():
    with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute('select timestamp from datasets.timeline where geom is null and latitude is not null and longitude is not null limit 100000')
        for row in cur.fetchall():
            cur.execute('UPDATE datasets.timeline SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326) where timestamp = %s;', row)
        conn.commit()

@flow(log_prints=True)
def db_tasks_master():
    update_geom_column()
    run_metric_query('''select 'average_mandatory_spending_over_last_year' as name, now() as timestamp, avg("Dollars Spent") as value from (select substring(t.date, 1,7) as month, sum(t.amount)/-1000.0 as "Dollars Spent" from raw.ynab_transactions t join raw.ynab_mandatory_discretionary m on m.category_id = t.category_id where m.mandatory is true and date_trunc('month', to_timestamp(t.date, 'YYYY-MM-DD')) < date_trunc('month', current_date) and to_timestamp(t.date, 'YYYY-MM-DD') > current_date - interval '365' day group by month order by month) x''')
    run_metric_query('''select 'months_of_funding_over_time' as name, now() as timestamp, a/b as value from (select (select balance/1000.0 from raw.ynab_categories where name = 'Emergency Fund' and run_id = (select max(run_id) from raw.ynab_categories)) a, (select avg("Dollars Spent") from (select substring(t.date, 1,7) as month, sum(t.amount)/-1000.0 as "Dollars Spent" from raw.ynab_transactions t join raw.ynab_mandatory_discretionary m on m.category_id = t.category_id where m.mandatory is true  and date_trunc('month', to_timestamp(t.date, 'YYYY-MM-DD')) < date_trunc('month', current_date) group by month order by month) x) b) c;''')
    run_metric_query('''select '6_month_emergency_progress' as name, now() as timestamp, b.value/a.value as value from (select avg("Dollars Spent")*6 as value from (select month, sum(t.amount)/-1000.0 as "Dollars Spent" from raw.ynab_transactions_enriched t join raw.ynab_mandatory_discretionary m on m.category_id = t.category_id where m.mandatory is true and date_trunc('month', to_timestamp(t.date, 'YYYY-MM-DD')) < date_trunc('month', current_date) group by month order by month) x) a, (select balance/1000.0 as value from raw.ynab_categories where name = 'Emergency Fund' and run_id = (select max(run_id) from raw.ynab_categories)) b;''')
    run_metric_query('''select '12_month_emergency_progress' as name, now() as timestamp, b.value/a.value as value from (select avg("Dollars Spent")*12 as value from (select month, sum(t.amount)/-1000.0 as "Dollars Spent" from raw.ynab_transactions_enriched t join raw.ynab_mandatory_discretionary m on m.category_id = t.category_id where m.mandatory is true and date_trunc('month', to_timestamp(t.date, 'YYYY-MM-DD')) < date_trunc('month', current_date) group by month order by month) x) a, (select balance/1000.0 as value from raw.ynab_categories where name = 'Emergency Fund' and run_id = (select max(run_id) from raw.ynab_categories)) b;''')
    run_metric_query('''select 'average_mandatory_spending_last_3months' as name, now() as timestamp, avg("Dollars Spent") as value from (select month, sum(t.amount)/-1000.0 as "Dollars Spent" from raw.ynab_transactions_enriched t join raw.ynab_mandatory_discretionary m on m.category_id = t.category_id where m.mandatory is true and date_trunc('month', to_timestamp(t.date, 'YYYY-MM-DD')) < date_trunc('month', current_date) and to_timestamp(t.date, 'YYYY-MM-DD') > current_date - interval '90' day group by month order by month) x;''')
    run_metric_query('''select 'average_mandatory_spending_last_6months' as name, now() as timestamp, avg("Dollars Spent") as value from (select month, sum(t.amount)/-1000.0 as "Dollars Spent" from raw.ynab_transactions_enriched t join raw.ynab_mandatory_discretionary m on m.category_id = t.category_id where m.mandatory is true and date_trunc('month', to_timestamp(t.date, 'YYYY-MM-DD')) < date_trunc('month', current_date) and to_timestamp(t.date, 'YYYY-MM-DD') > current_date - interval '180' day group by month order by month) x;''')

    copy_google_locations_to_dataset()
    copy_owntracks_locations_to_dataset()
    copy_strava_locations_to_dataset()
if __name__ == "__main__":
    db_tasks_master.serve(name="db-tasks-master", cron="30 * * * *")
