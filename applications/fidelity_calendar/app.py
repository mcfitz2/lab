from ics import Calendar, Event
from flask import Flask
import yaml
import requests
import time
import pprint
import datetime
last_price_fetch = None
last_price = None

def get_avgo_price():
    global last_price_fetch
    global last_price
    if not last_price_fetch or (time.time() - last_price_fetch) > 60*60*24:
         print("Fetching price of AVGO")
         r = requests.get("https://api.polygon.io/v2/aggs/ticker/AVGO/prev", params={"adjusted":"true", "apiKey":""})
         last_price_fetch = time.time()
         last_price = float(r.json()['results'][0]['c'])
         print(f"Got price of AVGO at {last_price}")
app = Flask(__name__)

@app.get("/fidelity.ics")
def generate_calendar():
    global last_price_fetch
    global last_price
    print("Got request for calendar")
    with open("vests.yaml", "r") as stream:
        try:
            vests = yaml.safe_load(stream)
            c = Calendar()
            get_avgo_price()
            totals = {}
            total_value = {}
            for vest in vests['vests']:
                shares = float(vest['units'])
                if not totals.get(vest['date']):
                    totals[vest['date']] = {'shares':0, 'value':0}
                totals[vest['date']]['shares'] += shares
                e = Event()
                value = shares * last_price
                totals[vest['date']]['value'] += value
                e.name = f"{shares} shares; ${value:,}"
                e.begin = vest['date']
                e.make_all_day()
                c.events.add(e)
            pprint.pprint(totals)
            for date, values in totals.items():
                e = Event()
                shares = values['shares']
                value = values['value']
                after_tax = value * (1-vests['tax_rate'])
                e.name = f"Total: {shares} shares; ${value:,} ${after_tax:,}"
                e.description = f"Total: {shares} shares; ${value:,}\n After Tax: ${after_tax:,}\n Price Fetched At: {datetime.datetime.fromtimestamp(last_price_fetch)}\n Calendar Accessed At: {datetime.datetime.now()}"
                e.begin = date
                e.make_all_day()
                c.events.add(e)
            return c.serialize() 
        except yaml.YAMLError as exc:
            print(exc)





if __name__ == '__main__':

    # run() method of Flask class runs the application 
    # on the local development server.
    app.run(port=8989, host='0.0.0.0')
