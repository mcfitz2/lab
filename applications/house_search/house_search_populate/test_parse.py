import base64
import json
from bs4 import BeautifulSoup
import pprint

import unicodedata

import requests
printable = {'Lu', 'Ll'}
def filter_non_printable(str):
  return ''.join(c for c in str if unicodedata.category(c) in printable)
def convert_int(s):
    if not s:
        return None
    return int(s.replace('$', '').replace(',',''))

def download_img_to_base64(url):
    return base64.b64encode(requests.get(url).content)

converters = [
    ('New construction', 'new_construction', lambda x: x.lower().strip() == 'yes'),
    ('Architectural style', 'architectural_style', lambda x: x.strip()),
    ('Annual tax amount', 'annual_taxes', convert_int),
    ('Garage Spaces', 'garage_spaces', convert_int),
    ('Major remodel year', 'major_remodel_year', convert_int),
    ('Parcel number', 'parcel_number', convert_int),
    ('Tax assessed value', 'tax_assessed_value', convert_int),
    ('Stories', 'stories', convert_int),
    ('Parking features', 'parking_features', lambda x: x.strip())
    
]





with open('test.json', 'rb') as f:
    payload = json.load(f)
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
        'year_built': int(highlights[1].split('Built in ')[1]),
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
    pprint.pprint(house_info)
    
