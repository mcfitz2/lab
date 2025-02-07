import chevron
import pprint
import os
import yaml
script_dir = os.path.dirname(__file__)
with open(os.path.join(script_dir, "values.yml"), "r") as stream:
    try:
        config = yaml.safe_load(stream)
        config['places'] = [{"region":place.get('region'), 'continent':place['continent'], 'country':place['country'], 'depends_on':config['places'][index-1] if index > 0 else None} for index, place in enumerate(config['places'])]
#        pprint.pprint(config)

        #pprint.pprint(config)
	
        with open(os.path.join(script_dir, 'template.yml'), 'r') as template:
                with open('docker-compose.yml', 'w') as output:
                    output.write(chevron.render(template, config))

    except yaml.YAMLError as exc:
        print(exc)
