from celery import shared_task
from .models import *
from collections import defaultdict
import datetime
import io
import json
from time import sleep
from donations.celery import app
import os

# emails
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# receive webhook
from django.utils import timezone
from django.db.transaction import atomic

@shared_task
def send_email(receipt_id, pdf_path, send_to, body, t, cc=None):
	try:
		sleep(t*15)
		s = Paramètre.objects.get(id=4)
		smtp_object = smtplib.SMTP(s.smtp_domain,int(s.smtp_port))
		print("SMTP domain and SMTP port accepted.")
		smtp_object.ehlo()
		smtp_object.starttls()
		smtp_object.ehlo()
		smtp_object.login(s.host_email, s.host_password)
		print("Logged in ok.")
		message = MIMEMultipart()
		message["From"] = s.host_email
		message["To"] = send_to
		if cc not in ("", None):
			message["Cc"] = cc
		message["Subject"] = "Receipt"
		message.attach(MIMEText(body+"\n\n", "plain"))
		with open(pdf_path, "rb") as attachment:
			part = MIMEBase("application", "octet-stream")
			part.set_payload(attachment.read())
			encoders.encode_base64(part)
			part.add_header(
				"Content-Disposition",
				f"attachment; filename={pdf_path.split('/receipts/')[1]}",
			)
			message.attach(part)
		print("PDF file found.")
		text = message.as_string()
		smtp_object.sendmail(s.host_email, send_to, text)
		smtp_object.quit()
		receipt = ReçusFiscaux.objects.get(id=receipt_id)
		if pdf_path.split(".pdf")[0][-6:] == "Annulé":
			receipt.email_cancel = True
		else:
			receipt.email_active = True
		receipt.save()
		return "SENT"
	except:
		return "ERROR"

@shared_task
def email_confirmation(t, lst):
	sleep(t*15+10)
	notification = Paramètre.objects.get(id=4)
	l = []
	for contact_id, receipt_id in lst:
		receipt = ReçusFiscaux.objects.get(id=receipt_id)
		if receipt.email_active or receipt.email_cancel:
			l.append((Contact.objects.get(id=contact_id).profile.email, True))
		else:
			l.append((Contact.objects.get(id=contact_id).profile.email, False))
	notification.email_notification = True
	notification.email_notification_list = l
	notification.save()

@shared_task
@atomic
def process_webhook_payload():
	for stored_value in WebhookLogs.objects.filter(processed=False):
		payload = stored_value.payload
		stored_value.processed = True
		stored_value.save()
		action = payload["notifications"][0]["action"].split("profile.")[1]
		print(action)
		data = payload["notifications"][0]["payload"]

		try:
			if action == "create":
				if type(payload["notifications"]) == list:
					print("A send all function")
					stored_value.delete()
					print("Deleting log for send all function")
					for i in range(len(payload["notifications"])):
						data = payload["notifications"][i]["payload"]
						try:
							p = Profile.objects.get(seminar_desk_id = data["id"])
							print(f"{p.name} exists in database.")
							continue
						except:
							print(f"Creating {data['name']}.")
							p = Profile()
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
							address = [address for key, address in data["primaryAddress"].items()]
							address = list(filter(lambda x: x, [address[1]] + address[5:] + [address[0]] + address[2:5]))
							p.primary_address = str(address)
							print(str(address))
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
							print("Profile created succesfully.")
							object_type = data["objectType"]
							if object_type == "PERSON":
								c = Contact()
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
								print("Contact created successfuly.")
					print("Process complete.") 
					return
				else:
					try:
						p = Profile.objects.get(seminar_desk_id = data["id"])
						print("Profile object found at create.")
						return 
					except:
						print(f"New profile being created for {data['name']}.")
						p = Profile()
						object_type = data["objectType"]
						if object_type == "PERSON":
							c = Contact()
							print("New contact being created.")

			if action == "merge":
				if data[0]["mergeStatus"] == "MERGED":
					merged = 0
					deleted = 1
				else:
					merged = 1
					deleted = 0
				try:
					p_del = Profile.objects.get(seminar_desk_id = data[deleted]["id"])
					print("DELETED profile found for merge.")
				except:
					print("DELETED profile not found for merge.")
					return
				# donations found for old profile
				donations_to_be_appended = Donation.objects.filter(contact__profile = p_del)
				# new profile / contact
				try:
					p = Profile.objects.get(seminar_desk_id = data[merged]["id"])
					print("MERGED profile found for merge.")
				except:
					print("MERGED profile not found for merge.")
					return
				data = data[merged]
				object_type = data["objectType"]
				c = Contact.objects.get(profile = p)
				print("contact found for merge.")
				# redirect donations to merged contact
				for don in donations_to_be_appended:
					don.contact = c
					don.save()
				p_del.delete()
				print("Merged profile with all the donations.")

			if action == "update":
				p = Profile.objects.get(seminar_desk_id = data["id"])
				print("profile found for update.")
				object_type = data["objectType"]
				if object_type == "PERSON":
					c = Contact.objects.get(profile = p)
					print("contact found for update.")

			if action == "delete":
				p = Profile.objects.get(seminar_desk_id = data["id"])
				print("profile found for delete.")
				profile_name = p.name
				linked_dons = Donation.objects.filter(contact__profile = p)
				linked_receipts = ReçusFiscaux.objects.filter(contact__profile = p)
				for receipt in linked_receipts:
					receipt.contact_name = profile_name
					receipt.save()
				p.delete()
				return

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
			print("Profile created successfuly.")

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
				print("Contact created successfuly.")

			print("Message received okay.")
			return 
		except:
			print("Something went wrong.")
			return 


@app.task(name="donations.receipt_trigger_notification")
def annual_receipt_reminder():
	notification = Paramètre.objects.get(id=2)
	if notification.release_date.toordinal() <= datetime.date.today().toordinal():
		date_range = (
			Paramètre.objects.get(id=1).date_range_start, 
			Paramètre.objects.get(id=1).date_range_end
		)
		donations = Donation.objects.filter(disabled=False)\
			.filter(pdf=False)\
			.filter(eligible=True)\
			.filter(date_donated__gte=date_range[0])\
			.filter(date_donated__lte=date_range[1])
		if len(donations) > 0:
			notification.release_notification = True
			notification.save()
		else:
			notification.release_date = datetime.date.fromordinal(notification.release_date.toordinal() + 365)
			notification.save()
			rnge = Paramètre.objects.get(id=1)
			rnge.date_range_start = datetime.date.fromordinal(rnge.date_range_start.toordinal() + 365)
			rnge.date_range_end = datetime.date.fromordinal(rnge.date_range_end.toordinal() + 365)
			rnge.save()
