from celery import shared_task
from .models import *
from collections import defaultdict
import datetime
import io
import json
from time import sleep
from donations.celery import app
import os

# pdf receipt
from donations.settings import BASE_DIR
import num2words
from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import simpleSplit, ImageReader
from reportlab.pdfbase.ttfonts import TTFont
from textwrap import wrap

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
def create_individual_receipt(receipt, donation, file_name):
	receipt_settings = Organisation.objects.filter(used_for_receipt=True)
	print(donation)
	if len(receipt_settings) > 1:
		print("There is more than one default value")
		print("Something has gone wrong with the save functionality")
	else:
		receipt_settings = receipt_settings[0]
	path = f"{BASE_DIR}/static/pdf/receipts/"
	c = Contact.objects.get(id=donation["contact"])
	# Create pdf
	address = eval(c.profile.primary_address)
	if len(address) == 5:
		address = address[:2]+[address[2]+", "+address[3]]+[address[4]]
	if len(address) == 7:
		address = [address[0]+(", " if address[0] != "" else "")+address[1]]+list(filter(lambda x: x, address[2]))+[address[3]+" "+address[4]]+[address[5]+(", " if address[6] != "" else "")+address[6]]
	text_variables = {
		"institut_address": [
			receipt_settings.institut_title or "", 
			receipt_settings.institut_street_name or "", 
			(receipt_settings.institut_post_code or "") + " " + (receipt_settings.institut_town or "")
		],
		"receipt_id": [str(receipt["id"])],
		"organisation_object": [
			"Object:", 
			receipt_settings.object_title or "", 
			receipt_settings.object_description or ""
		],
		"contact": [c.profile.name or ""], 
		"contact_address": address,
		"date_donated": ["/".join((str(donation["date_donated"]).split("T")[0]).split("-")[::-1])],
		"amount": ["€ "+ str(donation["amount"])],
		"other_donation_variables": [
			num2words.num2words("%.2f"%float(donation["amount"] or 0), lang="fr").capitalize() + " euros", 
			PaymentMode.objects.get(id=donation["payment_mode"]).payment_mode, 
			donation["forme_du_don_name"], 
			donation["nature_du_don_name"],
		], 
		"institut_village": [receipt_settings.institut_town or ""],
		"date_today": ["/".join(str(datetime.date.today()).split("-")[::-1])],
		"president": [receipt_settings.president or ""],
	}
	images = {
		"institution": receipt_settings.institut_image or "",
		"signature": receipt_settings.president_signature or "",
	}
	packet = io.BytesIO()
	can = canvas.Canvas(packet, pagesize=A4)

	pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
	pdfmetrics.registerFont(TTFont('Arial Bold', 'Arial Bold.ttf'))
	pdfmetrics.registerFont(TTFont('Arial Italic', 'Arial Italic.ttf'))
	fonts = ["Arial Bold", "Arial", "Arial Italic"]
	sizes = [12, 16, 18]

	text_matrix = {
		"institut_address": [(0, 0, 143, 700), (1, 0, 143, 680), (1, 0, 143, 665)], 
		"receipt_id": [(0, 2, 470, 782)], 
		"organisation_object": [(0, 0, 38, 615), (1, 0, 88, 615), (1, 0, 32, 590)], 
		"contact": [(0, 0, 200, 500)], 
		"contact_address": [(1, 0, 200, 480), (1, 0, 200, 465), (1, 0, 200, 450), (1, 0, 200, 435)], 
		"date_donated": [(1, 0, 363, 400)], 
		"amount": [(0, 1, 252, 370)], 
		"other_donation_variables": [(2, 0, 206, 337), (2, 0, 182, 322), (2, 0, 151, 307), (2, 0, 152, 293)], 
		"institut_village": [(1, 0, 42, 193)], 
		"date_today": [(1, 0, 124, 193)], 
		"president": [(0, 0, 302, 158)],
	}

	image_matrix = {
		"institution": (45, 565, 80),
		"signature": (310, -55, 100),
	}
	print(text_variables)
	for key,value in text_variables.items():
		for index in range(len(value)):
			t = text_matrix[key][index]
			can.setFont(fonts[t[0]], sizes[t[1]])
			if key=="organisation_object" and index==2:
				textobject = can.beginText(t[2], t[3])
				wrapped_text = "\n".join(wrap(value[index], 100))
				textobject.textLines(wrapped_text)
				can.drawText(textobject)
				continue
			can.drawString(t[2],t[3], value[index])
	for key, value in images.items():
		try:
			img = ImageReader(value)
			can.drawImage(img, image_matrix[key][0], image_matrix[key][1], width=image_matrix[key][2], preserveAspectRatio=True)
		except:
			pass
	can.showPage()
	can.save()
	print("can created.")
	packet.seek(0)
	new_pdf = PdfFileReader(packet)
	existing_pdf = PdfFileReader(open(f"{BASE_DIR}/static/pdf/individual_receipt.pdf", "rb"))
	print("existing template found.")
	output = PdfFileWriter()
	page = existing_pdf.getPage(0)
	page.mergePage(new_pdf.getPage(0))
	output.addPage(page)
	outputStream = open(path + file_name, "wb")
	print("outputStream created")
	output.write(outputStream)
	outputStream.close()
	print("outputStream saved.")
	return

