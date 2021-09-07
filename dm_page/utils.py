from django.http import HttpResponse
import datetime

# pdf receipt
from donations.settings import BASE_DIR
from .models import *
import num2words
from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import simpleSplit, ImageReader
from reportlab.pdfbase.ttfonts import TTFont
from textwrap import wrap
import json

# file storage
from pathlib import Path
import os

# export to excel
import xlwt

# export to csv
import csv

# emails
from donations.settings import EMAIL_ADDRESS, PASSWORD, SEND_TO
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def language_text(lang="fr"):
	if lang == "en":
		l = "english"
	if lang == "fr":
		l = "french"
	print(BASE_DIR)
	with open(f"{BASE_DIR}/static/language/{l}.json", "r") as f:
		payload = json.load(f)
		return payload

def file_storage_check(donations):
	path = Path(f"{BASE_DIR}/static/pdf/receipts/")
	files = [str(entry).split("/receipts/")[1] for entry in path.iterdir() if str(entry).split("/receipts/")[1] != ".DS_Store"]
	# Check for individual donations
	for donation in donations:
		donation_file_name = donation.contact.profile.name + "_" + str(donation.date_donated) + "_" + str(donation.id) + "_" + "Individuel" + ".pdf"
		if donation.pdf == True and donation_file_name not in files:
			donation_receipt = DonationReceipt()
			donation_receipt.save()
			# Create pdf
			address = eval(donation.contact.profile.primary_address)
			if len(address) == 5:
				address = address[:2]+[address[2]+", "+address[3]]+[address[4]]
			text_variables = {
				"institut_address": ["Institut Vajra Yogini pour l'Epanouissement de la Sagesse", "LIEU DIT CLAUZADE", "81500 MARZENS"],
				"donation_id": [str(donation_receipt.id)],
				"organisation_object": ["Object:", "Exercise du culte bouddhiste", "Association Culturelle régie par la loi du 9 décembre 1905 du 16 mars 1906. Ce reçu donne droit à une déduction fiscale conformément à l'arrête préfectoral du Tarn du 30 décemebre 2003."],
				"contact": [donation.contact.profile.name], 
				"contact_address": address,
				"date_donated": ["/".join(str(donation.date_donated).split("-")[::-1])],
				"amount": ["€ "+ str(donation.amount)],
				"other_donation_variables": [num2words.num2words(int(donation.amount or 0), lang="fr").capitalize() + " euros", "Espèces", "Déclaration de don manuel", "Numéraire"], 
				"institut_village": ["MARZENS"],
				"date_today": ["/".join(str(datetime.date.today()).split("-")[::-1])],
				"president": ["Charles Trébaol"],
			}
			images = {
				"institution": "/static/png/IVY_Logo_carré.png",
				"signature": "/static/png/signature_Charles_Trebaol.png",
			}
			donation_receipt.contact = donation.contact
			donation_receipt.receipt_type = ('I', 'Individual')
			donation_receipt.file_name = individual_pdf_receipt(text_variables, images, str(path) + "/" + donation_file_name)
			donation_receipt.save()
		elif donation.pdf == False and donation_file_name in files:
			# Annuler
			donation_receipt = DonationReceipt.objects.get(file_name=donation_file_name)
			donation_receipt.canceled = True
			donation_receipt.file_name = cancel_pdf_receipt(str(path) + "/" + donation_file_name)
			donation_receipt.save()

def annual_pdf_receipt(text, images, contact, donations, path):
	return

