import requests
from requests.structures import CaseInsensitiveDict
import json

headers = CaseInsensitiveDict()
headers["Accept"] = "application/json"
headers["Content-Type"] = "application/json"
headers["Dms-Webhook-Token"] = "6f85048b984cdf9a3204ac23c4eb7e2f0cc03a5ec01b4113c77f7b6867d9"

path = "/Users/alexanderhalsey/Documents/Work/Coding/Django/Donation Manager/tests/json/"

with open(path+"profile_person_merge.json", "r") as jfile:
	payload = json.load(jfile)
	resp = requests.post(
		'https://dmsivy.herokuapp.com/webhooks/7f6qy3IqT5L2x75mFoUkaEdrY9Kuutuu2dzbuxOwcfw/', 
		headers=headers, 
		data=json.dumps(payload)
	)
	print(resp.status_code)
	print(resp.content.decode())