from django.http import HttpResponse
import datetime

# export to excel
import xlwt

# html to pdf
from django.template.loader import get_template
from xhtml2pdf import pisa

# word to html
import mammoth

# emails
from donations.settings import EMAIL_ADDRESS, PASSWORD, SEND_TO
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



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

def receipt(context):
	result_file = open(f"dm_page/static/pdf/PDF_Receipt_{datetime.date.today()}_{context['id']}.pdf", "w+b")
	template = get_template("receipt.html")
	html = template.render(context)
	pisa_status = pisa.CreatePDF(html, dest=result_file)
	result_file.close()           
	return  pisa_status.err, f"dm_page/static/pdf/PDF_Receipt_{datetime.date.today()}_{context['id']}.pdf"

def send_email(data):
	smtp_object = smtplib.SMTP('smtp.gmail.com',587)
	smtp_object.ehlo()
	smtp_object.starttls()
	smtp_object.ehlo()
	smtp_object.login(EMAIL_ADDRESS, PASSWORD)
	message = MIMEMultipart()
	message["From"] = EMAIL_ADDRESS
	message["To"] = SEND_TO
	message["Subject"] = "Receipt"
	body = ""
	for key,value in data.items():
		body += f"{key}: {value}"+"\n"
	message.attach(MIMEText(body, "plain"))
	filename = receipt(data)[1]
	with open(filename, "rb") as attachment:
		part = MIMEBase("application", "octet-stream")
		part.set_payload(attachment.read())
		encoders.encode_base64(part)
		part.add_header(
			"Content-Disposition",
			f"attachment; filename= {filename.split('/pdf/')[1]}",
		)
		message.attach(part)
	text = message.as_string()
	smtp_object.sendmail(EMAIL_ADDRESS, SEND_TO, text)
	smtp_object.quit()

def word_to_html(path_to_word_file, path_to_html_file):
	with open(path_to_word_file, "rb") as docx_file:
		result = mammoth.convert_to_html(docx_file)
	with open(path_to_html_file, "w") as html_file:
		html_file.write(result.value)
	docx_file.closed
	html_file.closed
	return
