from django.http import HttpResponse
from donations.settings import EMAIL_ADDRESS, PASSWORD, SEND_TO
import xlwt
import datetime
import smtplib


def export_xls(view, data, columns):
	response = HttpResponse(content_type='application/ms-excel')
	response['Content-Disposition'] = f'attachment; filename="{view}_{datetime.date.today()}.xls"'
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

def send_email(data):
	smtp_object = smtplib.SMTP('smtp.gmail.com',587)
	smtp_object.ehlo()
	smtp_object.starttls()
	smtp_object.ehlo()
	smtp_object.login(EMAIL_ADDRESS, PASSWORD)
	message = "Subject: Receipt" + "\n\n\n"
	for key,value in data.items():
		message += f"{key}: {value}"+"\n"
	smtp_object.sendmail(EMAIL_ADDRESS, SEND_TO, message)
	smtp_object.quit()