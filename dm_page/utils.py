from django.http import HttpResponse
import datetime
from donations.settings import BASE_DIR
from .tasks import cancel_pdf_receipt
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
			cancel_pdf_receipt.delay(f"/media/reçus/{receipt.file_name}", receipt.id)

def export_xls(view, data, columns, file_name_extension):
	response = HttpResponse()
	response['Content-Type'] = 'application/ms-excel'
	response['Content-Disposition'] = f'attachment; filename="{datetime.date.today()}_{view}{file_name_extension}.xls"'
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

def format_address(json_dict):
	address = json_dict
	formatted_address = []

	care_of = address["careOf"]
	street_address = address["streetAddress"]
	street_address_2 = address["streetAddress2"]
	zip_code = address["zipCode"]
	city = address["city"]
	province = address["province"]
	countryCode = address["countryCode"]

	if care_of not in (None, "") and street_address not in (None, ""):
		formatted_address.append(care_of+", "+street_address)
	elif care_of not in (None, ""):
		formatted_address.append(care_of)
	elif street_address not in (None, ""):
		formatted_address.append(street_address)

	if street_address_2 not in (None, ""):
		formatted_address.append(street_address_2)

	if zip_code not in (None, "") and city not in (None, ""):
		formatted_address.append(zip_code+" "+city)
		if province not in (None, ""):
			formatted_address.append(province)
	elif zip_code not in (None, ""):
		if province not in (None, ""):
			formatted_address.append(zip_code+" "+province)
		else:
			formatted_address.append(zip_code)
	elif city not in (None, ""):
		if province not in (None, ""):
			formatted_address.append(city+", "+province)
		else:
			formatted_address.append(city)
	elif province not in (None, ""):
            formatted_address.append(province)

	return formatted_address
