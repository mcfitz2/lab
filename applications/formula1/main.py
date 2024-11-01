import re
import xml.etree.ElementTree as ET
from io import BytesIO

from flask import Flask, Response, request
from formula1.feeds import ReleaseFetcher

rss_url = "https://torrentgalaxy.mx/rss?magnet&user=48718"

regex = r"Formula 1\. (?P<year>\d{4})\. R(?P<race_number>.+?)\. (?P<name>.+)\. (?P<broadcaster>.+?)\. (?P<quality>.+)"
desc_regex = r'(?P<category>.+?)\W+Size:\W+(?P<size>\d+\.\d+)\W+(?P<unit>[mktgMKTG][Bb])\W+Added: .+'
app = Flask(__name__)
app.cache = []
app.last_check = None


@app.route("/api")
def api():
    t = request.args.get('t')
    if t == "caps":
        rss = ET.Element("rss", attrib={'version': "2.0",
                                        'xmlns:atom': "http://www.w3.org/2005/Atom",
                                        'xmlns:torznab': "http://torznab.com/schemas/2015/feed"})
        caps = ET.SubElement(rss, 'caps')
        ET.SubElement(caps, "server", attrib={"version": "1.0", "title": "Formznab"})
        ET.SubElement(caps, 'limits', attrib={"max": "1000", "default": "1000"})
        ET.SubElement(caps, 'retention', attrib={"days": "1000"})
        ET.SubElement(caps, 'registration', attrib={"available": "no", "open": "no"})
        searching = ET.SubElement(caps, 'searching')
        ET.SubElement(searching, 'search', attrib={"available": "yes"})
        ET.SubElement(searching, 'tv-search', attrib={"available": "yes"})

        categories = ET.SubElement(caps, 'categories')
        ET.SubElement(categories, 'category', attrib={"id": "5000", "name": "Formula 1"})
        f = BytesIO()
        et = ET.ElementTree(caps)
        et.write(f, encoding='utf-8', xml_declaration=True)

        return Response(f.getvalue(), status=200, mimetype="application/xml")
    elif t == "search" or t == 'tvsearch':
        rss = ET.Element("rss", attrib={'version': "2.0",
                                        'xmlns:atom': "http://www.w3.org/2005/Atom",
                                        'xmlns:torznab': "http://torznab.com/schemas/2015/feed"})
        channel = ET.SubElement(rss, 'channel')
        ET.SubElement(channel, 'title')
        ET.SubElement(channel, 'description')
        episodes = app.fetcher.get_releases(request.args.get('season'), request.args.get('ep'))
        for release, entry, episode in episodes:
            if not entry or not episode:
                continue
            item = ET.SubElement(channel, 'item')
            ET.SubElement(item, 'title').text = entry['title']
            ET.SubElement(item, 'guid').text = entry['guid']
            ET.SubElement(item, 'link').text = entry['links'][0]['href']
            m = re.match(desc_regex, entry['description'])
            if m:
                description_fields = m.groupdict()
                size_num = float(description_fields['size'])
                if description_fields['unit'].lower() == "kb":
                    size = size_num * 1000
                    ET.SubElement(item, 'size').text = str(int(size))
                    ET.SubElement(item, 'enclosure',
                                  attrib={'url': entry['links'][0]['href'], 'type': 'application/x-bittorent',
                                          "size": str(int(size))})
                    ET.SubElement(item, 'torznab:attr',
                                  attrib={"name": "size", "value": str(int(size))})

                elif description_fields['unit'].lower() == "mb":
                    size = size_num * 1000 * 1000
                    ET.SubElement(item, 'size').text = str(int(size))
                    ET.SubElement(item, 'enclosure',
                                  attrib={'url': entry['links'][0]['href'], 'type': 'application/x-bittorent',
                                          "size": str(int(size))})
                    ET.SubElement(item, 'torznab:attr',
                                  attrib={"name": "size", "value": str(int(size))})

                elif description_fields['unit'].lower() == "gb":
                    size = size_num * 1000 * 1000 * 1000
                    ET.SubElement(item, 'size').text = str(int(size))
                    ET.SubElement(item, 'enclosure',
                                  attrib={'url': entry['links'][0]['href'], 'type': 'application/x-bittorent',
                                          "size": str(int(size))})
                    ET.SubElement(item, 'torznab:attr',
                                  attrib={"name": "size", "value": str(int(size))})

                elif description_fields['unit'].lower() == "tb":
                    size = size_num * 1000 * 1000 * 1000 * 1000
                    ET.SubElement(item, 'size').text = str(int(size))
                    ET.SubElement(item, 'enclosure',
                                  attrib={'url': entry['links'][0]['href'], 'type': 'application/x-bittorent',
                                          "size": str(int(size))})
                    ET.SubElement(item, 'torznab:attr',
                                  attrib={"name": "size", "value": str(int(size))})

                else:
                    print(f"found {description_fields['unit'].lower()} unit, unable to calc size")
                    ET.SubElement(item, 'enclosure',
                                  attrib={'url': entry['links'][0]['href'], 'type': 'application/x-bittorent'})
            else:
                print("unable to parse description")
                ET.SubElement(item, 'enclosure',
                              attrib={'url': entry['links'][0]['href'], 'type': 'application/x-bittorent'})
            ET.SubElement(item, 'comments').text = entry['comments']
            ET.SubElement(item, 'pubDate').text = entry['published']
            ET.SubElement(item, 'category').text = "Formula 1"
            ET.SubElement(item, 'description').text = entry['description']
            ET.SubElement(item, 'torznab:attr', attrib={"name": "season", "value": "S" + str(episode['seasonNumber'])})
            ET.SubElement(item, 'torznab:attr',
                          attrib={"name": "episode", "value": "E" + str(episode['number']).zfill(3)})
            ET.SubElement(item, 'torznab:attr', attrib={"name": "tvdbid", "value": str(episode['id'])})
            ET.SubElement(item, 'torznab:attr', attrib={"name": "magneturl", "value": entry['links'][0]['href']})

        doc = ET.ElementTree(rss)
        f = BytesIO()
        doc.write(f, encoding='utf-8', xml_declaration=True, method="xml")
        return Response(f.getvalue(), status=200, mimetype="application/xml")
    else:
        return Response(status=203)


def main():
    app.fetcher = ReleaseFetcher()
    app.run("0.0.0.0", 9999, debug=True)


if __name__ == "__main__":
    main()
