from django.http import HttpResponse
import datetime
from donations.settings import BASE_DIR
from .models import *
import json
import io

# file storage
from pathlib import Path
import os

# export to excel
import xlwt

# export to csv
import csv

# pdf receipt
from donations.settings import BASE_DIR
from django.core.files import File
from django.core.files.storage import FileSystemStorage
import num2words
from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.utils import simpleSplit, ImageReader
from reportlab.pdfbase.ttfonts import TTFont
from textwrap import wrap


def language_text(lang="fr"):
	if lang == "en":
		l = "english"
	if lang == "fr":
		l = "french"
	with open(f"{BASE_DIR}/static/language/{l}.json", "r") as f:
		payload = json.load(f)
		return payload

def file_storage_check():
	for receipt in ReçusFiscaux.objects.all():
		if receipt.cancel == True and receipt.file_name[-10:] != "Annulé.pdf":
			for i in eval(receipt.donation_list):
				donation = Donation.objects.get(id=i)
				donation.pdf = False
				donation.save()
			receipt.file_name = cancel_pdf_receipt(f"{BASE_DIR}/static/pdf/receipts/{receipt.file_name}")
			receipt.save()

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

def create_individual_receipt(receipt_id, donation_id, file_name):
	receipt_settings = Organisation.objects.filter(used_for_receipt=True)
	donation = Donation.objects.get(id=donation_id)
	if len(receipt_settings) > 1:
		print("There is more than one default value")
		print("Something has gone wrong with the save functionality")
	else:
		receipt_settings = receipt_settings[0]
	receipt = ReçusFiscaux.objects.get(id=receipt_id)
	path = f"{BASE_DIR}/static/pdf/receipts/"
	c = donation.contact
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
		"receipt_id": [str(receipt_id)],
		"organisation_object": [
			"Object:", 
			receipt_settings.object_title or "", 
			receipt_settings.object_description or ""
		],
		"contact": [c.profile.name or ""], 
		"contact_address": address,
		"date_donated": ["/".join(str(donation.date_donated).split("-")[::-1])],
		"amount": ["€ "+ str(donation.amount)],
		"other_donation_variables": [
			num2words.num2words("%.2f"%float(donation.amount or 0), lang="fr").capitalize() + " euros", 
			donation.payment_mode_name, 
			donation.forme_du_don_name, 
			donation.nature_du_don_name,
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
	custom_storage = FileSystemStorage(location='static', base_url='/static/')
	with open(path + file_name, "wb+") as f:
		django_file = File(f)
		output.write(django_file)
		custom_storage.save(path+file_name, django_file)
	print("New file created.")
	return

def create_annual_receipt(receipt_id, contact_id, donation_lst, date_range, file_name):
	receipt_settings = Organisation.objects.filter(used_for_receipt=True)
	receipt = ReçusFiscaux.objects.get(id=receipt_id)
	contact = Contact.objects.get(id=contact_id)
	donations = Donation.objects.filter(id__in = donation_lst)
	if len(receipt_settings) > 1:
		print("There is more than one default value")
		print("Something has gone wrong with the save functionality")
	else:
		receipt_settings = receipt_settings[0]
	path = f"{BASE_DIR}/static/pdf/receipts/"
	p = contact.profile
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
		"total_amount": ["€ "+ str("%.2f"%sum([float(d.amount) for d in donations]))],
		"in_letters": [num2words.num2words("%.2f"%sum([float(d.amount) for d in donations]), lang="fr").capitalize() + " euros"], 
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
		can.drawString(79, 235-(index*18), " / ".join(str(donation.date_donated).split("-")[::-1]))
		can.drawString(156, 235-(index*18), donation.payment_mode_name or "")
		can.drawString(239, 235-(index*18), donation.forme_du_don_name)
		can.drawString(377, 235-(index*18), donation.nature_du_don_name)
		can.drawString(460, 235-(index*18), "€ " + str(donation.amount))
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
			can2.drawString(450, 767-(index*18), "€ " + str(donation.amount))
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
	can2.drawString(305, 678-additional, "Président de l'association")
	can2.drawString(52, 734-additional, "A "+(receipt_settings.institut_town or "")+" le :")
	can2.drawString(146, 734-additional, "/".join(str(datetime.date.today()).split("-")[::-1]))
	can2.drawString(305, 583-additional, (receipt_settings.president or ""))
	try:
		img3 = ImageReader(images["president_signature"])
		can2.drawImage(img3, 310, 483-additional, width=100, preserveAspectRatio=True)
	except:
		pass
	can2.showPage()
	can2.save()
	packet2.seek(0)
	new_pdf2 = PdfFileReader(packet2)

	existing_pdf = PdfFileReader(open(f"{BASE_DIR}/static/pdf/annual_receipt.pdf", "rb"))
	output = PdfFileWriter()
	page = existing_pdf.getPage(0)
	page.mergePage(new_pdf.getPage(0))
	page2 = existing_pdf.getPage(1)
	page2.mergePage(new_pdf2.getPage(0))
	output.addPage(page)
	output.addPage(page2)
	outputStream = open(path + file_name, "wb")
	output.write(outputStream)
	outputStream.close()
	return

def cancel_pdf_receipt(path):
	# this also needs to include anual pdf_receipts !!!
	# only considering individual receipts at the moment
	packet = io.BytesIO()
	can = canvas.Canvas(packet, pagesize=A4)
	img = ImageReader(f"{BASE_DIR}/static/png/LOGO-ANNULÉ.png")
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
