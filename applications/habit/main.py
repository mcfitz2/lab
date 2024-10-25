import psycopg2
from flask import Flask, jsonify
import os

app = Flask(__name__)

def connect_to_db():
    print("Connecting to DB")
    user = os.environ['POSTGRES_USER']
    password = os.environ['POSTGRES_PASS']
    psql = psycopg2.connect(database=os.environ['POSTGRES_DB'], host=os.environ['POSTGRES_HOST'],
                            port=int(os.environ['POSTGRES_PORT']), user=user, password=password)
    return psql


@app.route('/record/<habit>', methods=["POST"])
def record(habit):
    with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute('insert into raw.habits(timestamp, habit) values (NOW(), %s)', (habit,))
        conn.commit()
    return jsonify({'message': f'Habit {habit} recorded successfully'})

@app.route('/')
def default():
    return 'Hello!'
if __name__ == "__main__":
    with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute("CREATE schema if not exists raw;")
        cur.execute("CREATE TABLE if not exists raw.habits(timestamp timestamp PRIMARY KEY NOT NULL,habit varchar NOT NULL);")
    app.run(port=8989, host='0.0.0.0')