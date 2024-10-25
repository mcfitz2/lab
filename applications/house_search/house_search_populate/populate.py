

from prefect import flow, task, variables
from prefect.blocks.system import Secret
import requests
import json
import psycopg2
import requests
from datetime import date, datetime
from bs4 import BeautifulSoup
import base64
import unicodedata

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def connect_to_db():
    print("Connecting to DB")
    user = Secret.load("greatlakes-user").get()
    password = Secret.load("greatlakes-password").get()
    psql = psycopg2.connect(database=variables.get("greatlakes_db"), host=variables.get("greatlakes_host"),
                            port=int(variables.get("greatlakes_port")), user=user, password=password)
    return psql

@task(retries=5, retry_delay_seconds=10)
def geocode_address(address):
    r = requests.get('https://geocode.maps.co/search', params={'api_key':'', 'format':'jsonv2', 'q': address})
    result = r.json()[0]
    lat, lon = result['lat'], result['lon']
    r = requests.get('https://geocode.maps.co/reverse', params={'api_key':'', 'format':'jsonv2', 'lat': lat, 'lon':lon})
    if not r.status_code == 200:
        print(r.status_code)
        print(r.content)
    result_reverse = r.json()
    return lat, lon, result_reverse['address']

@task
def determine_neighborhood(lat, lon):
    with connect_to_db() as conn: 
        cursor = conn.cursor()
        cursor.execute('select * from house_search.neighborhoods where ST_Contains(geom::geometry, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) limit 1;', (lon, lat))
        return cursor.fetchone()
    
@task
def find_cta_stations(lat, lon, radius=5000):
    keys = ['station_name', 'lines', 'distance']
    with connect_to_db() as conn: 
        cursor = conn.cursor()
        cursor.execute("SELECT distinct station_name, lines, ST_Distance(location::geography, ST_MakePoint(%s, %s)::geography) FROM house_search.l_stops WHERE ST_DWithin(location::geography, ST_MakePoint(%s, %s)::geography, %s);", (lon, lat, lon, lat, radius))
        return [{keys[i]: row[i] for i in range(len(keys))} for row in cursor.fetchall()]
    
@task
def get_crimes(lat, lon, radius=1600):
    with connect_to_db() as conn:
        keys = ['primary_type', 'description', 'date', 'distance']
        cursor = conn.cursor()
        cursor.execute("SELECT primary_type, description, date, ST_Distance(geom::geography, ST_MakePoint(%s, %s)::geography) FROM house_search.crimes WHERE geom is not null and date > (current_date - INTERVAL '3 months') and ST_DWithin(geom::geography, ST_MakePoint(%s, %s)::geography, %s);", (lon, lat, lon, lat, radius))
        crimes = cursor.fetchall()
        cursor.execute("select avg(count) from (SELECT count(*) as count, date_trunc('month', date) as month FROM house_search.crimes WHERE geom is not null and date > (current_date - INTERVAL '3 months') and ST_DWithin(geom, ST_MakePoint(%s, %s)::geography, %s) group by month) a;", (lon, lat, radius))
        per_month = cursor.fetchone()[0]
        return {
            "crimes": [{keys[i]: row[i] for i in range(len(keys))} for row in crimes],
            "avg_crimes_per_month": float(per_month)
        }
