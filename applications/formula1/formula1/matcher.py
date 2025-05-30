import os
import time
import json
import re
import requests
from rapidfuzz import fuzz
from tvdb_v4_official import TVDB
import datetime

CACHE_DIR = "cache"
CACHE_TTL = 60 * 10

def cache_get(cache_key):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")
    if os.path.exists(cache_path):
        if time.time() - os.path.getmtime(cache_path) < CACHE_TTL:
            with open(cache_path, "r") as f:
                return json.load(f)
    return None

def cache_set(cache_key, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")
    with open(cache_path, "w") as f:
        json.dump(data, f)

# Example mapping, expand as needed
COUNTRY_SYNONYMS = {
    "UK": ["UK", "Britain", "British", "Great Britain", "Silverstone", "England", "GBR"],
    "Italy": ["Italy", "Italian", "Imola", "Monza", "ITA"],
    "Australia": ["Australia", "Australian", "Melbourne", "AUS"],
    "Bahrain": ["Bahrain", "Sakhir", "BRN"],
    "Saudi Arabia": ["Saudi Arabia", "Jeddah", "KSA", "Saudi"],
    "Japan": ["Japan", "Suzuka", "Japanese", "JPN"],
    "China": ["China", "Shanghai", "Chinese", "CHN"],
    "United States": ["USA", "United States", "Austin", "Miami", "Las Vegas", "US", "America", "United States of America", "COTA", "Texas"],
    "Azerbaijan": ["Azerbaijan", "Baku", "AZE"],
    "Netherlands": ["Netherlands", "Dutch", "Zandvoort", "NED"],
    "Monaco": ["Monaco", "Monte Carlo", "MON"],
    "Canada": ["Canada", "Montreal", "Canadian", "CAN"],
    "Austria": ["Austria", "Spielberg", "Austrian", "Red Bull Ring", "AUT"],
    "Singapore": ["Singapore", "Marina Bay", "SGP"],
    "Hungary": ["Hungary", "Budapest", "Hungarian", "Hungaroring", "HUN"],
    "Belgium": ["Belgium", "Spa", "Spa-Francorchamps", "Belgian", "BEL"],
    "Mexico": ["Mexico", "Mexico City", "Mexican", "MEX"],
    "Brazil": ["Brazil", "Sao Paulo", "Interlagos", "Brazilian", "BRA"],
    "Qatar": ["Qatar", "Lusail", "QAT"],
    "United Arab Emirates": ["Abu Dhabi", "Yas Marina", "UAE", "United Arab Emirates", "Yas Island"],
    # Add more as needed
}

F1_TVDB_SERIES_ID = 387219
API_KEY = os.environ.get('NZBGEEK_API_KEY')
TVDB_SUBSCRIBER_PIN = os.environ.get('TVDB_PIN')
TVDB_API_KEY = os.environ.get('TVDB_KEY')
if not API_KEY or not TVDB_SUBSCRIBER_PIN or not TVDB_API_KEY:
    raise ValueError("Environment variables NZBGEEK_API_KEY, TVDB_PIN, and TVDB_KEY must be set.")
class OpenF1Client:
    def __init__(self, base_url="https://api.openf1.org/v1/"):
        self.base_url = base_url.rstrip("/")

    def get(self, endpoint, params=None):
        """
        Generic GET request to the OpenF1 API with disk caching.
        """
        cache_key = f"openf1_{endpoint.replace('/', '_')}"
        if params:
            param_str = "_".join(f"{k}-{v}" for k, v in sorted(params.items()))
            cache_key += f"_{param_str}"
        cached = cache_get(cache_key)
        if cached is not None:
            return cached
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        cache_set(cache_key, data)
        return data

    def get_sessions(self, year=None, event=None, session_type=None):
        """
        Fetch sessions, optionally filtered by year, event, or session_type.
        """
        params = {}
        if year:
            params["year"] = year
        if event:
            params["event"] = event
        if session_type:
            params["session_type"] = session_type
        return self.get("sessions", params)

    def get_events(self, year=None):
        """
        Fetch events, optionally filtered by year.
        """
        params = {}
        if year:
            params["year"] = year
        return self.get("events", params)

    def get_results(self, session_key):
        """
        Fetch results for a given session_key.
        """
        return self.get(f"results/{session_key}")

    def get_meetings(self, year=None):
        """
        Fetch meetings, optionally filtered by year.
        """
        params = {}
        if year:
            params["year"] = year
        return self.get("meetings", params)
    
class NZBGeekClient:
    def __init__(self, api_key, base_url="https://api.nzbgeek.info/api"):
        self.api_key = api_key
        self.base_url = base_url

    def search(self, query, limit=100, extended=1, total_limit=1000):
        """
        Search NZBGeek for a query string with pagination.
        Returns the parsed JSON response containing up to total_limit items.
        
        Args:
            query (str): Search query
            limit (int): Number of items per page (max 100)
            extended (int): Whether to include extended attributes
            total_limit (int): Maximum total number of results to return
        """
        all_items = []
        offset = 0
        
        while offset < total_limit:
            params = {
                "t": "search",
                "q": query,
                "limit": min(limit, total_limit - offset),
                "offset": offset,
                "extended": extended,
                "o": "json",
                "apikey": self.api_key,
            }
            resp = requests.get(self.base_url, params=params)
            resp.raise_for_status()
            results = resp.json()
            
            # Extract items from the response
            items = results.get("channel", {}).get("item", [])
            if not items:
                break  # No more results
            
            all_items.extend(items)
            offset += len(items)
            
            # If we got fewer items than requested, there are no more results
            if len(items) < params["limit"]:
                break
        
        # Create a response structure similar to the original API
        response = {
            "channel": {
                "item": all_items
            }
        }
        return response

    def search_multiple(self, keywords, total_limit=1000):
        """
        Search NZBGeek for multiple keywords with pagination.
        Returns a list of unique items up to total_limit per keyword.
        """
        all_items = []
        seen_guids = set()
        
        for keyword in keywords:
            search_results = self.search(keyword, total_limit=total_limit)
            for result_item in search_results.get("channel", {}).get("item", []):
                guid = result_item.get("guid")
                if guid and guid not in seen_guids:
                    all_items.append(result_item)
                    seen_guids.add(guid)
        
        return all_items
    
def normalize_name(name):
    """Lowercase and remove non-alphanumeric for fuzzy matching."""
    return ''.join(c for c in name.lower() if c.isalnum())

def extract_info_from_title(title):
    # Normalize and split
    norm = title.replace("_", ".").replace("-", ".").replace(" ", ".")
    parts = [p for p in re.split(r"[.\s]", norm) if p]

    # Year
    year = None
    for part in parts:
        m = re.match(r"(20\d{2})", part)
        if m:
            year = int(m.group(1))
            break

    # Event type
    event_types = [
        "Practice 1", "Practice 2", "Practice 3",
        "FP1", "FP2", "FP3",
        "Qualifying", "Qualy", "Sprint", "Shootout", "Sprint Qualifying", "Sprint Race", "Pre-Race", "Post-Race", "Race"
    ]
    event_type = None
    for et in event_types:
        et_norm = et.lower().replace(" ", "")
        for part in parts:
            part_norm = part.replace(".", "").lower()
            if et_norm == part_norm:
                event_type = et
                break
            # Also match e.g. "practice1" or "practice.1"
            if "practice" in et_norm and part_norm.startswith("practice") and part_norm.replace("practice", "") == et_norm.replace("practice", ""):
                event_type = et
                break
        if event_type:
            break
    if event_type in ["FP1", "FP2", "FP3"]:
        event_type = f"Practice {event_type[-1]}"
    elif event_type == "Qualy":
        event_type = "Qualifying"
    elif "pre-race" in title.lower():
        event_type = "Pre-Race"
    elif "post-race" in title.lower():
        event_type = "Post-Race"
    elif "post-qualifying" in title.lower():
        event_type = "Post-Qualifying"
    elif "pre-qualifying" in title.lower(): 
        event_type = "Pre-Qualifying"
    elif "notebook" in title.lower():
        event_type = "Notebook"
    elif "pre-sprint" in title.lower():       
        event_type = "Pre-Sprint"
    elif "post-sprint" in title.lower():
        event_type = "Post-Sprint"
    # Location/country/track
    location = None
    for country, synonyms in COUNTRY_SYNONYMS.items():
        for syn in synonyms:
            if normalize_name(syn) in normalize_name(title):
                location = country
                break
        if location:
            break
    if not location:
        for i, part in enumerate(parts):
            if re.match(r"Round\d+", part, re.IGNORECASE) and i + 1 < len(parts):
                location = parts[i + 1]
                break
    return {
        "year": year,
        "event_type": event_type,
        "location": location,
        "title": title
    }

def match_title_to_session(title, sessions, min_confidence=70):
    parsed = extract_info_from_title(title)
    if not parsed["year"] or not parsed["event_type"]:
        return None, 0.0, parsed
    if "Pre" in parsed["event_type"] or "Post" in parsed["event_type"]:
        return None, 0.0, parsed
    candidates = []
    for session in sessions:
        # Year must match
        if int(session.get("year", 0)) != parsed["year"]:
            continue

        # Event type fuzzy match (e.g. "Practice 1" vs "Practice 1")
        session_type = session.get("session_type", "")
        session_name = session.get("session_name", "")
        event_score = max(
            fuzz.ratio(normalize_name(parsed["event_type"]), normalize_name(session_type)),
            fuzz.ratio(normalize_name(parsed["event_type"]), normalize_name(session_name))
        )

        # Location/country/circuit fuzzy match
        loc_score = 0
        if parsed["location"]:
            for field in ["location", "country_name", "circuit_short_name"]:
                session_field = session.get(field, "")
                loc_score = max(loc_score, fuzz.ratio(normalize_name(parsed["location"]), normalize_name(session_field)))
        else:
            # Try all synonyms if not found
            for country, synonyms in COUNTRY_SYNONYMS.items():
                for syn in synonyms:
                    for field in ["location", "country_name", "circuit_short_name"]:
                        session_field = session.get(field, "")
                        loc_score = max(loc_score, fuzz.ratio(normalize_name(syn), normalize_name(session_field)))

        # Combine scores (weighted)
        score = 0.6 * event_score + 0.4 * loc_score
        candidates.append((score, session, parsed))

    if not candidates:
        return None, 0.0, parsed

    best_score, best_session, parsed = max(candidates, key=lambda x: x[0])
    if best_score >= min_confidence:
        return best_session, best_score, parsed
    return None, best_score, parsed

def get_tvdb_episodes(series_id, api_token, subscriber_pin):
    """
    Fetch all episodes for a series from TVDB with disk caching, using tvdb_v4_official.
    """
    cache_key = f"tvdb_episodes_{series_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    tvdb = TVDB(api_token, pin=subscriber_pin)

    episodes = []
    page = 0
    while True:
        resp = tvdb.get_series_episodes(series_id, page=page)
        episodes.extend(resp.get("episodes", []))
        if len(resp['episodes']) == 0:
            break
        page += 1
    cache_set(cache_key, episodes)
    return episodes

def extract_practice_number(text):
    """
    Extracts the practice number from a string, e.g., "Practice 3" -> 3
    Returns None if not found.
    """
    m = re.search(r'practice\s*(\d)', text.lower())
    if m:
        return int(m.group(1))
    return None

def match_to_tvdb_episode(combined_data, tvdb_episodes):
    """
    Match a combined F1 event/session to the best TVDB episode.
    Enforces exact match for practice numbers and year.
    For Sprint/Sprint Qualifying, only match to TVDB episodes with 'Sprint' in the title.
    Gives a high score if air date and session date are within 1 week.
    """
    best_score = 0
    best_ep = None
    parsed_event_type = combined_data["parsed"].get("event_type", "")
    parsed_practice_num = extract_practice_number(parsed_event_type)
    parsed_year = combined_data["parsed"].get("year")
    session = combined_data.get("session", {})

    # Parse session date if available
    session_date = None
    session_date_str = session.get("date_end") or session.get("date")
    if session_date_str:
        try:
            session_date = datetime.datetime.fromisoformat(session_date_str.replace("Z", "+00:00")).date()
        except Exception:
            session_date = None

    for ep in tvdb_episodes:
        ep_title = ep.get("name", "") or ""
        ep_airdate = ep.get("aired", "")
        score = 0

        # Enforce exact match for year if available
        ep_year = None
        if ep_airdate and len(ep_airdate) >= 4:
            try:
                ep_year = int(ep_airdate[:4])
            except Exception:
                pass
        if parsed_year and ep_year and parsed_year != ep_year:
            continue  # Skip if years don't match

        # Enforce exact match for practice number if present
        ep_practice_num = extract_practice_number(ep_title)
        if parsed_practice_num is not None:
            if ep_practice_num != parsed_practice_num:
                continue  # Skip if practice numbers don't match

        # Strict event type matching
        event_type_match = False
        pet = parsed_event_type.lower() if parsed_event_type else ""
        et_in_title = ep_title.lower()
        if pet == "race":
            event_type_match = "race" in et_in_title and "sprint" not in et_in_title
        elif pet == "qualifying":
            event_type_match = "qualifying" in et_in_title and "sprint" not in et_in_title
        elif pet == "sprint race":
            event_type_match = "sprint race" in et_in_title
        elif pet == "sprint qualifying":
            event_type_match = "sprint qualifying" in et_in_title
        elif pet.startswith("practice"):
            event_type_match = pet in et_in_title
        else:
            event_type_match = True  # fallback for other types
        if not event_type_match:
            continue  # Skip if event type doesn't match

        # Improved location matching
        location_match = False
        parsed_location = combined_data["parsed"].get("location")
        if parsed_location:
            for syn in COUNTRY_SYNONYMS.get(parsed_location, []):
                if normalize_name(syn) in normalize_name(ep_title):
                    location_match = True
                    break
        if not location_match:
            for key in ["country_code", "country_name", "circuit_short_name"]:
                val = session.get(key)
                if val and normalize_name(val) in normalize_name(ep_title):
                    location_match = True
                    break
        if not location_match:
            continue  # Skip this episode if location doesn't match

        # Fuzzy match on event title and episode title
        if combined_data.get("title"):
            score += fuzz.ratio(normalize_name(combined_data["title"]), normalize_name(ep_title))
        # Fuzzy match on race/country and episode title
        if combined_data["parsed"].get("location"):
            score += fuzz.ratio(normalize_name(combined_data["parsed"]["location"]), normalize_name(ep_title))
        # Fuzzy match on event type and episode title
        if parsed_event_type:
            score += fuzz.ratio(normalize_name(parsed_event_type), normalize_name(ep_title))

        # Match on airdate if available, give high score if within 1 week
        if session_date and ep_airdate:
            try:
                ep_date = datetime.datetime.strptime(ep_airdate, "%Y-%m-%d").date()
                days_diff = abs((session_date - ep_date).days)
                if days_diff == 0:
                    score += 50  # Exact match
                elif days_diff <= 7:
                    score += 40  # Within 1 week
            except Exception:
                pass

        if score > best_score:
            best_score = score
            best_ep = ep

    return best_ep, best_score
def process_result(item, sessions, tvdb_episodes):
    title = item['title']
    session, score, parsed = match_title_to_session(title, sessions)
    if session and score > 0.95:
        combined_data = {
            "parsed": parsed,
            "enclosure": item['enclosure'],
            "entry": item,
            "title": title,
            "description": item['description'],
            "session": session,
            "score": score
        }
        best_ep, ep_score = match_to_tvdb_episode(combined_data, tvdb_episodes)
        combined_data["tvdb_episode"] = best_ep
        combined_data["tvdb_score"] = ep_score
        return combined_data
    return None

def search_f1_releases(season=None, episode=None):
    nzbgeek = NZBGeekClient(API_KEY)
    openf1 = OpenF1Client()
    results = nzbgeek.search_multiple(["f1", "formula1"])
    sessions = openf1.get_sessions()
    tvdb_episodes = get_tvdb_episodes(F1_TVDB_SERIES_ID, TVDB_API_KEY, TVDB_SUBSCRIBER_PIN)
    processed_results = [process_result(item, sessions, tvdb_episodes) for item in results]

    filtered_results = filter(
        lambda x: (x is not None and 
                  x.get("tvdb_episode") is not None and 
                  x.get("tvdb_score", 0) >= 120),
        processed_results
    )
    
    # Return the filtered results
    yield from filtered_results