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
        print("Creating transactions table")
        cur.execute('''CREATE TABLE IF NOT EXISTS "raw".ynab_transactions
                        (
                            id varchar PRIMARY KEY,
                            date varchar,
                            amount integer,
                            memo varchar, 
                            cleared varchar,
                            approved boolean,
                            flag_color varchar,
                            flag_name varchar,
                            account_id varchar,
                            account_name varchar,
                            payee_id varchar,
                            payee_name varchar,
                            category_id varchar,
                            category_name varchar,
                            transfer_account_id varchar,
                            transfer_transaction_id varchar,
                            matched_transaction_id varchar,
                            import_id varchar,
                            import_payee_name varchar,
                            import_payee_name_original varchar,
                            debt_transaction_type varchar,
                            deleted boolean, 
                            parent_transaction_id varchar
                        )''')
        print("Creating categories table")
        cur.execute(
            '''CREATE TABLE IF NOT EXISTS "raw".ynab_categories (id varchar,
                                                                run_id integer,
                                                                timestamp timestamp,
                                                                category_group_id varchar,
                                                                category_group_name varchar,
                                                                name varchar,
                                                                hidden boolean,
                                                                original_category_group_id varchar,
                                                                note varchar,
                                                                budgeted integer,
                                                                activity integer,
                                                                balance integer,
                                                                goal_type varchar,
                                                                goal_day varchar,
                                                                goal_cadence integer,
                                                                goal_cadence_frequency varchar,
                                                                goal_creation_month varchar,
                                                                goal_target integer,
                                                                goal_target_month varchar,
                                                                goal_percentage_complete integer,
                                                                goal_months_to_budget integer,
                                                                goal_under_funded integer,
                                                                goal_overall_funded integer,
                                                                goal_overall_left integer,
                                                                deleted boolean,
                                                                PRIMARY KEY (id, run_id));'''
        )
        print("Creating accounts table")
        cur.execute('''CREATE TABLE if not exists "raw".ynab_accounts (
                                      "id" text,
                                      "run_id" integer,
                                      "timestamp" timestamp,
                                      "name" text,
                                      "type" text,
                                      "on_budget" boolean,
                                      "closed" boolean,
                                      "note" text,
                                      "balance" bigint,
                                      "cleared_balance" bigint,
                                      "uncleared_balance" bigint,
                                      "transfer_payee_id" text,
                                      "direct_import_linked" boolean,
                                      "direct_import_in_error" boolean,
                                      "last_reconciled_at" text,
                                      "deleted" boolean,
                                      PRIMARY KEY (id, run_id));''')

        print("Creating months table")
        cur.execute('''CREATE TABLE if not exists "raw".ynab_months (
            "month" text primary key,
            "note" text,
            "income" bigint,
            "budgeted" bigint,
            "activity" bigint,
            "to_be_budgeted" bigint,
            "age_of_money" bigint,
            "deleted" boolean);''')
@task
def delete_deleted_transactions():
    with connect() as p_conn:
        cursor = p_conn.cursor()
        print("Deleting uncleared transactions")
        cursor.execute("delete from raw.ynab_transactions where cleared = 'uncleared';")
        #p_conn.commit()
@task
def process_transactions(transactions):
    for transaction in transactions:
        if len(transaction['subtransactions']) > 0:
            for s_transaction in transaction['subtransactions']:
                combined = transaction
                combined.update(s_transaction)
                combined['parent_transaction_id'] = transaction['id']
                yield combined
        else:
            transaction['parent_transaction_id'] = None
            yield transaction

@task
def get_run_id(table):
    print("Getting next run_id")
    with connect() as p_conn:
        cursor = p_conn.cursor()
        cursor.execute(f"select max(run_id) from raw.{table};")
        current_run_id = cursor.fetchone()[0] or 0
        return current_run_id + 1

@task
def process_categories(run_id, categories):
    timestamp = datetime.datetime.now()
    for group in categories:
        for category in group['categories']:
            category['run_id'] = run_id
            category['timestamp'] = timestamp
            yield category
@task
def process_accounts(run_id, accounts):
    timestamp = datetime.datetime.now()
    for account in accounts:
        account['run_id'] = run_id
        account['timestamp'] = timestamp
        yield account
