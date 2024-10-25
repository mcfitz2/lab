import datetime
import json
from zoneinfo import ZoneInfo

from ics import Calendar, Event






with open('/Users/fmicah/Downloads/paramount.json', 'r') as f:
    data = json.load(f)
    c = Calendar()
    for event in data:
        for performance in event['performances']:
            e = Event()
            parsed_date = datetime.datetime.fromisoformat(performance['iso8601DateString'])
            e.name = f"Paramount: {performance['performanceTitle']}"
            e.begin = parsed_date.replace(tzinfo=ZoneInfo('America/Chicago'))
            e.duration = datetime.timedelta(hours=3)
            e.description = performance['actionUrl']
            c.events.add(e)
    with open('paramount_film.ics', 'w') as cf:
        cf.write(c.serialize())