@shared_task
def create_annual_receipt(receipt, contact, donations, date_range, file_name):
	receipt_settings = Organisation.objects.filter(used_for_receipt=True)
	if len(receipt_settings) > 1:
		print("There is more than one default value")
		print("Something has gone wrong with the save functionality")
	else:
		receipt_settings = receipt_settings[0]
	path = f"{BASE_DIR}/static/pdf/receipts/"
	p = Profile.objects.get(id=contact["profile"])
	# Create pdf
	address = eval(p.primary_address)
	if len(address) == 5:
		address = address[:2]+[address[2]+", "+address[3]]+[address[4]]
	if len(address) == 7:
		address = [address[0]+(", " if address[0] != "" else "")+address[1]]+list(filter(lambda x: x, address[2]))+[address[3]+" "+address[4]]+[address[5]+(", " if address[6] != "" else "")+address[6]]
	text_variables = {
		"institut_address": [
			receipt_settings.institut_title or "", 
			receipt_settings.institut_street_name or "", 
			(receipt_settings.institut_post_code or "") + " " + (receipt_settings.institut_town or "")
		],
		"receipt_id": [str(receipt["id"])],
		"organisation_object": [
			"Object:", 
			receipt_settings.object_title or "", 
			receipt_settings.object_description or ""
		],
		"contact": [p.name], 
		"contact_address": address,
		"date_start": ["/".join((str(date_range[0]).split("T")[0]).split("-")[::-1])],
		"date_end": ["/".join((str(date_range[1]).split("T")[0]).split("-")[::-1])],
		"total_amount": ["€ "+ str("%.2f"%sum([float(d["amount"]) for d in donations]))],
		"in_letters": [num2words.num2words("%.2f"%sum([float(d["amount"]) for d in donations]), lang="fr").capitalize() + " euros"], 
			}
	images = {
		"institution": receipt_settings.institut_image or "",
		"president_signature": receipt_settings.president_signature or "",
	}
	packet = io.BytesIO()
	can = canvas.Canvas(packet, pagesize=A4)

	pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
	pdfmetrics.registerFont(TTFont('Arial Bold', 'Arial Bold.ttf'))
	pdfmetrics.registerFont(TTFont('Arial Italic', 'Arial Italic.ttf'))
	fonts = ["Arial Bold", "Arial", "Arial Italic"]
	sizes = [12, 16, 18, 10, 11]

	text_matrix = {
		"institut_address": [(0, 0, 143, 695), (1, 0, 143, 675), (1, 0, 143, 660)], 
		"receipt_id": [(0, 2, 475, 773)], 
		"organisation_object": [(0, 0, 51, 610), (1, 0, 101, 610), (1, 0, 51, 590), (1, 0, 51, 575), (1, 0, 51, 560)], 
		"contact": [(0, 0, 200, 500)], 
		"contact_address": [(1, 0, 200, 480), (1, 0, 200, 465), (1, 0, 200, 450), (1, 0, 200, 435)], 
		"date_start": [(1, 0, 434, 379)], 
		"date_end": [(1, 0, 74, 352)], 
		"total_amount": [(0, 1, 286, 353)], 
		"in_letters": [(2, 0, 222, 324)],
	}

	for key,value in text_variables.items():
		for index in range(len(value)):
			if key == "date_today":
				continue
			t = text_matrix[key][index]
			can.setFont(fonts[t[0]], sizes[t[1]])
			if key=="organisation_object" and index==2:
				textobject = can.beginText(t[2], t[3])
				wrapped_text = "\n".join(wrap(value[index], 90))
				textobject.textLines(wrapped_text)
				can.drawText(textobject)
				continue
			can.drawString(t[2],t[3], value[index])
	try:
		img = ImageReader(images["institution"])
		can.drawImage(img, 49, 555, width=80, preserveAspectRatio=True)
	except:
		pass

	can.grid([69, 150, 232, 367, 450, 515],[274]+[246-(y*18) for y in range(len(donations[:9])+1)])
	can.setFont(fonts[0], sizes[4])
	can.drawString(79, 256, "Date du Don")
	can.drawString(168, 262, "Mode de")
	can.drawString(166, 250, "Paiement")
	can.drawString(268, 256, "Forme du Don")
	can.drawString(378, 262, "Nature du")
	can.drawString(392, 250, "Don")
	can.drawString(460, 256, "Montant")

	can.setFont(fonts[2], sizes[3])
	for index, donation in enumerate(donations):
		if index == 9:
			break
		can.drawString(79, 235-(index*18), " / ".join((str(donation["date_donated"]).split("T")[0]).split("-")[::-1]))
		can.drawString(156, 235-(index*18), PaymentMode.objects.get(id=donation["payment_mode"]).payment_mode or "")
		can.drawString(239, 235-(index*18), donation["forme_du_don_name"])
		can.drawString(377, 235-(index*18), donation["nature_du_don_name"])
		can.drawString(460, 235-(index*18), "€ " + str(donation["amount"]))
	can.showPage()
	can.save()
	packet.seek(0)
	new_pdf = PdfFileReader(packet)

	packet2 = io.BytesIO()
	can2 = canvas.Canvas(packet2, pagesize=A4)
	if len(donations) > 9:
		can2.grid([69, 154, 232, 367, 438, 515],[778-(y*18) for y in range(len(donations[9:])+1)])
		can2.setFont(fonts[2], sizes[3])
		for index, donation in enumerate(donations[9:]):
			can2.drawString(79, 767-(index*18), " / ".join((str(donation["date_donated"]).split("T")[0]).split("-")[::-1]))
			can2.drawString(168, 767-(index*18), PaymentMode.objects.get(id=donation["payment_mode"]).payment_mode)
			can2.drawString(239, 767-(index*18), donation["forme_du_don_name"])
			can2.drawString(377, 767-(index*18), donation["nature_du_don_name"])
			can2.drawString(450, 767-(index*18), "€ " + str(donation["amount"]))
	try:
		img2 = ImageReader(str(BASE_DIR)+"/static/png/end_of.png")
		if len(donations) > 9:
			additional = (len(donations[9:]))*18
			if additional != 0:
				additional += 50
		else:
			additional = 0
		can2.drawImage(img2, 43, 492-additional, width=506, preserveAspectRatio=True)
	except:
		pass
	can2.showPage()
	can2.save()
	packet2.seek(0)
	new_pdf2 = PdfFileReader(packet2)

	packet3 = io.BytesIO()
	can3 = canvas.Canvas(packet3, pagesize=A4)
	can3.setFont(fonts[1], sizes[0])
	can3.drawString(52, 734-additional, "A "+(receipt_settings.institut_town or "")+" le :")
	can3.drawString(142, 734-additional, "/".join(str(datetime.date.today()).split("-")[::-1]))
	can3.drawString(305, 583-additional, (receipt_settings.president or ""))
	try:
		img3 = ImageReader(images["president_signature"])
		can3.drawImage(img3, 310, 483-additional, width=100, preserveAspectRatio=True)
	except:
		pass
	can3.showPage()
	can3.save()
	packet3.seek(0)
	new_pdf3 = PdfFileReader(packet3)

	existing_pdf = PdfFileReader(open(f"{BASE_DIR}/static/pdf/annual_receipt.pdf", "rb"))
	output = PdfFileWriter()
	page = existing_pdf.getPage(0)
	page.mergePage(new_pdf.getPage(0))
	page2 = existing_pdf.getPage(1)
	page2.mergePage(new_pdf2.getPage(0))
	page2.mergePage(new_pdf3.getPage(0))
	output.addPage(page)
	output.addPage(page2)
	outputStream = open(path + file_name, "wb")
	output.write(outputStream)
	outputStream.close()
	return

