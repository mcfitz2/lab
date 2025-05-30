import pprint
import re
import xml.etree.ElementTree as ET
from io import BytesIO

from flask import Flask, Response, request
from formula1.matcher import search_f1_releases
from flask_caching import Cache

config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
}
app = Flask(__name__)
# tell Flask to use the above defined config
app.config.from_mapping(config)
cache = Cache(app)
def make_key():
   """A function which is called to derive the key for a computed value.
      The key in this case is the concat value of all the json request
      parameters. Other strategy could to use any hashing function.
   :returns: unique string for which the value should be cached.
   """
   return request.args.get("t", "") + "_" + request.args.get("season", "") + "_" + request.args.get("ep", "")

@app.route("/api")
@cache.cached(timeout=60, make_cache_key=make_key)
def api():
    t = request.args.get("t")
    if t == "caps":
        rss = ET.Element(
            "rss",
            attrib={
                "version": "2.0",
                "xmlns:atom": "http://www.w3.org/2005/Atom",
                "xmlns:torznab": "http://torznab.com/schemas/2015/feed",
            },
        )
        caps = ET.SubElement(rss, "caps")
        ET.SubElement(caps, "server", attrib={"version": "1.0", "title": "Formznab"})
        ET.SubElement(caps, "limits", attrib={"max": "1000", "default": "1000"})
        ET.SubElement(caps, "retention", attrib={"days": "1000"})
        ET.SubElement(caps, "registration", attrib={"available": "no", "open": "no"})
        searching = ET.SubElement(caps, "searching")
        ET.SubElement(searching, "search", attrib={"available": "yes"})
        ET.SubElement(searching, "tv-search", attrib={"available": "yes"})

        categories = ET.SubElement(caps, "categories")
        ET.SubElement(
            categories, "category", attrib={"id": "5000", "name": "Formula 1"}
        )
        f = BytesIO()
        et = ET.ElementTree(caps)
        et.write(f, encoding="utf-8", xml_declaration=True)

        return Response(f.getvalue(), status=200, mimetype="application/xml")
    elif t == "search" or t == "tvsearch":
        rss = ET.Element(
            "rss",
            attrib={
                "version": "2.0",
                "xmlns:atom": "http://www.w3.org/2005/Atom",
                "xmlns:torznab": "http://torznab.com/schemas/2015/feed",
            },
        )
        channel = ET.SubElement(rss, "channel")
        ET.SubElement(channel, "title")
        ET.SubElement(channel, "description")
        episodes = search_f1_releases(
            request.args.get("season"), request.args.get("ep")
        )
        for combined_data in episodes:
            try:
                entry = combined_data["entry"]
                tvdb_episode = combined_data["tvdb_episode"]
                item = ET.SubElement(channel, "item")
                ET.SubElement(item, "title").text = combined_data["title"]
                ET.SubElement(item, "guid").text = entry["guid"]
                ET.SubElement(item, "link").text = entry['link']
                ET.SubElement(item, "enclosure", attrib=combined_data["enclosure"]['@attributes'])
                ET.SubElement(item, "comments").text = entry["comments"]
                ET.SubElement(item, "pubDate").text = entry["pubDate"]
                ET.SubElement(item, "category").text = "Formula 1"
                ET.SubElement(item, "description").text = entry["description"]
                ET.SubElement(
                    item,
                    "torznab:attr",
                    attrib={"name": "season", "value": "S" + str(tvdb_episode["seasonNumber"])},
                )
                ET.SubElement(
                    item,
                    "torznab:attr",
                    attrib={
                        "name": "episode",
                        "value": "E" + str(tvdb_episode["number"]).zfill(3),
                    },
                )
                ET.SubElement(
                    item,
                    "torznab:attr",
                    attrib={"name": "tvdbid", "value": str(tvdb_episode["id"])},
                )

            except KeyError as e:
                print(f"KeyError: {e}")
                pprint.pprint(combined_data)
                continue
        doc = ET.ElementTree(rss)
        f = BytesIO()
        doc.write(f, encoding="utf-8", xml_declaration=True, method="xml")
        return Response(f.getvalue(), status=200, mimetype="application/xml")
    else:
        return Response(status=203)


def main():
    app.run("0.0.0.0", 9999, debug=True)


if __name__ == "__main__":
    main()
