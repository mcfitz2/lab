import math
import geojson
from shapely.geometry import shape
import json
import base64
import requests
def deg2rad(degrees):
    return math.pi*degrees/180.0
def rad2deg(radians):
    return 180.0*radians/math.pi

WGS84_a = 6378137.0  
WGS84_b = 6356752.3  

def WGS84EarthRadius(lat):
    An = WGS84_a*WGS84_a * math.cos(lat)
    Bn = WGS84_b*WGS84_b * math.sin(lat)
    Ad = WGS84_a * math.cos(lat)
    Bd = WGS84_b * math.sin(lat)
    return math.sqrt( (An*An + Bn*Bn)/(Ad*Ad + Bd*Bd) )


def boundingBox(latitudeInDegrees, longitudeInDegrees, halfSideInKm):
    lat = deg2rad(latitudeInDegrees)
    lon = deg2rad(longitudeInDegrees)
    halfSide = 1000*halfSideInKm
    radius = WGS84EarthRadius(lat)
    pradius = radius*math.cos(lat)
    latMin = lat - halfSide/radius
    latMax = lat + halfSide/radius
    lonMin = lon - halfSide/pradius
    lonMax = lon + halfSide/pradius

    return (rad2deg(latMin), rad2deg(lonMin), rad2deg(latMax), rad2deg(lonMax))

def geojson_to_geography(geo):
    g = geojson.loads(json.dumps(geo))
    s = shape(g)
    return s.wkt

def download_img_to_base64(url):
    return base64.b64encode(requests.get(url).content)