from celery import shared_task
from .models import *
from . import utils
from collections import defaultdict
import datetime
import io
import json
from time import sleep
from donations.celery import app
import os
import traceback

# pdf receipt
from donations.settings import BASE_DIR, DROPBOX_OAUTH2_TOKEN, ADMIN_EMAIL
import dropbox
import num2words
from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import simpleSplit, ImageReader
from reportlab.pdfbase.ttfonts import TTFont
from textwrap import wrap

# emails
from django.utils import timezone
import pytz
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# receive webhook
from django.db.transaction import atomic


@shared_task
def create_individual_receipt(receipt_id, donation_id, file_name):
	try:
		receipt_settings = Organisation.objects.filter(used_for_receipt=True)
		donation = Donation.objects.get(id=donation_id)
		if len(receipt_settings) > 1:
			print("There is more than one default value")
			print("Something has gone wrong with the save functionality")
		else:
			receipt_settings = receipt_settings[0]
		receipt = ReçusFiscaux.objects.get(id=receipt_id)
		c = donation.contact
		# Create pdf
		address = utils.format_address(c.profile.primary_address)
		text_variables = {
			"institut_address": [
				receipt_settings.institut_title or "", 
				receipt_settings.institut_street_name or "", 
				(receipt_settings.institut_post_code or "") + " " + (receipt_settings.institut_town or "")
			],
			"receipt_id": [str(receipt_id)],
			"organisation_object": [
				"Object:", 
				receipt_settings.object_title or "", 
				receipt_settings.object_description or ""
			],
			"contact": [c.profile.name or ""], 
			"contact_address": address,
			"date_donated": ["/".join(str(donation.date_donated).split("-")[::-1])],
			"amount": [str(donation.amount) + " €"],
			"other_donation_variables": [
				num2words.num2words("%.2f"%float(donation.amount or 0), lang="fr").capitalize() + " euros", 
				donation.payment_mode_name, 
				donation.forme_du_don_name, 
				donation.nature_du_don_name,
			], 
			"institut_village": [f"A {receipt_settings.institut_town or '                 '} le : {'/'.join(str(datetime.date.today()).split('-')[::-1])}"],
			"president": [receipt_settings.president or ""],
			"president_position": [receipt_settings.president_position],
		}
		images = {
			"institution": receipt_settings.institut_image or "",
			"signature": receipt_settings.president_signature or "",
		}
		print(images["institution"])
		packet = io.BytesIO()
		can = canvas.Canvas(packet, pagesize=A4)
		print("can created.")
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
			"date_donated": [(1, 0, 369, 400)], 
			"amount": [(0, 1, 252, 370)], 
			"other_donation_variables": [(2, 0, 206, 337), (2, 0, 182, 322), (2, 0, 151, 307), (2, 0, 152, 293)],
			"institut_village": [(1, 0, 40, 200)],
			"president": [(0, 0, 302, 158)],
			"president_position": [(1, 0, 302, 143)], 
		}

		image_matrix = {
			"institution": (45, 655, 80, 65), # <-- x, y, max-width, max-height
			"signature": (310, 65, 100, 70),
		}
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

		dbx = dropbox.Dropbox(DROPBOX_OAUTH2_TOKEN)

		for key, value in images.items():
			downloaded_file = dbx.files_download(str(value))
			img = ImageReader(downloaded_file[1].raw)
			w, h = img.getSize()
			r = h/w
			if image_matrix[key][2]*r < image_matrix[key][3]:
				w, h = image_matrix[key][2], int(image_matrix[key][2]*r)
			else:
				w, h = int(image_matrix[key][3]/r), image_matrix[key][3]
			can.drawImage(img, image_matrix[key][0], image_matrix[key][1], width=w, height=h)

		can.showPage()
		can.save()
		print("variables appended to can.")
		packet.seek(0)
		new_pdf = PdfFileReader(packet)
		existing_pdf = PdfFileReader(open(f"{BASE_DIR}/static/pdf/individual_receipt.pdf", "rb"))
		print("existing file found for base layer.")
		output = PdfFileWriter()
		page = existing_pdf.getPage(0)
		page.mergePage(new_pdf.getPage(0))
		print("merge succesful")
		output.addPage(page)
		print("new dropbox instance created ok")
		with open(file_name, "wb+") as outputStream:
			output.write(outputStream)
			outputStream.seek(0)
			bin_data = outputStream.read()
		dbx.files_upload(bin_data, f"/media/reçus/{file_name}")
		print("New file saved to DropBox.")
		os.remove(file_name)
	except Exception:
		send_task_error.delay("DMS: Create Indivdual Receipt Error", traceback.format_exc())
	return

