import os, yaml

original_dir = "/opt/magic_mirror"
os.chdir(original_dir)
try:
	os.mkdir("modules")
except:
	pass

with open("modules.yaml", "r") as stream:
	try:
		modules = yaml.safe_load(stream)
		for module in modules['modules']:
			url = module['url']
			branch = module.get('branch', 'master')
			module_name = url.split('/')[-1].split('.git')[0]
			print(f"Cloning {module_name}")
			if os.path.exists("modules/"+module_name):
				os.chdir("modules/"+module_name)
				os.system(f"git pull origin {branch}")
			else:
				os.chdir("modules/")
				os.system(f"git clone -b {branch} {url} {module_name}")
				os.chdir(module_name)
			os.system("npm install")
			os.chdir(original_dir)

	except yaml.YAMLError as exc:
		print(exc)
