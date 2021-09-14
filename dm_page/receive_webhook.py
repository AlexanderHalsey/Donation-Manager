from django.db.transaction import atomic
from .models import Profile, Contact, Organisation, Donation

@atomic
def process_webhook_payload(payload):
	action = payload["notifications"][0]["action"].split("profile.")[1]
	data = payload["notifications"][0]["payload"]
	messages = []
	try:
		if action == "create":
			if type(data) == list:
				for i in range(len(data)):
					try:
						p = Profile.objects.get(seminar_desk_id = data[i]["id"])
						messages.append(f"{p.name} exists in database.")
						continue
					except:
						messages.append(f"Creating {data[i]['name']}.")
						p = Profile()
						p.seminar_desk_id = data[i]["id"]
						p.salutation = data[i]["salutation"]
						p.object_type = data[i]["objectType"]
						p.title = data[i]["title"]
						p.name = data[i]["name"]
						p.language = data[i]["language"]
						p.labels = str([(["SD_Label",label["id"],label["name"]]) for label in data[i]["labels"]])
						p.email = data[i]["email"]
						p.alternative_email = data[i]["alternativeEmail"]
						p.website = data[i]["website"]
						p.fax_number = data[i]["faxNumber"]
						p.primary_address = str([address for key, address in data[i]["primaryAddress"].items()])
						p.billing_address_active = data[i]["billingAddressActive"]
						p.billing_address = str([address for key, address in data[i]["billingAddress"].items()])
						p.remarks = data[i]["remarks"]
						p.information = data[i]["information"]
						p.is_blocked = data[i]["isBlocked"]
						p.blocked_reason = data[i]["blockedReason"]
						p.bank_account_data = str([d for key, d in data[i]["bankAccountData"].items()])
						p.tax_number = data[i]["taxNumber"]
						p.vat_id = data[i]["vatId"]
						p.customer_number = data[i]["customerNumber"]
						p.additional_fields = str([field for key, field in data[i]["additionalFields"].items()])
						p.save()
						messages.append("Profile created succesfully.")
						object_type = data[i]["objectType"]
						if object_type == "PERSON":
							c = Contact()
							c.profile = p
							c.first_name = data[i]["firstName"]
							c.last_name = data[i]["lastName"]
							c.additional_title = data[i]["additionalTitle"]
							c.date_of_birth = data[i]["dateOfBirth"]
							c.profession = data[i]["profession"]
							c.salutation_type = data[i]["salutationType"] 
							c.private_phone_number = data[i]["privatePhoneNumber"]
							c.alternative_phone_number = data[i]["alternativePhoneNumber"]
							c.work_phone_number = data[i]["workPhoneNumber"]
							c.preferred_address = data[i]["preferredAddress"]
							c.preferred_email = data[i]["preferredEmail"]
							c.preferred_phone_number = data[i]["preferredPhoneNumber"]
							c.is_subscribed_to_newsletter = data[i]["isSubscribedToNewsletter"]
							c.is_facilitator = data[i]["isFacilitator"]
							c.save()
							messages.append(("Contact contact successfuly."))
						elif object_type == "ORGANIZATION":
							o.profile = p
							o.additional_name = data[i]["additionalName"]
							o.save()
				message = ""
				for m in messages:
					message += (m + "\n")
				message += "Message received okay."
				return message 

			else:
				try:
					p = Profile.objects.get(seminar_desk_id = data["id"])
					messages.append("Profile object found at create.")
					return messages
				except:
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
			if data[0]["mergeStatus"] == "MERGED":
				merged = 0
				deleted = 1
			else:
				merged = 1
				deleted = 0
			try:
				p_del = Profile.objects.get(seminar_desk_id = data[deleted]["id"])
				messages.append("DELETED profile found for merge.")
			except:
				messages.append("DELETED profile not found for merge.")
				return messages
			# donations found for old profile
			donations_to_be_appended = Donation.objects.filter(contact__profile = p_del)
			p_del.disabled = True
			p_del.save()
			# new profile / contact
			try:
				p = Profile.objects.get(seminar_desk_id = data[merged]["id"])
				messages.append("MERGED profile found for merge.")
			except:
				messages.append("MERGED profile not found for merge.")
				return messages
			data = data[merged]
			object_type = data["objectType"]
			c = Contact.objects.get(profile = p)
			messages.append("contact found for merge.")
			# redirect donations to merged contact
			for don in donations_to_be_appended:
				don.contact = c
				don.save()
			messages.append("Merged profile with all the donations.")

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
			return messages

		p.seminar_desk_id = data["id"]
		p.salutation = data["salutation"]
		p.object_type = data["objectType"]
		p.title = data["title"]
		p.name = data["name"]
		p.language = data["language"]
		p.labels = str([(["SD_Label",label["id"],label["name"]]) for label in data["labels"]])
		p.email = data["email"]
		p.alternative_email = data["alternativeEmail"]
		p.website = data["website"]
		p.fax_number = data["faxNumber"]
		p.primary_address = str([address for key, address in data["primaryAddress"].items()])
		p.billing_address_active = data["billingAddressActive"]
		p.billing_address = str([address for key, address in data["billingAddress"].items()])
		p.remarks = data["remarks"]
		p.information = data["information"]
		p.is_blocked = data["isBlocked"]
		p.blocked_reason = data["blockedReason"]
		p.bank_account_data = str([d for key, d in data["bankAccountData"].items()])
		p.tax_number = data["taxNumber"]
		p.vat_id = data["vatId"]
		p.customer_number = data["customerNumber"]
		p.additional_fields = str([field for key, field in data["additionalFields"].items()])
		p.save()
		messages.append("Profile created successfuly.")

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
			messages.append("Contact created successfuly.")

		elif object_type == "ORGANIZATION":
			o.profile = p
			o.additional_name = data["additionalName"]
			o.save()
			messages.append("Organisation created successfuly.")

		message = ""
		for m in messages:
			message += (m + "\n")
		message += "Message received okay."
		return message 
	except:
		messages.append("Something went wrong.")
		message = ""
		for m in messages:
			message += (m + "\n")
		return message