@shared_task
def cancel_pdf_receipt(path):
	# this also needs to include anual pdf_receipts !!!
	# only considering individual receipts at the moment
	packet = io.BytesIO()
	can = canvas.Canvas(packet, pagesize=A4)
	img = ImageReader(str(BASE_DIR)+"/static/png/LOGO-ANNULÉ.png")
	can.drawImage(img, -100, 400, width=800, preserveAspectRatio=True, mask='auto')
	can.showPage()
	can.save()
	packet.seek(0)
	new_pdf = PdfFileReader(packet)
	existing_pdf = PdfFileReader(open(f"{path}", "rb"))
	output = PdfFileWriter()
	for i in range(existing_pdf.getNumPages()):
		page = existing_pdf.getPage(i)
		page.mergePage(new_pdf.getPage(0))
		output.addPage(page)
	new_path = path.split("/receipts/")[1].split(".pdf")
	new_path.insert(1, "_Annulé.pdf")
	new_path = "".join(new_path)
	new_path = path.split("/receipts/")[0] + "/receipts/" + new_path
	outputStream = open(f"{new_path}", "wb")
	output.write(outputStream)
	outputStream.close()
	os.remove(f"{path}")
	return new_path.split("/receipts/")[1]

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
							p.primary_address = str([address for key, address in data["primaryAddress"].items()])
							print(data["primaryAddress"])
							print(str([address for key, address in data["primaryAddress"].items()]))
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
						print("New profile being created.")
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