@shared_task
def create_annual_receipt(receipt_id, contact_id, donation_lst, date_range, file_name):
	try:
		receipt_settings = Organisation.objects.filter(used_for_receipt=True)
		receipt = ReçusFiscaux.objects.get(id=receipt_id)
		contact = Contact.objects.get(id=contact_id)
		donations = Donation.objects.filter(id__in = donation_lst)
		if len(receipt_settings) > 1:
			print("There is more than one default value")
			print("Something has gone wrong with the save functionality")
		else:
			receipt_settings = receipt_settings[0]
		path = f"{BASE_DIR}/media/pdf/receipts/"
		p = contact.profile
		# Create pdf
		address = utils.format_address(p.primary_address)
		text_variables = {
			"institut_address": [
				receipt_settings.institut_title or "", 
				receipt_settings.institut_street_name or "", 
				(receipt_settings.institut_post_code or "") + " " + (receipt_settings.institut_town or "")
			],
			"receipt_id": [str(receipt_id)],
			"organisation_object": [
				"Object:", 
				receipt_settings.object_title or "", 
				receipt_settings.object_description or ""
			],
			"contact": [p.name], 
			"contact_address": address,
			"date_start": ["/".join(date_range[0].split("-")[::-1])],
			"date_end": ["/".join(date_range[1].split("-")[::-1])],
			"total_amount": [str("%.2f"%sum([float(d.amount) for d in donations])) + " €"],
			"in_letters": [num2words.num2words("%.2f"%sum([float(d.amount) for d in donations]), lang="fr").capitalize() + " euros"], 
				}
		images = {
			"institution": receipt_settings.institut_image or "",
			"president_signature": receipt_settings.president_signature or "",
		}
		packet = io.BytesIO()
		can = canvas.Canvas(packet, pagesize=A4)
		print("can created.")
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

		dbx = dropbox.Dropbox(DROPBOX_OAUTH2_TOKEN)

		downloaded_file = dbx.files_download(str(images["institution"]))
		img = ImageReader(downloaded_file[1].raw)
		w, h = img.getSize()
		r = h/w
		if 80*r < 65:
			w, h = 80, int(80*r)
		else:
			w, h = int(65/r), 65
		can.drawImage(img, 55, 645, width=w, height=h)

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
			can.drawString(79, 234-(index*18), " / ".join(str(donation.date_donated).split("-")[::-1]))
			can.drawString(156, 234-(index*18), donation.payment_mode_name or "")
			can.drawString(239, 234-(index*18), donation.forme_du_don_name)
			can.drawString(377, 234-(index*18), donation.nature_du_don_name)
			can.drawString(460, 234-(index*18), str(donation.amount) + " €")
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
				can2.drawString(79, 767-(index*18), " / ".join(str(donation.date_donated).split("-")[::-1]))
				can2.drawString(168, 767-(index*18), donation.payment_mode_name)
				can2.drawString(239, 767-(index*18), donation.forme_du_don_name)
				can2.drawString(377, 767-(index*18), donation.nature_du_don_name)
				can2.drawString(450, 767-(index*18), str(donation.amount)) + " €" 
			additional = (len(donations[9:]))*18
			if additional != 0:
				additional += 50
		else:
			additional = 0
		# draw line
		can2.setLineWidth(1)
		can2.line(41, 806-additional, 552, 806-additional)
		can2.setFont(fonts[1], sizes[0])
		final_clause = "Le bénéficiare certifie sur l'honneur que les dons et versements qu'il reçoit ouvrent droit à la réduction d'impôt prévue à l'article 200 du CGI, 238 bis du CGI, 885-0 V bis A."
		textobject2 = can2.beginText(51, 783-additional)
		wrapped_text2 = "\n".join(wrap(final_clause, 94))
		textobject2.textLines(wrapped_text2)
		can2.drawText(textobject2)
		can2.setFont(fonts[0], sizes[0])
		can2.drawString(305, 693-additional, (receipt_settings.president or ""))
		can2.setFont(fonts[1], sizes[0])
		can2.drawString(305, 678-additional, receipt_settings.president_position)
		can2.drawString(52, 734-additional, f"A {receipt_settings.institut_town or '                 '} le : {'/'.join(str(datetime.date.today()).split('-')[::-1])}")

		downloaded_file = dbx.files_download(str(images["president_signature"]))
		img = ImageReader(downloaded_file[1].raw)
		w, h = img.getSize()
		r = h/w
		if 100*r < 70:
			w, h = 100, int(100*r)
		else:
			w, h = int(70/r), 70
		can2.drawImage(img, 310, 595-additional, width=w, height=h)

		can2.showPage()
		can2.save()
		print("variables appended to can.")
		packet2.seek(0)
		new_pdf2 = PdfFileReader(packet2)

		existing_pdf = PdfFileReader(open(f"{BASE_DIR}/static/pdf/annual_receipt.pdf", "rb"))
		print("existing file found for base layer.")
		output = PdfFileWriter()
		page = existing_pdf.getPage(0)
		page.mergePage(new_pdf.getPage(0))
		page2 = existing_pdf.getPage(1)
		page2.mergePage(new_pdf2.getPage(0))
		print("merge successful")
		output.addPage(page)
		output.addPage(page2)
		print("new dropbox instance created ok")
		with open(file_name, "wb+") as outputStream:
			output.write(outputStream)
			outputStream.seek(0)
			bin_data = outputStream.read()
		dbx.files_upload(bin_data, f"/media/reçus/{file_name}")
		print("New file saved to DropBox.")
		os.remove(file_name)
	except Exception:
		send_task_error.delay("DMS: Create Annual Receipt Error", traceback.format_exc())
	return

