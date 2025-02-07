import requests
import pprint

URL = "https://download.geofabrik.de/north-america/us.poly"

resp = requests.get(URL)
name = None
for line in resp.text.splitlines():
	print(line)
	geometry = {"properties":{}, "type": "Polygon", "coordinates": [ ]}
	started = False
	if line == "END":
		started = False
		print("ENDed")
	elif name == None:
		name = line
		print("Name", name)
	elif line.strip().isdigit():
		print("Started")
		started = True
	elif started:
		print("COORDS", line.split(' '))



