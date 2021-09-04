from django.db.transaction import atomic
from .models import Profile, Contact, Organisation

@atomic
def process_webhook_payload(payload):
	action = payload["notifications"][0]["action"].split("profile.")[1]
	data = payload["notifications"][0]["payload"]
	messages = []
	try:
		if action == "create":
			try:
				p = Profile.objects.get(seminar_desk_id = data["id"])
				messages.append("Profile object found at create.")
				return
			except:
				pass
			finally:
				messages.append("new profile being created.")
				p = Profile()
				object_type = data["objectType"]
				if object_type == "PERSON":
					c = Contact()
					messages.append("new contact being created.")
				elif object_type == "ORGANIZATION":
					o = Organisation()
					messages.append("new organisation being created.")
		if action == "merge":
			p = Profile.objects.get(seminar_desk_id = data[0]["id"])
			messages.append("old profile found for merge.")
			# Do nothing: acting as an update
			data = data[1]
			messages.append("new profile to be processed.")
			object_type = data["objectType"]
			if object_type == "PERSON":
				c = Contact.objects.get(profile = p)
				messages.append("contact found for merge.")
			elif object_type == "ORGANIZATION":
				o = Organisation.objects.get(profile = p)
				messages.append("organisation found for merge.")
		if action == "update":
			p = Profile.objects.get(seminar_desk_id = data["id"])
			messages.append("profile found for update.")
			object_type = data["objectType"]
			if object_type == "PERSON":
				c = Contact.objects.get(profile = p)
				messages.append("contact found for update.")
			elif object_type == "ORGANIZATION":
				o = Organisation.objects.get(profile = p)
				messages.append("organisation found for update.")
		if action == "delete":
			p = Profile.objects.get(seminar_desk_id = data["id"])
			messages.append("profile found for delete.")
			p.disabled = True
			p.save()
			return

		p.seminar_desk_id = data["id"]
		p.salutation = data["salutation"]
		p.object_type = data["objectType"]
		p.title = data["title"]
		p.name = data["name"]
		p.language = data["language"]
		p.labels = [label for key, label in data["labels"].items()]
		p.email = data["email"]
		p.alternative_email = data["alternativeEmail"]
		p.website = data["website"]
		p.fax_number = data["faxNumber"]
		p.primary_address = [address for key, address in data["primaryAddress"].items()]
		p.billing_address_active = data["billingAddressActive"]
		p.billing_address = [address for key, address in data["billingAddress"].items()]
		p.remarks = data["remarks"]
		p.information = data["information"]
		p.is_blocked = data["isBlocked"]
		p.blocked_reason = data["blockedReason"]
		p.bank_account_data = [d for key, d in data["bankAccountData"].items()]
		p.tax_number = data["taxNumber"]
		p.vat_id = data["vatId"]
		p.customer_number = data["customerNumber"]
		p.additional_fields = [field for key, field in data["additionalFields"].items()]
		p.save()

		if object_type == "PERSON":
			c.profile = p
			c.first_name = data["firstName"]
			c.last_name = data["lastName"]
			c.additional_title = data["additionalTitle"]
			c.date_of_birth = data["dateOfBirth"]
			c.profession = data["profession"]
			c.salutation_type = data["salutationType"] 
			c.private_phone_number = data["privatePhoneNumber"]
			c.alternative_phone_number = data["alternativePhoneNumber"]
			c.work_phone_number = data["workPhoneNumber"]
			c.preferred_address = data["preferredAddress"]
			c.preferred_email = data["preferredEmail"]
			c.preferred_phone_number = data["preferredPhoneNumber"]
			c.is_subscribed_to_newsletter = data["isSubscribedToNewsletter"]
			c.is_facilitator = data["isFacilitator"]
			c.save()

		elif object_type == "ORGANIZATION":
			o.profile = p
			o.additional_name = data["additionalName"]
			o.save()

		message = ""
		for m in messages:
			message += (m + "\n")
		return message 
	except:
		messages.append("Something went wrong.")
		message = ""
		for m in messages:
			message += (m + "\n")
		return message