@shared_task
def cancel_pdf_receipt(path, receipt_id):
	try:
		# this also needs to include anual pdf_receipts !!!
		# only considering individual receipts at the moment
		packet = io.BytesIO()
		can = canvas.Canvas(packet, pagesize=A4)
		print("new can created")
		img = ImageReader(f"{BASE_DIR}/static/png/LOGO-ANNULÉ.png")
		can.drawImage(img, -100, 400, width=800, preserveAspectRatio=True, mask='auto')
		can.showPage()
		can.save()
		print("variable added.")
		packet.seek(0)
		new_pdf = PdfFileReader(packet)
		# need to do tests to make sure this part is working ok
		dbx = dropbox.Dropbox(DROPBOX_OAUTH2_TOKEN)
		downloaded_file = dbx.files_download(path)
		existing_pdf = PdfFileReader(io.BytesIO(downloaded_file[1].content))
		dbx.files_delete(path) # <-- This will delete the file that was found to be replaced by a "cancelled" version
		print("Active receipt deleted.")
		output = PdfFileWriter()
		for i in range(existing_pdf.getNumPages()):
			page = existing_pdf.getPage(i)
			page.mergePage(new_pdf.getPage(0))
			output.addPage(page)
		file_name = path.split("/reçus/")[1].split(".pdf")[0] + "_Annulé.pdf"
		# upload canceled file
		with open(file_name, "wb+") as outputStream:
			output.write(outputStream)
			outputStream.seek(0)
			bin_data = outputStream.read()
		dbx.files_upload(bin_data, f'/media/reçus/{file_name}') # <-- cancelled receipt to be uploaded
		print("Cancelled version saved to DropBox.")
		receipt = ReçusFiscaux.objects.get(id=receipt_id)
		receipt.file_name = file_name
		receipt.save()
		os.remove(file_name)
	except Exception:
		send_task_error.delay("DMS: Cancel PDF Receipt Error", traceback.format_exc())

@shared_task
def send_email(receipt_id, pdf_path, send_to, subject, body, t, cc=None, bcc=None):
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
		message["From"] = f"{s.host_email_name} <{s.host_email}>"
		message["To"] = send_to
		if bcc not in ("", None):
			message["Bcc"] = bcc
		if cc not in ("", None):
			message["Cc"] = cc
		message["Subject"] = subject
		message.attach(MIMEText(body+"\n\n", "plain"))
		dbx = dropbox.Dropbox(DROPBOX_OAUTH2_TOKEN)
		meta, res = dbx.files_download(pdf_path)
		part = MIMEBase("application", "octet-stream")
		part.set_payload(res.content)
		encoders.encode_base64(part)
		part.add_header(
			"Content-Disposition",
			f"attachment; filename={pdf_path.split('/reçus/')[1]}",
		)
		message.attach(part)
		print("PDF file found.")
		text = message.as_string()
		print("message processed ok")
		smtp_object.sendmail(s.host_email, list(filter(lambda x: x, [send_to, cc, bcc])), text)
		print("email sent")
		smtp_object.quit()
		receipt = ReçusFiscaux.objects.get(id=receipt_id)
		if pdf_path.split(".pdf")[0][-6:] == "Annulé":
			receipt.email_cancel = True
		else:
			receipt.email_active = True
		receipt.email_sent_time = timezone.now()
		receipt.save()
	except Exception:
		send_task_error.delay("DMS: Send Email Error", traceback.format_exc())
	return

