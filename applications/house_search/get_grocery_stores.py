import googlemaps
from datetime import datetime
import pprint
import psycopg2
import time

neighborhoods = [
    "Albany Park",
    "Andersonville",
    "Arcadia Terrace   ",
    "Archer Heights",
    "Ashburn",
    "Auburn Gresham",
    "Austin",
    "Avalon Park",
    "Avondale",
    "Back of the Yards",
    "Belmont Cragin",
    "Beverly",
    "Bowmanville",
    "Boystown",
    "Bridgeport",
    "Brighton Park",
    "Bronzeville",
    "Bucktown",
    "Budlong Woods",
    "Buena Park",
    "Burnside",
    "Calumet Heights",
    "Chatham",
    "Chicago Lawn",
    "Chicago Loop",
    "Chinatown",
    "Clearing",
    "Dearborn Park",
    "DePaul",
    "Douglas",
    "Dunning",
    "East Garfield Park",
    "East Side",
    "East Village",
    "Edgebrook",
    "Edgewater",
    "Edison Park",
    "Englewood",
    "Forest Glen",
    "Fuller Park",
    "Fulton Market",
    "Gage Park",
    "Garfield Ridge",
    "Gold Coast",
    "Graceland West",
    "Greater Grand Crossing",
    "Hamlin Park",
    "Harwood Heights",
    "Hegewisch",
    "Hermosa",
    "Hollywood Park",
    "Humboldt Park",
    "Hyde Park",
    "Irving Park",
    "Jefferson Park ",
    "Kenwood",
    "Kilbourn Park",
    "Lakeshore East",
    "Lakeview",
    "Lakewood Balmoral",
    "Lincoln Park",
    "Lincoln Square",
    "Little Italy",
    "Little Village",
    "Logan Square",
    "Margate Park",
    "Mayfair",
    "McKinley Park",
    "Montclare",
    "Morgan Park",
    "Mount Greenwood",
    "Near West Side",
    "Noble Square",
    "North Center",
    "North Lawndale",
    "North Mayfair",
    "North Park",
    "Norwood Park",
    "O'Hare",
    "Oakland",
    "Old Irving Park",
    "Old Town",
    "Peterson Park",
    "Peterson Woods",
    "Pilsen",
    "Portage Park",
    "Printer's Row",
    "Pullman",
    "Ravenswood",
    "Ravenswood Manor",
    "River North",
    "River West",
    "Riverdale",
    "Rogers Park",
    "Roscoe Village",
    "Roseland",
    "Sauganash",
    "Sheridan Park",
    "South Chicago",
    "South Deering",
    "South Loop",
    "South Shore",
    "Southport Corridor",
    "St. Ben's",
    "Streeterville",
    "Tri-Taylor",
    "Ukrainian Village",
    "University Village",
    "Uptown",
    "Washington Heights",
    "Washington Park",
    "West Elsdon",
    "West Englewood",
    "West Garfield Park",
    "West Lawn",
    "West Loop",
    "West Pullman",
    "West Ridge",
    "West Town",
    "Wicker Park",
    "Woodlawn",
    "Wrigleyville",
]











gmaps = googlemaps.Client(key='')

import json
def connect():
    return psycopg2.connect(database="",
                            user="",
                            password="",
                            host="", 
                            port=5432)
def create_table(table):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(f'CREATE TABLE if not exists "raw".{table} (place_id character varying NOT NULL, data jsonb NOT NULL, PRIMARY KEY (place_id));'
)
def get_stores(table, text, neighborhood):
    create_table(table)
    page_token = None
    results = gmaps.places(f"{text} in {neighborhood} chicago", location=(30.3339023,-97.7308078))
    page_token = results.get('next_page_token')
    if not page_token:
        pprint.pprint(results)
    places = []
    with connect() as conn:
        cur = conn.cursor()
        for place in results['results']:
            cur.execute(f"insert into raw.{table} (place_id, data) Values (%s, %s) on conflict do nothing;", (place['place_id'], json.dumps(place)))
    time.sleep(2)
    # for result in results['results']:
    #     places.append((result['name'], result['geometry']['location']['lat'], result['geometry']['location']['lng'], result['formatted_address']))

    while page_token:
        time.sleep(2)
        print("getting next page", page_token)
        results = gmaps.places(f"{text} in {neighborhood} chicago", location=(30.3339023,-97.7308078), page_token=page_token)
        page_token = results.get('next_page_token')       
        with connect() as conn:
            cur = conn.cursor()
            for place in results['results']:
                cur.execute(f"insert into raw.{table} (place_id, data) Values (%s, %s) on conflict do nothing;", (place['place_id'], json.dumps(place)))




for neighborhood in neighborhoods:
    get_stores("bakeries", "bakery", neighborhood)
    get_stores("home_impovement_stores", "home improvement store", neighborhood)
    get_stores("hardware_stores", "hardware store", neighborhood)