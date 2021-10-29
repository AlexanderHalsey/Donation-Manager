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
			receipt.file_name = cancel_pdf_receipt.delay(f"/media/reçus/{receipt.file_name}")
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
