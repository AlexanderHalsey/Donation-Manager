import requests
from requests.structures import CaseInsensitiveDict
from pathlib import Path
import json

headers = CaseInsensitiveDict()
headers["Accept"] = "application/json"
headers["Content-Type"] = "application/json"
headers["Dms-Webhook-Token"] = "abc123"

path = Path("/Users/alexanderhalsey/Documents/Work/Coding/Django/Donation Manager/tests/json")

for p in path.iterdir():
	with open(p, "r") as jfile:
		payload = json.load(jfile)
		resp = requests.post(
			'https://dmsivy.herokuapp.com/webhooks/7f6qy3IqT5L2x75mFoUkaEdrY9Kuutuu2dzbuxOwcfw/', 
			headers=headers, 
			data=json.dumps(payload)
		)
		print(resp.content.decode())