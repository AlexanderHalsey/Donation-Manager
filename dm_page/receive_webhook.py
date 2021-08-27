from django.db.transaction import atomic
from .models import Profile, Contact, Organisation

@atomic
def process_webhook_payload(payload):
	action = payload["notifications"][0]["action"].split("profile.")[1]
	data = payload["notifications"][0]["payload"]
	try:
		if action == "merge":
			p = Profile.objects.get(seminar_desk_id = data[0]["id"])
		else:
			p = Profile.objects.get(seminar_desk_id = data["id"])
		new = False
	except:
		new = True
		p = Profile()
	finally:
		if action == "delete" and not new:
			return
		elif action == "create" or action == "update" or action == "merge":
			if (action == "create" and not new) or (action == "update" and new) or (action == "merge" and new):
				return 
			if action == "create" or action == "update":
				object_type = data["objectType"]
			if action == "merge":
				object_type = data[0]["objectType"]
				data = data[1]

			p.seminar_desk_id = data["id"]
			p.salutation = data["salutation"]
			p.object_type = data["objectType"]
			p.title = data["title"]
			p.name = data["name"]
			p.language = data["language"]
			p.labels = data["labels"]
			p.email = data["email"]
			p.alternative_email = data["alternativeEmail"]
			p.website = data["website"]
			p.fax_number = data["faxNumber"]
			p.primary_address = data["primaryAddress"]
			p.billing_address_active = data["billingAddressActive"]
			p.billing_address = data["billingAddress"]
			p.remarks = data["remarks"]
			p.information = data["information"]
			p.is_blocked = data["isBlocked"]
			p.blocked_reason = data["blockedReason"]
			p.bank_account_data = data["bankAccountData"]
			p.tax_number = data["taxNumber"]
			p.vat_id = data["vatId"]
			p.customer_number = data["customerNumber"]
			p.additional_fields = data["additionalFields"]
			p.save()
		
			if object_type == "PERSON":
				c = Contact(
					profile = p,
					first_name = data["firstName"],
					last_name = data["lastName"],
					additional_title = data["additionalTitle"],
					date_of_birth = data["dateOfBirth"],
					profession = data["profession"],
					salutation_type = data["salutationType"], 
					private_phone_number = data["privatePhoneNumber"],
					alternative_phone_number = data["alternativePhoneNumber"],
					work_phone_number = data["workPhoneNumber"],
					preferred_address = data["preferredAddress"],
					preferred_email = data["preferredEmail"],
					preferred_phone_number = data["preferredPhoneNumber"],
					is_subscribed_to_newsletter = data["isSubscribedToNewsletter"],
					is_facilitator = data["isFacilitator"],
				)
				c.save()

			elif object_type == "ORGANISATION":
				o = Organisation(
					profile = p,
					additional_name = data["additionalName"],
				)
				o.save()