def individual_pdf_receipt(text, images, donation_file_name):
	packet = io.BytesIO()
	can = canvas.Canvas(packet, pagesize=A4)

	pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
	pdfmetrics.registerFont(TTFont('Arial Bold', 'Arial Bold.ttf'))
	pdfmetrics.registerFont(TTFont('Arial Italic', 'Arial Italic.ttf'))
	fonts = ["Arial Bold", "Arial", "Arial Italic"]
	sizes = [12, 16, 18]

	text_matrix = {
		"institut_address": [(0, 0, 143, 700), (1, 0, 143, 680), (1, 0, 143, 665)], 
		"donation_id": [(0, 2, 470, 782)], 
		"organisation_object": [(0, 0, 38, 615), (1, 0, 88, 615), (1, 0, 32, 590)], 
		"contact": [(0, 0, 200, 500)], 
		"contact_address": [(1, 0, 200, 480), (1, 0, 200, 465), (1, 0, 200, 450), (1, 0, 200, 435)], 
		"date_donated": [(1, 0, 363, 400)], 
		"amount": [(0, 1, 252, 370)], 
		"other_donation_variables": [(2, 0, 206, 337), (2, 0, 182, 322), (2, 0, 151, 307), (2, 0, 152, 293)], 
		"institut_village": [(1, 0, 43, 193)], 
		"date_today": [(1, 0, 124, 193)], 
		"president": [(0, 0, 302, 158)],
	}

	image_matrix = {
		"institution": (45, 565, 80),
		"signature": (310, -55, 100),
	}

	for key,value in text.items():
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

	for key,value in images.items():
		img = ImageReader(str(BASE_DIR)+value)
		can.drawImage(img, image_matrix[key][0], image_matrix[key][1], width=image_matrix[key][2], preserveAspectRatio=True)

	can.showPage()
	can.save()
	packet.seek(0)
	new_pdf = PdfFileReader(packet)
	existing_pdf = PdfFileReader(open(f"{BASE_DIR}/static/pdf/receipt.pdf", "rb"))
	output = PdfFileWriter()
	page = existing_pdf.getPage(0)
	page.mergePage(new_pdf.getPage(0))
	output.addPage(page)
	outputStream = open(donation_file_name, "wb")
	output.write(outputStream)
	outputStream.close()
	return donation_file_name.split("/receipts/")[1]

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
	page = existing_pdf.getPage(0)
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

def send_email(pdf_path, donation_id):
	smtp_object = smtplib.SMTP('smtp.gmail.com',587)
	smtp_object.ehlo()
	smtp_object.starttls()
	smtp_object.ehlo()
	smtp_object.login(EMAIL_ADDRESS, PASSWORD)
	message = MIMEMultipart()
	message["From"] = EMAIL_ADDRESS
	message["To"] = SEND_TO
	message["Subject"] = "Receipt"
	body = f"Dear Sir Madam,\n\nThis is an email confirmation of your donation with order n° {donation_id}.\n\nPlease find attached your receipt.\n\n\n\nKind Regards,\n\nInstitut Vajra Yogini\n\n\n"
	message.attach(MIMEText(body, "plain"))
	with open(pdf_path, "rb") as attachment:
		part = MIMEBase("application", "octet-stream")
		part.set_payload(attachment.read())
		encoders.encode_base64(part)
		part.add_header(
			"Content-Disposition",
			f"attachment; filename={pdf_path.split('/receipts/')[1]}",
		)
		message.attach(part)
	text = message.as_string()
	smtp_object.sendmail(EMAIL_ADDRESS, SEND_TO, text)
	smtp_object.quit()

def export_xls(view, data, columns, file_name_extension):
	response = HttpResponse()
	response['Content-Type'] = 'application/ms-excel'
	response['Content-Disposition'] = f'attachment; filename="{view}_{datetime.date.today()}{file_name_extension}.xls"'
	wb = xlwt.Workbook(encoding='utf-8')
	ws = wb.add_sheet(view)
	row_num = 0
	font_style = xlwt.XFStyle()
	font_style.font.bold = True
	for col_num in range(len(columns)):
		ws.write(row_num, col_num, columns[col_num], font_style)
	font_style.font.bold = False 
	for row in data:
		row_num += 1
		for col_num in range(len(row)):
			ws.write(row_num, col_num, row[col_num], font_style)
	wb.save(response)
	return response

def export_csv(view, data, file_name_extension):
	response = HttpResponse()
	response['Content-Type'] = 'text/csv'
	response['Content-Disposition'] = f'attachment; filename="{view}_{datetime.date.today()}{file_name_extension}.csv"'
	writer = csv.writer(response)
	for row in data:
		writer.writerow(row)
	return response