@task
def load_database():
    ynab_token = Secret.load("ynab-token").get()
    headers = {"Authorization": f"Bearer {ynab_token}"}
    print("Pulling transactions from API")
    r = requests.get("https://api.ynab.com/v1/budgets/87e3e9b5-77c7-485e-918c-1855f4812f5b/transactions",
                     headers=headers)
    transactions = list(process_transactions(r.json()['data']['transactions']))
    print("Pulling categories from API")

    r = requests.get("https://api.ynab.com/v1/budgets/87e3e9b5-77c7-485e-918c-1855f4812f5b/categories",
                     headers=headers)
    categories = list(process_categories(get_run_id('ynab_categories'), r.json()['data']['category_groups']))
    print("Pulling accounts from API")

    r = requests.get("https://api.ynab.com/v1/budgets/87e3e9b5-77c7-485e-918c-1855f4812f5b/accounts",
                     headers=headers)
    accounts = list(process_accounts(get_run_id('ynab_accounts'), r.json()['data']['accounts']))
    print("Pulling months from API")

    r = requests.get("https://api.ynab.com/v1/budgets/87e3e9b5-77c7-485e-918c-1855f4812f5b/months",
                     headers=headers)
    months = list(r.json()['data']['months'])
    with connect() as p_conn:
        cursor = p_conn.cursor()
        print("Loading transactions to DB")
        psycopg2.extras.execute_values(cursor,
                                       "insert into raw.ynab_transactions(id,date,amount,memo,cleared,approved,flag_color,flag_name,account_id,account_name,payee_id,payee_name,category_id,category_name,transfer_account_id,transfer_transaction_id,matched_transaction_id,import_id,import_payee_name,import_payee_name_original,debt_transaction_type,deleted,parent_transaction_id) values %s on conflict (id) do update set date = EXCLUDED.date,amount = EXCLUDED.amount,memo = EXCLUDED.memo,cleared = EXCLUDED.cleared,approved = EXCLUDED.approved,flag_color = EXCLUDED.flag_color,flag_name = EXCLUDED.flag_name,account_id = EXCLUDED.account_id,account_name = EXCLUDED.account_name,payee_id = EXCLUDED.payee_id,payee_name = EXCLUDED.payee_name,category_id = EXCLUDED.category_id,category_name = EXCLUDED.category_name,transfer_account_id = EXCLUDED.transfer_account_id,transfer_transaction_id = EXCLUDED.transfer_transaction_id,matched_transaction_id = EXCLUDED.matched_transaction_id,import_id = EXCLUDED.import_id,import_payee_name = EXCLUDED.import_payee_name,import_payee_name_original = EXCLUDED.import_payee_name_original,debt_transaction_type = EXCLUDED.debt_transaction_type,deleted = EXCLUDED.deleted,parent_transaction_id = EXCLUDED.parent_transaction_id;",
                                       transactions,
                                       template='(%(id)s,%(date)s,%(amount)s,%(memo)s,%(cleared)s,%(approved)s,%(flag_color)s,%(flag_name)s,%(account_id)s,%(account_name)s,%(payee_id)s,%(payee_name)s,%(category_id)s,%(category_name)s,%(transfer_account_id)s,%(transfer_transaction_id)s,%(matched_transaction_id)s,%(import_id)s,%(import_payee_name)s,%(import_payee_name_original)s,%(debt_transaction_type)s,%(deleted)s,%(parent_transaction_id)s)',
                                       page_size=1)
        ids_in_ynab = [transaction['id'] for transaction in transactions]
        print(ids_in_ynab[:10])
        cursor.execute("select id from raw.ynab_transactions;")
        ids_in_db = [row[0] for row in cursor.fetchall()]
        print(ids_in_db[:10])
        deleted_in_ynab = list(set(ids_in_db).difference(ids_in_ynab))
        print("Marking these transactions as deleted")
        print(deleted_in_ynab)
        cursor.executemany("update raw.ynab_transactions set deleted = true where id = %s;", [[i] for i in deleted_in_ynab])

        print("Loading categories to DB")
        psycopg2.extras.execute_values(cursor,
                                       "insert into raw.ynab_categories(id,run_id,timestamp,category_group_id,category_group_name,name,hidden,original_category_group_id,note,budgeted,activity,balance,goal_type,goal_day,goal_cadence,goal_cadence_frequency,goal_creation_month,goal_target,goal_target_month,goal_percentage_complete,goal_months_to_budget,goal_under_funded,goal_overall_funded,goal_overall_left,deleted) values %s on conflict do nothing;",
                                       categories,
                                       template='(%(id)s,%(run_id)s,%(timestamp)s,%(category_group_id)s,%(category_group_name)s,%(name)s,%(hidden)s,%(original_category_group_id)s,%(note)s,%(budgeted)s,%(activity)s,%(balance)s,%(goal_type)s,%(goal_day)s,%(goal_cadence)s,%(goal_cadence_frequency)s,%(goal_creation_month)s,%(goal_target)s,%(goal_target_month)s,%(goal_percentage_complete)s,%(goal_months_to_budget)s,%(goal_under_funded)s,%(goal_overall_funded)s,%(goal_overall_left)s,%(deleted)s)',
                                       page_size=100)
        print("Loading accounts to DB")
        psycopg2.extras.execute_values(cursor,
                                       "insert into raw.ynab_accounts(id,run_id,timestamp,name,type,on_budget,closed,note,balance,cleared_balance,uncleared_balance,transfer_payee_id,direct_import_linked,direct_import_in_error,last_reconciled_at,deleted) values %s on conflict do nothing;",
                                       accounts,
                                       template='(%(id)s,%(run_id)s,%(timestamp)s,%(name)s,%(type)s,%(on_budget)s,%(closed)s,%(note)s,%(balance)s,%(cleared_balance)s,%(uncleared_balance)s,%(transfer_payee_id)s,%(direct_import_linked)s,%(direct_import_in_error)s,%(last_reconciled_at)s,%(deleted)s)',
                                       page_size=100)
        print("Truncating months table")
        cursor.execute('truncate table raw.ynab_months')
        print("Loading months to DB")
        psycopg2.extras.execute_values(cursor,
                                       'insert into raw.ynab_months("month","note","income","budgeted","activity","to_be_budgeted","age_of_money","deleted") values %s on conflict (month) do update set "note" = EXCLUDED.note,"income" = EXCLUDED.income,"budgeted" = EXCLUDED.budgeted,"activity" = EXCLUDED.activity,"to_be_budgeted" = EXCLUDED.to_be_budgeted,"age_of_money" = EXCLUDED.age_of_money,"deleted" = EXCLUDED.deleted;',
                                       months,
                                       template='(%(month)s,%(note)s,%(income)s,%(budgeted)s,%(activity)s,%(to_be_budgeted)s,%(age_of_money)s,%(deleted)s)',
                                       page_size=1)

#        delete_deleted_transactions()
@flow(log_prints=True)
def ynab_master():
    create_table()
    load_database()


if __name__ == "__main__":
    ynab_master.serve(name="ynab-master", cron="0 * * * *")