@task
def create_house_table():
    with connect_to_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE if not exists house_search.houses (
                            house_number varchar,
                            road varchar,
                            city varchar,
                            state varchar,
                            postcode varchar,
                            address jsonb,
                            latitude numeric,
                            longitude numeric,
                            neighborhood varchar,
                            nearest_cta_stations jsonb,
                            crimes jsonb,
                            url varchar,
                            price bigint,
                            beds bigint,
                            baths bigint,
                            sqft bigint,
                            home_type varchar,
                            year_built bigint,
                            lot_size bigint,
                            zestimate bigint,
                            price_per_sqft bigint,
                            hoa_fees bigint,
                            description text,
                            days_on_zillow bigint,
                            views bigint,
                            saves bigint,
                            status varchar,
                            images varchar[],
                            new_construction varchar,
                            architectural_style varchar,
                            annual_taxes bigint,
                            garage_spaces bigint,
                            major_remodel_year bigint,
                            parcel_number bigint,
                            tax_assessed_value bigint,
                            stories bigint,
                            parking_features varchar,
                            transit_score bigint,
                            walk_score bigint,
                            bike_score bigint,
                            location geography,
                            primary key (house_number, road, city, state, postcode)
                        );''')

      
@task 
def dist_to_home_improvement(address):
    
@task
def populate_house(house_info):
    address = house_info['address']
    lat, lon, address_structured = geocode_address(address)
    neighborhood, neighborhood_secondary, polygon = determine_neighborhood(lat, lon)
    stations = find_cta_stations(lat, lon)
    crimes = get_crimes(lat, lon)
    house_info.update({
        'house_number': address_structured['house_number'],
        'road': address_structured['road'],
        'city': address_structured['city'],
        'state': address_structured['state'],
        'postcode': address_structured['postcode'],
        'address': json.dumps(address_structured, default=json_serial),
        'latitude': lat,
        'longitude': lon,
        'neighborhood': neighborhood,
        'nearest_cta_stations': json.dumps(stations, default=json_serial),
        'crimes': json.dumps(crimes, default=json_serial)
    })
    with connect_to_db() as conn:
        cursor = conn.cursor()
        cursor.execute('delete from house_search.houses where house_number = %(house_number)s and road = %(road)s and city = %(city)s and state = %(state)s and postcode = %(postcode)s;', house_info) 
        cursor.execute('''insert into house_search.houses (
                                    house_number, 
                                    road, 
                                    city, 
                                    state, 
                                    postcode, 
                                    address, 
                                    latitude, 
                                    longitude, 
                                    neighborhood, 
                                    nearest_cta_stations, 
                                    crimes,
                                    url,
                                    price,
                                    beds,
                                    baths,
                                    sqft,
                                    home_type,
                                    year_built,
                                    lot_size,
                                    zestimate,
                                    price_per_sqft,
                                    hoa_fees,
                                    description,
                                    days_on_zillow,
                                    views,
                                    saves,
                                    status,
                                    images,
                                    new_construction,
                                    architectural_style,
                                    annual_taxes,
                                    garage_spaces,
                                    major_remodel_year,
                                    parcel_number,
                                    tax_assessed_value,
                                    stories,
                                    parking_features,
                                    transit_score,
                                    walk_score,
                                    bike_score, 
                                    location) values (
                                        %(house_number)s, 
                                        %(road)s, 
                                        %(city)s, 
                                        %(state)s,
                                        %(postcode)s, 
                                        %(address)s, 
                                        %(latitude)s, 
                                        %(longitude)s, 
                                        %(neighborhood)s, 
                                        %(nearest_cta_stations)s, 
                                        %(crimes)s,
                                        %(url)s,
                                        %(price)s,
                                        %(beds)s,
                                        %(baths)s,
                                        %(sqft)s,
                                        %(home_type)s,
                                        %(year_built)s,
                                        %(lot_size)s,
                                        %(zestimate)s,
                                        %(price_per_sqft)s,
                                        %(hoa_fees)s,
                                        %(description)s,
                                        %(days_on_zillow)s,
                                        %(views)s,
                                        %(saves)s,
                                        %(status)s,
                                        %(images)s,
                                        %(new_construction)s,
                                        %(architectural_style)s,
                                        %(annual_taxes)s,
                                        %(garage_spaces)s,
                                        %(major_remodel_year)s,
                                        %(parcel_number)s,
                                        %(tax_assessed_value)s,
                                        %(stories)s,
                                        %(parking_features)s, 
                                        %(transit_score)s,
                                        %(walk_score)s,
                                        %(bike_score)s,
                                        ST_SetSRID(ST_MakePoint(%(longitude)s, %(latitude)s), 4326))''', 
                                house_info)
@task 
def get_payload(payload_url):
    print('Got submission for URL', payload_url)
    r = requests.get(payload_url)
    real_payload = r.json()
    return real_payload

printable = {'Lu', 'Ll'}
def filter_non_printable(str):
  return ''.join(c for c in str if unicodedata.category(c) in printable)
def convert_int(s):
    if not s:
        return None
    return int(s.replace('$', '').replace(',',''))

def download_img_to_base64(url):
    return base64.b64encode(requests.get(url).content)
@task
def extract_info(payload):
    converters = [
        ('New construction', 'new_construction', lambda x: x.lower().strip() == 'yes'),
        ('Architectural style', 'architectural_style', lambda x: x.strip()),
        ('Annual tax amount', 'annual_taxes', convert_int),
        ('Garage spaces', 'garage_spaces', convert_int),
        ('Major remodel year', 'major_remodel_year', convert_int),
        ('Parcel number', 'parcel_number', convert_int),
        ('Tax assessed value', 'tax_assessed_value', convert_int),
        ('Stories', 'stories', convert_int),
        ('Parking features', 'parking_features', lambda x: x.strip()),
        ('Year built', 'year_built', convert_int)
    ]

    soup = BeautifulSoup(payload['htmlBody'], 'html.parser')
    bed_bath = soup.select('div[data-testid="bed-bath-sqft-fact-container"] > span')

    highlights = [h.get_text() for h in soup.select('#search-detail-lightbox div.layout-container-desktop > div.layout-content-container > div.layout-static-column-container > div > div > div:nth-child(4) > div > div > div > div > span')]
    stats = [h.get_text() for h in soup.select('#search-detail-lightbox div.layout-container-desktop > div.layout-content-container > div.layout-static-column-container > div > div > div:nth-child(6) > div > div > dl > dt')]
    facts = {item.get_text().split(':')[0]:item.get_text().split(':')[-1] for item in soup.select('div[data-testid="fact-category"] li') if ':' in item.get_text()}
    images = [download_img_to_base64(el.attrs.get('src')) for el in soup.select('div[data-testid="hollywood-gallery-images-tile-list"] li img') if not 'third-party-virtual-tour' in el.attrs.get('src')]
    scores = soup.select('div.neighborhood-score > div:nth-child(2)')
    score_type_mapping = {
        'Walk Score':'walk_score',
        'Transit Score': 'transit_score',
        'Bike Score': 'bike_score'
    }
    house_info = {
        "url": payload['url']['protocol']+'//'+payload['url']['hostname']+payload['url']['pathname'],
        'price': soup.select('span[data-testid="price"] > span')[0].get_text().replace('$', '').replace(',', ''),
        'address': soup.select('div[data-testid="fs-chip-container"] h1')[0].get_text().replace('\xa0', ' '),
        'beds': int(bed_bath[0].get_text()),
        'baths': int(bed_bath[2].get_text()),
        'sqft': int(bed_bath[4].get_text().replace(',', '')),
        'home_type': highlights[0],
        'year_built': None,
        'lot_size': convert_int(highlights[2].split(' ')[0]),
        'zestimate': convert_int(highlights[3].split(' ')[0].replace('$', '').replace('--', '') or None),
        'price_per_sqft': convert_int(highlights[4].split('/')[0]),
        'hoa_fees': highlights[5].split(' ')[0].replace('$', '').replace('--', '') or None,
        'description': soup.select('div[data-testid="description"] > article > div > div')[0].get_text(),
        'days_on_zillow': int(stats[0].split(' ')[0]),
        'views': int(stats[2]),
        'saves': int(stats[4]),
        'status': soup.select('div[data-testid="gallery-status-pill"] > div > span:nth-child(2)')[0].get_text(),
        'images': images,
        'walk_score': None,
        'bike_score': None,
        'transit_score': None
    }
    for score in scores:
        score_type = score_type_mapping.get(score.select('span > button')[0].get_text().replace('®', ''))
        score_value = score.select('div > a')[0].get_text()
        house_info[score_type] = int(score_value)
    for original_key, new_key, converter in converters:
        if original_key in facts:
            house_info[new_key] = converter(facts[original_key])
        else:
            house_info[new_key] = None
    return house_info

    
@flow(log_prints=True)
def populate_by_html(payload):
    create_house_table()
    payload = get_payload(payload['payload_url'])
    house_info = extract_info(payload)
    populate_house(house_info)
if __name__ == "__main__":
    populate_by_html.serve(name="house-search-populate-by-html", cron="0 * * * *")
