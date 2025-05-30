import os

from sqlmodel import select
import gspread
import json
from collections import OrderedDict

from models import Neighborhood, BusStop, LStop
import numpy_financial as npf
import time
import uuid
import requests
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.sql import text
from homeharvest import scrape_property
import datetime
from models import House
import overpy
from utils import boundingBox, download_img_to_base64
import openrouteservice
import pprint
import googlemaps

from utils import geojson_to_geography

STATE_EQUALIZER = 2.916
ASSESSMENT_LEVEL = 0.1
HOMEOWNER_EXEMPTION = 10000
TAX_RATE = 0.08
ESTIMATED_INSURANCE = 1975  # 500K Assessed value
DOWN_PAYMENT_PERCENT = 0.05
PMI_PERCENT = 0.0046  # Estimated from NerdWallet
INTEREST_RATE = 0.07
LOAN_TERM_MONTHS = 30


class HouseProcessor:
    def __init__(self, engine):
        self.engine = engine
    def _meters_to_miles(self, meters):
        return meters * 0.000621371

    def _lines_served(self, stop):
        mapping = {
            "red": "Red",
            "blue": "Blue",
            "g": "Green",
            "brn": "Brown",
            "p": "Purple",
            "pexp": "Purple Express",
            "y": "Yellow",
            "pnk": "Pink",
            "o": "Orange",
        }
        return [
            mapping[key]
            for key, value in stop.items()
            if key in mapping.keys() and value
        ]

    def _routes_served(self, stop):
        return stop["routesstpg"].split(",")

    async def initialize(self):
        print("Loading neighborhoods")
        URL = "https://data.cityofchicago.org/resource/y6yq-dbs2.json"
        r = requests.get(URL, headers={"X-App-Token": os.environ['CHICAGO_DATA_TOKEN']}, timeout=120)
        async with AsyncSession(self.engine) as session:
            for neighborhood in r.json():
                await Neighborhood.upsert(
                    Neighborhood.model_validate(
                        {
                            "primary_name": neighborhood["pri_neigh"],
                            "secondary_name": neighborhood["sec_neigh"],
                            "location": geojson_to_geography(neighborhood["the_geom"]),
                        }
                    ), session
                )
            await session.commit()
        print("Loading L stops")
        URL = "https://data.cityofchicago.org/resource/8pix-ypme.json"
        r = requests.get(URL, headers={"X-App-Token": os.environ['CHICAGO_DATA_TOKEN']}, timeout=120)
        async with AsyncSession(self.engine) as session:
            for l_stop in r.json():
                await LStop.upsert(
                    LStop.model_validate({
                        'stop_id': l_stop["stop_id"],
                        'direction_id': l_stop["direction_id"],
                        'stop_name': l_stop["stop_name"],
                        'station_name': l_stop["station_name"],
                        'station_descriptive_name': l_stop["station_descriptive_name"],
                        'map_id': l_stop["map_id"],
                        'ada': l_stop["ada"],
                        'lines': self._lines_served(l_stop),
                        'location': f"SRID=4326;POINT({l_stop['location']['longitude']} {l_stop['location']['latitude']})",
                    }), session
                )
            await session.commit()

        print("Loading bus stops")
        URL = "https://data.cityofchicago.org/resource/qs84-j7wh.json"
        r = requests.get(URL, headers={"X-App-Token": os.environ['CHICAGO_DATA_TOKEN']}, timeout=120)
        async with AsyncSession(self.engine) as session:
            for bus_stop in r.json():
                await BusStop.upsert(
                    BusStop.model_validate(
                        {
                            "stop_id": bus_stop["systemstop"],
                            "direction": bus_stop["dir"],
                            "street": bus_stop["street"],
                            "cross_street": bus_stop["cross_st"],
                            "name": bus_stop["public_nam"],
                            "pos": bus_stop["pos"],
                            "routes": self._routes_served(bus_stop),
                            "location": geojson_to_geography(bus_stop["the_geom"]),
                        }
                    ),
                    session,
                )
            await session.commit()

    async def _geocode(self, session: AsyncSession, address: str) -> House:
        try:
            r = requests.get(
                "https://geocode.maps.co/search",
                params={
                    "api_key": os.environ['MAPS_CO_TOKEN'],
                    "format": "jsonv2",
                    "q": address,
                }, timeout=120
            )
            result = r.json()[0]
        except Exception as e:
            print(r.status_code)
            pprint.pprint(r.content)
            raise e
        lat, lon = result["lat"], result["lon"]
        time.sleep(2)
        r = requests.get(
            "https://geocode.maps.co/reverse",
            params={
                "api_key": os.environ['MAPS_CO_TOKEN'],
                "format": "jsonv2",
                "lat": lat,
                "lon": lon,
            }, timeout=120
        )
        if not r.status_code == 200:
            print(r.status_code)
            print(r.content)
        result_reverse = r.json()
        house = {
            "house_id": str(uuid.uuid4()),
            "address": f"{str(result_reverse['address']['house_number'])} {result_reverse['address']["road"]}, {result_reverse['address']["city"]}, {result_reverse['address']["state"]} {str(result_reverse['address']["postcode"])}",
            "latitude": lat,
            "longitude": lon,
            "house_number": str(result_reverse['address']['house_number']),
            "road": result_reverse['address']["road"],
            "city": result_reverse['address']["city"],
            "state": result_reverse['address']["state"],
            "postcode": str(result_reverse['address']["postcode"]),
            "location": f"SRID=4326;POINT({lon} {lat})"
        }
        return House.model_validate(house)

    async def _process_financials(self, session: AsyncSession, house: House) -> House:
        house.annual_taxes = ((((house.price * ASSESSMENT_LEVEL) * STATE_EQUALIZER) - HOMEOWNER_EXEMPTION) * TAX_RATE)
        house.yearly_insurance = ESTIMATED_INSURANCE
        house.pmi = (house.price - (house.price * DOWN_PAYMENT_PERCENT)) * PMI_PERCENT
        house.monthly_payment = abs(
            npf.pmt(INTEREST_RATE / 12, 12 * LOAN_TERM_MONTHS, house.price - (house.price * DOWN_PAYMENT_PERCENT), 0))
        house.monthly_cost = house.annual_taxes / 12 + house.yearly_insurance / 12 + house.pmi / 12 + house.monthly_payment
        return house

    async def _process_mls(self, session: AsyncSession, house: House) -> House:
        properties = scrape_property(
            location=house.address,
            #listing_type="for_sale",  # or (for_sale, for_rent, pending)
            property_type=["single_family", "multi_family"],
        )
        mls = properties.to_dict(orient="records")[0]
        #pprint.pprint(mls)
        if not mls.get("half_baths"):
            mls["half_baths"] = 0
        house.url = mls["property_url"]
        house.price = mls["list_price"]
        house.beds = mls["beds"]
        house.baths = mls["full_baths"] + (0.5 * mls["half_baths"])
        house.sqft = mls["sqft"]
        house.home_type = mls["style"]
        house.year_built = mls["year_built"]
        house.lot_size = mls["lot_sqft"]
        if mls.get('sqft') and mls.get('list_price'):
            house.price_per_sqft = mls["list_price"] / mls["sqft"]
        house.hoa_fees = mls["hoa_fee"]
        house.description = mls["text"]
        house.days_on_mls = mls["days_on_mls"]
        # house.images = [self.download_img_to_base64(url) for url in [mls['primary_photo']] + mls['alt_photos'].split(',')]
        house.primary_image = download_img_to_base64(mls['primary_photo'])
        house.primary_image_url = mls['primary_photo']
        house.new_construction = mls["new_construction"]
        house.garage_spaces = mls["parking_garage"]
        house.stories = mls["stories"]
        pprint.pprint(mls)
        return house

    async def _process_neighborhood(self, session: AsyncSession, house: House) -> House:
        async with AsyncSession(self.engine) as session:
            neighborhood = await session.exec(
                text(
                    "select * from neighborhood where ST_Contains(location::geometry, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) limit 1;" % (
                        house.longitude, house.latitude)),
            )
            house.neighborhood = neighborhood.first().primary_name
            return house

    async def _process_l_stops(self, session: AsyncSession, house: House) -> House:
        async def find_station_by_name(name):
            keys = ["station_name", "lines"]
            async with AsyncSession(self.engine) as session:
                statement = select(LStop).where(LStop.station_name == name)
                stops = (await session.exec(statement)).first()
                if stops:
                    return stops.lines
                return []

        gmaps = googlemaps.Client(key=os.environ['GOOGLE_API_KEY'])

        api = overpy.Overpass()
        south, west, north, east = boundingBox(house.latitude, house.longitude, 4.828032)
        query = f'nwr["public_transport"="station"]["subway"="yes"]["network"="CTA"]({south}, {west}, {north}, {east});out;'
        result = api.query(query)
        now = datetime.datetime.now()
        for node in result.nodes:
            routes = gmaps.directions((house.latitude, house.longitude),
                                      (float(node.lat), float(node.lon)),
                                      mode="walking",
                                      departure_time=now)
            leg = routes[0]['legs'][0]
            lines_served = await find_station_by_name(node.tags.get('name'))
            house.nearest_cta_stations.append(
                {"lat": float(node.lat), "lon": float(node.lon), "operator": node.tags.get("operator"),
                 "name": node.tags.get('name'), "duration_walking": leg['duration']['value'] / 60,
                 "distance_walking": self._meters_to_miles(leg['distance']['value']), "lines_served": lines_served})

        return house
    async def _process_non_transit(self, session: AsyncSession, house: House, field: str, query: str, radius: int) -> House:
        gmaps = googlemaps.Client(key=os.environ['GOOGLE_API_KEY'])

        api = overpy.Overpass()
        south, west, north, east = boundingBox(house.latitude, house.longitude, radius)
        query = f'{query}({south}, {west}, {north}, {east});out;'
        result = api.query(query)
        now = datetime.datetime.now()
        for node in result.nodes[:5]:
            walking = gmaps.directions((house.latitude, house.longitude),
                                      (float(node.lat), float(node.lon)),
                                      mode="walking",
                                      departure_time=now)[0]['legs'][0]
            driving = gmaps.directions((house.latitude, house.longitude),
                                      (float(node.lat), float(node.lon)),
                                      mode="driving",
                                      departure_time=now)[0]['legs'][0]
            getattr(house, field).append(
                {"lat": float(node.lat), "lon": float(node.lon),
                 "name": node.tags.get('name'), "duration_walking": walking['duration']['value'] / 60,
                 "distance_walking": self._meters_to_miles(walking['distance']['value']), "duration_driving": driving['duration']['value'] / 60,
                 "distance_driving": self._meters_to_miles(driving['distance']['value'])})
        return house
    async def _process_grocery_stores(self, session: AsyncSession, house: House, radius: int) -> House:
        gmaps = googlemaps.Client(key=os.environ['GOOGLE_API_KEY'])

        api = overpy.Overpass()
        south, west, north, east = boundingBox(house.latitude, house.longitude, radius)
        query = f'''
                (
                    nwr["shop"="supermarket"]["name"~"jewel", i]({south}, {west}, {north}, {east});
                    nwr["shop"="supermarket"]["name"~"aldi", i]({south}, {west}, {north}, {east});
                    nwr["shop"="supermarket"]["name"~"whole foods", i]({south}, {west}, {north}, {east});
                    nwr["shop"="supermarket"]["name"~"kroger", i]({south}, {west}, {north}, {east});
                    nwr["shop"="supermarket"]["name"~"walmart", i]({south}, {west}, {north}, {east});
                    nwr["shop"="supermarket"]["name"~"trader", i]({south}, {west}, {north}, {east});
                    nwr["shop"="supermarket"]["name"~"costco", i]({south}, {west}, {north}, {east});
                );
                out;
                '''
        #query = f'{query}({south}, {west}, {north}, {east});out;'
        result = api.query(query)
        now = datetime.datetime.now()
        for node in result.nodes[:5]:
            walking = gmaps.directions((house.latitude, house.longitude),
                                      (float(node.lat), float(node.lon)),
                                      mode="walking",
                                      departure_time=now)[0]['legs'][0]
            driving = gmaps.directions((house.latitude, house.longitude),
                                      (float(node.lat), float(node.lon)),
                                      mode="driving",
                                      departure_time=now)[0]['legs'][0]
            getattr(house, "nearest_grocery_stores").append(
                {"lat": float(node.lat), "lon": float(node.lon),
                 "name": node.tags.get('name'), "duration_walking": walking['duration']['value'] / 60,
                 "distance_walking": self._meters_to_miles(walking['distance']['value']), "duration_driving": driving['duration']['value'] / 60,
                 "distance_driving": self._meters_to_miles(driving['distance']['value'])})
        return house
    async def _find_bus_stops(self, lat, lon, radius=500):
        keys = ["name", "routes", "direction", "lon", "lat", "distance"]
        async with AsyncSession(self.engine) as session:
            bus_stops = await session.exec(
                text(
                    "SELECT distinct name, routes, direction, ST_X(ST_Centroid(ST_Transform(location::geometry, 4326))) AS long, ST_Y(ST_Centroid(ST_Transform(location::geometry, 4326))) AS lat, ST_Distance(location::geography, ST_MakePoint(%s, %s)::geography) FROM busstop WHERE ST_DWithin(location::geography, ST_MakePoint(%s, %s)::geography, %s);" % (
                        lon, lat, lon, lat, radius)),
            )
            return [
                {keys[i]: row[i] for i in range(len(keys))} for row in bus_stops
            ]

    async def _process_bus_stops(self, session: AsyncSession, house: House) -> House:
        gmaps = googlemaps.Client(key=os.environ['GOOGLE_API_KEY'])
        now = datetime.datetime.now()
        for stop in await self._find_bus_stops(house.latitude, house.longitude, radius=1609):
            routes = gmaps.directions((house.latitude, house.longitude),
                                      (float(stop['lat']), float(stop['lon'])),
                                      mode="walking",
                                      departure_time=now)
            leg = routes[0]['legs'][0]
            house.nearest_bus_stops.append(
                {"lat": float(stop['lat']), "lon": float(stop['lon']), "operator": "CTA",
                 "name": stop['name'], "duration_walking": leg['duration']['value'] / 60,
                 "distance_walking": self._meters_to_miles(leg['distance']['value']), "direction": stop['direction'],
                 "routes": stop['routes']})
        return house
    async def _process_soul_cycles(self, session: AsyncSession, house: House) -> House:
        gmaps = googlemaps.Client(key=os.environ['GOOGLE_API_KEY'])
        now = datetime.datetime.now()

        locations = [
                {'name': "SoulCycle Old Town",'lat': 41.906254740856305, 'lon': -87.63334885692286},
                {'name': "SoulCycle LOOP",    'lat':41.8881359739359, 'lon':-87.62890937888268}
            ]
        for stop in locations:
            walking = gmaps.directions((house.latitude, house.longitude),
                                      (float(stop['lat']), float(stop['lon'])),
                                      mode="walking",
                                      departure_time=now)[0]['legs'][0]
            driving = gmaps.directions((house.latitude, house.longitude),
                                      (float(stop['lat']), float(stop['lon'])),
                                      mode="driving",
                                      departure_time=now)[0]['legs'][0]
            transit = gmaps.directions((house.latitude, house.longitude),
                                      (float(stop['lat']), float(stop['lon'])),
                                      mode="transit",
                                      departure_time=now)[0]['legs'][0]
            getattr(house, "nearest_soul_cycles").append(
                {"lat": float(stop['lat']), "lon": float(stop['lon']),
                 "name": stop['name'], 
                 "duration_walking": walking['duration']['value'] / 60,
                 "distance_walking": self._meters_to_miles(walking['distance']['value']),
                 "duration_transit": transit['duration']['value'] / 60,
                 "distance_transit": self._meters_to_miles(transit['distance']['value']), 
                 "duration_driving": driving['duration']['value'] / 60,
                 "distance_driving": self._meters_to_miles(driving['distance']['value'])})
        return house
    async def upsert_house_to_sheet(self, house):
        def format_l_stops(stops):
            stops = sorted(stops, key=lambda x: x['duration_walking'])[:5]
            if len(stops) == 0:
                return "No L stations within 3 miles"
            out = ""
            for stop in stops:
                out += f"{stop['name']}: {stop['duration_walking']:.1f} min ({','.join(stop['lines_served'])})\n"
            return out
        def format_bus_stops(stops):
            stops = sorted(stops, key=lambda x: x['duration_walking'])[:5]
            if len(stops) == 0:
                return "No bus stops within 1 mile"
            out = ""
            for stop in stops:
                out += f"{stop['name']} {stop['direction']}: {stop['duration_walking']:.1f} min ({','.join(stop['routes'])})\n"
            return out
        def format_non_transit(places):
            stops = sorted(places, key=lambda x: x['duration_walking'])[:5]
            out = ""
            for place in places:
                if place.get('duration_transit'):
                    out += f"{place['name']}: {place['duration_walking']:.1f} min walk, {place['duration_driving']:.1f} min drive, {place['duration_transit']:.1f} min by transit\n"
                else:
                    out += f"{place['name']}: {place['duration_walking']:.1f} min walk, {place['duration_driving']:.1f} min drive\n"
            print(out)
            return out

        gc = gspread.service_account(filename=os.environ['SERVICE_ACCOUNT_CREDENTIALS_FILE'])

        sh = gc.open_by_key(os.environ['SPREADSHEET_ID'])

        worksheet = sh.worksheet("Houses")
        fields = OrderedDict({
            "primary_image_url": {"friendly": "Image", "format": None, "transformer": lambda x: f'=IMAGE("{x}")'},

            "address": {"friendly": "Full Address",
                        "format": {"numberFormat": {"type": "TEXT"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "price": {"friendly": "Price",
                      "format": {"textFormat": {"fontSize": 12}, "verticalAlignment": "TOP",
                                 "numberFormat": {"type": "CURRENCY"}}},
            "monthly_cost": {"friendly": "Monthly Cost",
                             "format": {"textFormat": {"fontSize": 12}, "verticalAlignment": "TOP",
                                        "numberFormat": {"type": "CURRENCY"}}},
            "neighborhood": {"friendly": "Neighborhood",
                             "format": {"numberFormat": {"type": "TEXT"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},

            "url": {"friendly": "Realtor.com Listing",
                    "format": {"numberFormat": {"type": "TEXT"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}, "transformer": lambda x: f'=HYPERLINK("{x}", "Open Listing")'},

            "beds": {"friendly": "Beds", "format": {"numberFormat": {"type": "NUMBER"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "baths": {"friendly": "Baths", "format": {"numberFormat": {"type": "NUMBER"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "sqft": {"friendly": "Sq Feet", "format": {"numberFormat": {"type": "NUMBER"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},

            "year_built": {"friendly": "Year Built",
                           "format": {"numberFormat": {"type": "TEXT"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "lot_size": {"friendly": "Lot Size",
                         "format": {"numberFormat": {"type": "NUMBER"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "price_per_sqft": {"friendly": "Price/SqFt",
                               "format": {"textFormat": {"fontSize": 12}, "verticalAlignment": "TOP",
                                          "numberFormat": {"type": "CURRENCY"}}},
            "hoa_fees": {"friendly": "HOA Fees",
                         "format": {"textFormat": {"fontSize": 12}, "verticalAlignment": "TOP",
                                    "numberFormat": {"type": "CURRENCY"}}},
            # "description": {"friendly": "Description",
            #                 "format": {"textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "days_on_mls": {"friendly": "Days Listed",
                            "format": {"numberFormat": {"type": "NUMBER"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "new_construction": {"friendly": "New Construction",
                                 "format": {"numberFormat": {"type": "TEXT"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "garage_spaces": {"friendly": "Garage Spaces",
                              "format": {"numberFormat": {"type": "NUMBER"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "parcel_number": {"friendly": "Parcel Number",
                              "format": {"textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "tax_assessed_value": {"friendly": "Assessed Value",
                                   "format": {"textFormat": {"fontSize": 12}, "verticalAlignment": "TOP",
                                              "numberFormat": {"type": "CURRENCY"}}},
            "stories": {"friendly": "Stories", "format": {"numberFormat": {"type": "NUMBER"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "transit_score": {"friendly": "Transit Score",
                              "format": {"numberFormat": {"type": "NUMBER"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "walk_score": {"friendly": "Walk Score",
                           "format": {"numberFormat": {"type": "NUMBER"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "bike_score": {"friendly": "Bike Score",
                           "format": {"numberFormat": {"type": "NUMBER"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "annual_taxes": {"friendly": "Yearly Taxes",
                             "format": {"textFormat": {"fontSize": 12}, "verticalAlignment": "TOP",
                                        "numberFormat": {"type": "CURRENCY"}}},
            "yearly_insurance": {"friendly": "Yearly Insurance",
                                 "format": {"textFormat": {"fontSize": 12}, "verticalAlignment": "TOP",
                                            "numberFormat": {"type": "CURRENCY"}}},
            "pmi": {"friendly": "Yearly PMI",
                    "format": {"textFormat": {"fontSize": 12}, "verticalAlignment": "TOP",
                               "numberFormat": {"type": "CURRENCY"}}},
            "monthly_payment": {"friendly": "Monthly Payment",
                                "format": {"textFormat": {"fontSize": 12}, "verticalAlignment": "TOP",
                                           "numberFormat": {"type": "CURRENCY"}}},

            "house_number": {"friendly": "House Number",
                             "format": {"numberFormat": {"type": "TEXT"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "road": {"friendly": "Road", "format": {"numberFormat": {"type": "TEXT"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "city": {"friendly": "City", "format": {"numberFormat": {"type": "TEXT"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "state": {"friendly": "State", "format": {"numberFormat": {"type": "TEXT"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "postcode": {"friendly": "Zip Code",
                         "format": {"numberFormat": {"type": "TEXT"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
            "nearest_cta_stations": {"friendly": "L Stops",
                                     "format": {"numberFormat": {"type": "TEXT"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"},
                                     "transformer": format_l_stops},
            "nearest_bus_stops": {"friendly": "Bus Stops",
                                  "format": {"numberFormat": {"type": "TEXT"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"},
                                  "transformer": format_bus_stops},
            "nearest_bakeries": {"friendly": "Bakeries",
                                  "format": {"numberFormat": {"type": "TEXT"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"},
                                  "transformer": format_non_transit},
            "nearest_grocery_stores": {"friendly": "Grocery Stores",
                                  "format": {"numberFormat": {"type": "TEXT"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"},
                                  "transformer": format_non_transit},
             "nearest_soul_cycles": {"friendly": "Soul Cycles",
                                  "format": {"numberFormat": {"type": "TEXT"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"},
                                  "transformer": format_non_transit},
            "home_type": {"friendly": "Type", "format": {"numberFormat": {"type": "TEXT"}, "textFormat": {"fontSize": 12}, "verticalAlignment": "TOP"}},
        })

        def number_to_excel_column(n):
            n += 1  # Convert to 1-indexed
            quotient, remainder = divmod(n - 1, 26)
            if quotient == 0:
                return chr(remainder + ord('A'))
            else:
                return chr((quotient - 1) % 26 + ord('A')) + chr(remainder + ord('A'))

        def get_headers():
            return [v['friendly'] for k, v in fields.items()]

        worksheet.update([get_headers()])
        for index, k in enumerate(fields.keys()):
            format = fields[k].get('format')
            if format:
                worksheet.format(f"{number_to_excel_column(index)}:{number_to_excel_column(index)}", format)
        worksheet.format(f"1:1", {
            "verticalAlignment": "TOP",
            "backgroundColor": {
                "red": 0.5,
                "blue": 0.8,
                "green": 0.6,
                "alpha": 1
            },
            "textFormat": {
                "bold": True,
                "fontSize": 16,
                "foregroundColor": {
                    "red": 0,
                    "blue": 0,
                    "green": 0,
                    "alpha": 1

                }
            }
        })
        sheet_id = worksheet._properties['sheetId']
        body = {
            "requests": [
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": 1,
                            "endIndex": 200
                        },
                        "properties": {
                            "pixelSize": 270
                        },
                        "fields": "pixelSize"
                    }
                },
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 1,
                        },
                        "properties": {
                            "pixelSize": 360
                        },
                        "fields": "pixelSize"
                    }
                }
            ]
        }
        res = sh.batch_update(body)

        def convert_fields(obj, key, options):
            value = getattr(obj, key)
            if options.get("transformer"):
                value = options.get("transformer")(value)
                print(key, options, value)

            else:
                return str(value)
            return value

        cell = worksheet.find(house.address)
        if cell:
            worksheet.delete_rows(cell.row)

        resp = worksheet.append_row([convert_fields(house, field, options) for field, options in fields.items()],
                                    value_input_option="USER_ENTERED")
        worksheet.columns_auto_resize(start_column_index=2, end_column_index=len(fields.keys()))
        worksheet.clear_basic_filter()
        worksheet.set_basic_filter(f"B1:{number_to_excel_column(len(fields.keys()))}1")

    async def process(self, address: str) -> House:
        async with AsyncSession(self.engine) as session:
            house = await self._geocode(session, address)
            house = await self._process_mls(session, house)
            try:
                house = await self._process_financials(session, house)
            except Exception as e:
                pass
            try:
                house = await self._process_neighborhood(session, house)
            except Exception as e:
                pass
            try:
                house = await self._process_l_stops(session, house)
            except Exception as e:
                pass
            try:
                house = await self._process_bus_stops(session, house)
            except Exception as e:
                pass
            try:
                house = await self._process_non_transit(session, house, "nearest_bakeries", 'nwr["shop"="bakery"]', 4.828032)
            except Exception as e:
                pass
            try:
                house = await self._process_grocery_stores(session, house, 8.04672)
            except Exception as e:
                pass
            try:
                house = await self._process_soul_cycles(session, house)
            except Exception as e:
                pass

            await House.upsert(house, session)
            await session.commit()
        await self.upsert_house_to_sheet(house)
        return house
