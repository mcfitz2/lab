import polytogeojson from 'polytogeojson'
import got from 'got'
import PolygonLookup from 'polygon-lookup'
import yaml from 'js-yaml'
import fs from 'fs'
import bodyParser from 'body-parser'
import proxy from 'express-http-proxy'
import express from 'express'

async function loadPoly(continent, country, region) {
   try {
        let response = null;
	if (region) {
	        response = await got(`https://download.geofabrik.de/${continent}/${country}/${region}.poly`);
	} else {
	        response = await got(`https://download.geofabrik.de/${continent}/${country}.poly`);
	}
	let polyJson = polytogeojson(response.body);
        return polyJson
    } catch (error) {
        console.log(`Could not get poly file ${continent} ${country} ${region}`);
        //=> 'Internal server error ...'
        return null;
    }
}


async function createLookup() {
	try {
	  	const doc = yaml.load(fs.readFileSync('/values.yml', 'utf8'));
	  	let features = await Promise.all(doc.places.map(async (place) => {
	  		let featureCollection = await loadPoly(place.continent, place.country, place.region);
			if (featureCollection == null) {
				return null;
			}
			let feature = featureCollection.features[0]
			if (place.region) {
				feature.properties = {baseUrl:`http://nominatim-${place.continent}-${place.country}-${place.region}:8080`}
			} else {
				feature.properties = {baseUrl:`http://nominatim-${place.continent}-${place.country}:8080`}
			}
			return feature
		}));
		let featureCollection = {
			type: "featureCollection",
			features: features.filter((feature) => {return feature != null})
		}
		console.log(featureCollection.features);
		return new PolygonLookup( featureCollection );			
	  } catch (e) {
	//	console.log(e);
		return null;
	  }
}


// Constants
const PORT = 8080;
const HOST = '0.0.0.0';

// App


(async () => {
	let lookup = await createLookup();
	const app = express();
//	app.use(bodyParser.urlencoded({ extended: false }));
//	app.use(bodyParser.json());
	app.get('/reverse', async (req, res) => {
		let lat = req.query.lat;
	    	let lon = req.query.lon;
                console.log(`Got request for ${lat}, ${lon}`)
    		let feature = lookup.search(lon, lat)
	    	if (feature) {
                        console.log(req.query);
			let baseUrl = feature.properties.baseUrl
			let params = req.query;
			params['format'] = "jsonv2"
		    	let response = await got({url:`${baseUrl}/reverse`, searchParams:params})
	    		res.send(response.body)
		} else {
			res.send(404);
		}
	});
	app.listen(PORT, HOST, () => {
  		console.log(`Running on http://${HOST}:${PORT}`);
	});
})();
