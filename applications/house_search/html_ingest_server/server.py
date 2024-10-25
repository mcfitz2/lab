from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import requests
import os, json
import uuid
app = Flask(__name__)
CORS(app)

app.cache = {}

@app.route("/", methods=["POST"])
def preflight():
    payload_id = str(uuid.uuid4())
    app.cache[payload_id] = request.json
    print(app.cache.keys())
    body = {
        "parameters": {
            "payload": {"__prefect_kind": "json", "value": json.dumps({'payload_url': f'https://n8n.micahf.net/payloads/{payload_id}'})}
        },
        "tags": [],
        "state": {
            "type": "SCHEDULED",
            "message": "",
            "state_details": {"scheduled_time": None, "cache_expiration": None},
        },
        "empirical_policy": {
            "retries": None,
            "retry_delay": None,
            "pause_keys": [],
            "resuming": False,
        },
        "work_queue_name": None,
        "job_variables": {},
    }
    r = requests.post(
        os.environ['PREFECT_API_URL'] + "/deployments/7d2e90a3-be01-40be-b0ba-9e7069a06613/create_flow_run",
        json=body,
        headers={
            "Content-type": "application/json; charset=UTF-8",
            "Authorization": "Bearer " + os.environ['PREFECT_API_KEY'],
        },
    )
    return r.json()
@app.route('/payloads/<payload_id>', methods=["GET"])
def get_payload(payload_id):
    print(app.cache.keys())
    return jsonify(app.cache[payload_id])
@app.route('/payloads', methods=["GET"])
def get_payloads():
    return jsonify(app.cache)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9191, debug=True)
