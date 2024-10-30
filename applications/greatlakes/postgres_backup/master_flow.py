import pprint
import os
import psycopg2
import requests
from prefect import flow, task, variables
from prefect.blocks.system import Secret
import peewee
import datetime
import subprocess
from common import upload_sftp_backups
import time

@task
def backup_greatlakes():
    user = Secret.load("greatlakes-user").get()
    password = Secret.load("greatlakes-password").get()
    psql = psycopg2.connect(database=variables.get("greatlakes_db"), host=variables.get("greatlakes_host"),
                            port=int(variables.get("greatlakes_port")), user=user, password=password)
    database = variables.get('greatlakes_db')
    dest_file = f'{database}-{time.strftime("%Y%m%d-%H%M%S")}.dump' 

    backup_postgres_db(variables.get("greatlakes_host"), variables.get("greatlakes_db"), int(variables.get("greatlakes_port")), user, password, dest_file, True)
#    with open(dest_file, 'w') as f:
#        f.write("dummy")
    upload_sftp_backups(dest_file, "greatlakes_db")
    os.remove(dest_file)
def backup_postgres_db(host, database_name, port, user, password, dest_file, verbose):
    """ Backup postgres db to a file. """ 
    if verbose:
        try:
            process = subprocess.Popen(
                ['pg_dump',
                 '--dbname=postgresql://{}:{}@{}:{}/{}'.format(user, password, host, port, database_name),
                 '-Fc',
                 '-f', dest_file,
                 '-v'],
                stdout=subprocess.PIPE
            )
            output = process.communicate()[0]
            if int(process.returncode) != 0:
                print('Command failed. Return code : {}'.format(process.returncode))
                exit(1)
            return output
        except Exception as e:
            print(e)
            exit(1)
    else:

        try:
            process = subprocess.Popen(
                ['pg_dump',
                 '--dbname=postgresql://{}:{}@{}:{}/{}'.format(user, password, host, port, database_name),
                 '-f', dest_file],
                stdout=subprocess.PIPE
            )
            output = process.communicate()[0]
            if process.returncode != 0:
                print('Command failed. Return code : {}'.format(process.returncode))
                exit(1)
            return output
        except Exception as e:
            print(e)
            exit(1)

@flow(log_prints=True)
def postgres_backup_master():
    backup_greatlakes()

if __name__ == "__main__":
    postgres_backup_master.serve(name="postgres-backup-master", cron="0 7 * * *")