@shared_task
def email_confirmation(t, lst):
	try:
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
		s = Paramètre.objects.get(id=4)
		smtp_object = smtplib.SMTP(s.smtp_domain,int(s.smtp_port))
		print("SMTP domain and SMTP port accepted.")
		smtp_object.ehlo()
		smtp_object.starttls()
		smtp_object.ehlo()
		smtp_object.login(s.host_email, s.host_password)
		print("Logged in ok.")
		message = MIMEMultipart()
		message["From"] = f"{s.host_email_name} <{s.host_email}>"
		message["To"] = s.host_email
		message["Subject"] = "Reçus envoyé par email"
		body = "\n"
		for email, sent_status in l:
			if sent_status:
				body += f"Email envoyé à : {email}\n"
			else:
				body += f"Email non envoyé à : {email}\n"
		message.attach(MIMEText(body, "plain"))
		text = message.as_string()
		smtp_object.sendmail(s.host_email, [s.host_email], text)
		print("email sent")
		smtp_object.quit()
	except Exception:
		send_task_error.delay("DMS: Email Confirmation Error", traceback.format_exc())

@shared_task
@atomic
def process_webhook_payload():
	try:
		for stored_value in WebhookLogs.objects.filter(processed=False):
			payload = stored_value.payload
			stored_value.processed = True
			stored_value.save()
			action = payload["notifications"][0]["action"].split("profile.")[1]
			data = payload["notifications"][0]["payload"]

			if action == "create":
				if len(payload["notifications"]) > 1:
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
							p.primary_address = data["primaryAddress"]
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
				if data[0].get("mergeStatus") == "MERGED":
					merged = 0
					deleted = 1
				else:
					merged = 1
					deleted = 0
				try:
					p_del = Profile.objects.get(seminar_desk_id = data[deleted]["id"])
					print("DISABLED profile found for merge.")
				except:
					print("DISABLED profile not found for merge.")
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
				p_del.disabled = True
				p_del.save()
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
				p.disabled = True
				p.save()
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
			p.primary_address = data["primaryAddress"]
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
			print(f"Profile {action}d successfuly.")

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
				print(f"Contact {action}d successfuly.")

			print("Message received okay.")

	except Exception:
		send_task_error.delay("DMS: Process Webhook Payload Error", traceback.format_exc())
	return 


@app.task(name="donations.receipt_trigger_notification")
def annual_receipt_reminder():
	try:
		notification = Paramètre.objects.get(id=2)
		if notification.release_date.toordinal() <= datetime.date.today().toordinal():
			if notification.annual_process_button == False:
				notification.annual_process_button = True
				notification.save()
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
		elif notification.annual_process_button == True:
			notification.annual_process_button = False
			notification.save()
	except Exception:
		send_task_error.delay("DMS: Annual Receipt Reminder Error", traceback.format_exc())
	return

@shared_task
def send_task_error(task_name, traceback):
	sleep(10)
	s = Paramètre.objects.get(id=4)
	smtp_object = smtplib.SMTP(s.smtp_domain,int(s.smtp_port))
	print("SMTP domain and SMTP port accepted.")
	smtp_object.ehlo()
	smtp_object.starttls()
	smtp_object.ehlo()
	smtp_object.login(s.host_email, s.host_password)
	print("Logged in ok.")
	message = MIMEMultipart()
	message["From"] = f"{s.host_email_name} <{s.host_email}>"
	message["To"] = ADMIN_EMAIL
	message["Subject"] = task_name
	message.attach(MIMEText("Traceback : \n"+traceback, "plain"))
	text = message.as_string()
	smtp_object.sendmail(s.host_email, ADMIN_EMAIL, text)
	print("email sent")
	smtp_object.quit()
