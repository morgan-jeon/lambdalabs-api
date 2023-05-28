#!/usr/bin/python3

import requests, json, sys, os

try:
	import secrets
	API_KEY = secrets.lambdalabs
except:
	API_KEY = os.environ.get('LAMBDA_API_KEY')
	if not API_KEY:
		print("Error, no Key provided.")
		sys.exit()

assert API_KEY

def lambda_api(method, url, data = {}):
	key_header = {"Authorization" : f"Basic {API_KEY}"}
	if method == "GET":
		req = requests.get(url, headers=key_header)
	elif method == "POST":
		req = requests.post(url, headers=key_header, data=json.dumps(data))
	
	return req.content

def check_instance():
	inst_list = json.loads(lambda_api("GET", "https://cloud.lambdalabs.com/api/v1/instances").decode())["data"]
	if len(inst_list) != 0:
		ists = []
		for inst in inst_list:
			ists.append((inst["id"], inst["ip"], inst["instance_type"]["name"], inst["instance_type"]["price_cents_per_hour"]*12))
		return ists
	else:
		return 0

def get_offer():
	reqd = json.loads(lambda_api("GET", "https://cloud.lambdalabs.com/api/v1/instance-types").decode())
	if "data" not in reqd.keys():
		return 1
	offers = reqd["data"]
	insts = []
	for offer in offers:
		inst = offers[offer]	
		name = inst['instance_type']['name']
		price = int(inst['instance_type']['price_cents_per_hour'])*12
		desc = inst['instance_type']['description']
		spec = inst['instance_type']['specs']
		specs = f'{spec["vcpus"]}C, {spec["memory_gib"]}GiB'
		location = inst['regions_with_capacity_available']
		if len(location) != 0:
			insts.append((name, price, desc, specs, location))
	return insts

def create_inst(iname, iloc, inick = ""):
	data = {"region_name": iloc,
    		"instance_type_name": iname,
    		"ssh_key_names": ["MSWIN1207"],
			"file_system_names": [],
    		"quantity": 1,
    		"name": inick
			}
	reqd = json.loads(lambda_api("POST", "https://cloud.lambdalabs.com/api/v1/instance-operations/launch", data).decode())
	if "data" not in reqd.keys():
		return (1, reqd["error"])
	return reqd["data"]["instance_ids"][0]

def get_insts(ids: str):
	reqd = json.loads(lambda_api("GET", f"https://cloud.lambdalabs.com/api/v1/instances/{ids}").decode())
	if "data" not in reqd.keys():
		return (1, reqd["error"])
	return reqd["data"]

if __name__=="__main__":
	if len(sys.argv) < 2 or sys.argv[1] not in ["create", "check", "get", "alert"]:
		print("Usage: \n  lamba.py create\n  lamda.py check\n  lambda.py get\n  lambda.py alert [Instance ID]")
		sys.exit()

	if sys.argv[1] == "create":
		offers = get_offer()
		max_length = max([len(offer[2]) for offer in offers])
		max_length2 = max([len(str(offer[1])) for offer in offers])
		strg = "\n".join([f"{'['+str(n)+']':<{len(offers)}} Name: {offer[2]:<{max_length}}, Cost: {offer[1]:<{max_length2}}, Spec: {offer[3]:<13}" for n, offer in enumerate(offers)])
		print(strg)
		instn = int(input(f"\nEnter number of Instance type: "))
		if input(f"Create Instance {offers[instn][2]} (W{offers[instn][1]}), Proceed? (Y/n): ") not in "Yy":
			print("Aborted. Exit.")
			sys.exit()

		print()
		max_length = max([ len(loc["name"]) for loc in offers[instn][4] ])
		max_length2 = max([ len(loc["description"]) for loc in offers[instn][4] ])
		strg = "\n".join([f'{"["+str(n)+"]":<4} Location: {loc["name"]:<{max_length}}, {loc["description"]:<{max_length2}}' for n, loc in enumerate(offers[instn][4])])
		print(strg)
		locn = int(input("\nEnter number of Location: "))
		inick = input("Enter nickname of Instance: ")
		iname = offers[instn][0]
		iloc = offers[instn][4][locn]["name"]
		print(f"Creating Instance {inick} [{iname}, {iloc}]...")

		insid = create_inst(iname, iloc, inick)
		if isinstance(insid, tuple):
			print(f"Error: {insid[1]}")
			sys.exit()

		insdet = get_insts(insid)
		print(f'Creation complete..!! IP: {insdet["ip"]}, Jupyter: {insdet["jupyter_url"]}')

	elif sys.argv[1] == "check":
		ckc = check_instance()
		if ckc:
			print(ckc)
		else:
			print("Nothing...")

	elif sys.argv[1] == "alert":
		from sms_api import send_alert
		ckc = check_instance()
		if ckc:
			print(ckc)
			alert = []

			if os.path.exists("lambda_alert.json"):
				with open("lambda_alert.json", "r") as f:
					alerted = json.load(f)
					for ist in ckc:
						if ist[0] not in alerted:
							alert.append(ist)
							alerted.append(ist[0])
			else:
				alerted = []

			with open("lambda_alert.json", "w") as f:
				json.dump(alerted, f)
				
			if alert:
				alert_msg = "\n\n".join([f"ID: {ist[0]}\nName: {ist[2]}\nIP: {ist[1]}\nCost: {ist[3]}" for ist in alert])
				print(send_alert(alert_msg, title="Lambda Cloud"))
			
	elif sys.argv[1] == "get":
		insd = get_insts(sys.argv[2])
		if isinstance(insd, tuple):
			print(f"Error: {insd[1]}")
			sys.exit()
		print(f'Name: {insd["name"]}\nType: {insd["instance_type"]["description"]}\nCost: {insd["instance_type"]["price_cents_per_hour"]*12}\nIP:   {insd["ip"]}\nJupyter: {insd["jupyter_url"]}')