from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.transaction import non_atomic_requests
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone

from donations.settings import BASE_DIR, DMS_WEBHOOK_PASSWORD, DMS_WEBHOOK_USERNAME, SEND_TO
from .models import *
from .utils import *
from .receive_webhook import process_webhook_payload
from .forms import DonationForm

import json
import datetime
import os
from secrets import compare_digest
# from pathlib import Path

# Create your views here.
def redir(request):
	return redirect("/fr")

def loginUser(request, lang):
	if request.user.is_authenticated:
		return redirect(f"/{lang}/")
	else:
		if request.method == "POST":
			username = request.POST.get('username')
			password = request.POST.get('password')
			user = authenticate(request, username=username, password=password)
			if user is not None:
				login(request, user)
				return redirect(f"/{lang}/")
			else:
				if lang == "fr":
					m = "le nom d'utilisateur ou le mot de passe est incorrect"
				if lang == "en":
					m = "The username or password is incorrect"
				messages.info(request, m) 
		return render(request, 'login.html', {"language": language_text(lang=lang)})

def logoutUser(request, lang):
	logout(request)
	return redirect(f"/{lang}/login")

@csrf_exempt
@require_POST
@non_atomic_requests
def dms_webhook(request):
	# Verify username and password
	username = request.headers.get("Username", "")
	password = request.headers.get("Password", "")
	if not compare_digest(username, DMS_WEBHOOK_USERNAME):
		return HttpResponseForbidden(
			f"Incorrect password in Dms-Webhook-Username header. {username}{DMS_WEBHOOK_USERNAME}",
			content_type = "text/plain",
		)
	if not compare_digest(password, DMS_WEBHOOK_PASSWORD):
		return HttpResponseForbidden(
			f"Incorrect password in Dms-Webhook-Password header.",
			content_type = "text/plain",
		)
		
	WebhookLogs.objects.filter(
			received_at__lte = timezone.now() - datetime.timedelta(days=7)
		).delete()
	payload = json.loads(request.body)
	WebhookLogs.objects.create(
			received_at = timezone.now(),
			payload = payload,
		)
	messages = process_webhook_payload(payload)
	return HttpResponse(messages, content_type="text/plain")

@login_required(login_url="/fr/login")
def webhooklogs(request, lang, change=None):
	'''path = Path("/Users/alexanderhalsey/Documents/Work/Coding/Django/Donation Manager/tests/json")
	for file in path.iterdir():
		payload = json.load(file)
		WebhookLogs.objects.create(
			received_at = timezone.now(),
			payload = payload,
		)'''
	logs = WebhookLogs.objects.all().order_by("-received_at")
	return render(request, 'webhooklogs.html',{'logs': logs, 'language': language_text(lang=lang)})

@login_required(login_url='/fr/login')
def dashboard(request, lang, change=None):

	# update receipts
	file_storage_check()

	# images that are not working on reportlab moved to database
	for i in Image.objects.all():
		i.delete()
	if len(Image.objects.all()) == 0:
		img1 = Image(
			name = "institution",
			image = "static/png/IVY_Logo_carré.png",
		)
		img1.save()
		img2 = Image(
			name = "signature",
			image = "static/png/signature_Charles_Trebaol.png",
		)
		img2.save()
 
	# receipt settings check
	if len(Paramètre.objects.all()) < 3:
		for setting in range(3):
			setting = Paramètre(
				date_range_start = None,
				date_range_end = None,
				release_date = None,
				automatic = False,
				manual = None,
				organisation_1 = None,
				donation_type_1 = None,
				organisation_2 = None,
				donation_type_2 = None,
				organisation_3 = None,
				donation_type_3 = None,
				organisation_4 = None,
				donation_type_4 = None,
				organisation_5 = None,
				donation_type_5 = None,
				
			)
			setting.save()

	# language change whilst mainting current url
	if change != None:
		return redirect(f'/{change}')

	# intial form_values
	form_values = {
		"title": language_text(lang=lang)["forms"]["donationTitle"]["create"], 
		"colour": "primary",
		"button": language_text(lang=lang)["buttons"]["submit"],
		"update": False,
		"delete": False,
		"confirn_receipt": False,
		"type": "create",
		"i": None,
		"errors": False,
		"errorlist": {},
	}

	# initial filter values
	initial_filter_values = {
		"contact": "",
		"date_donated_gte": "",
		"date_donated_lte": "",
		"payment_mode": "-----",
		"donation_type": "-----",
		"organisation": "-----",
		"amount_gte": "",
		"amount_lte": "",
		"disabled": False,
	}

	# context 
	tags = Tag.objects.all()
	if request.GET.get("disabled") == 'true':
		donations = Donation.objects.all().order_by("-date_donated")
		initial_filter_values["disabled"] = True
	else:
		donations = Donation.objects.all().filter(disabled=False).order_by('-date_donated')
	donations_count = Donation.objects.filter(disabled=False).count()
	total_donated = sum([d.amount for d in Donation.objects.filter(disabled=False)])

	# receipt eligibility
	eligibility = Paramètre.objects.get(id=3)
	receipt_conditions = list(filter(lambda x: x != ('None', 'None'), [(str(getattr(eligibility,f"organisation_{i}")),str(getattr(eligibility,f"donation_type_{i}"))) for i in range(1,6)]))
	for donation in donations:
		if (donation.organisation.profile.name, donation.donation_type.name) in receipt_conditions:
			donation.eligible = True
			donation.save()

	# front-end functionality
	scroll = 0 # to load with page scroll number so the page appears static on request
	collapse = 'collapse show' # to register collapse status of filter collapse button
	show_modal_pdf = False
	pdf_path = None

	# form
	form = DonationForm()
	if request.method == 'POST':

		if request.POST["Submit"] == "delete":
			disable_donation = Donation.objects.get(id=int(request.POST["id"]))
			disable_donation.disabled = True
			disable_donation.save()

			return redirect(f"/{lang}/")

		if request.POST["Submit"] == "confirm":
			donation = Donation.objects.get(id=int(request.POST["id"]))
			donation.pdf = True
			donation.save()
			receipt = RecettesFiscale()
			receipt.save()
			receipt.contact = donation.contact
			receipt.date_created = datetime.date.today()
			receipt.receipt_type = ('I','Individual')
			receipt.file_name = f"{receipt.id}_{donation.contact.profile.name}_{str(donation.date_donated)}_Individuel_{donation.id}.pdf"
			receipt.donation_list = [donation.id]
			receipt.cancel = False
			create_individual_receipt(receipt, donation,receipt.file_name)
			if request.POST.get("email") == 'true':
				body = 'Dear Sir Madam,\n\n'\
				f'This is an email confirmation of your donation with order n° {receipt.id}.\n'\
				'Please find attached your receipt.\n\n\n'\
				'Kind Regards,\n'\
				'Institut Vajra Yogini\n\n'
				path = f"{BASE_DIR}/static/pdf/receipts/{receipt.file_name}"
				email_status = send_email(path, SEND_TO, body)
				if email_status == "SENT":
					receipt.email_active = True
			receipt.save()
			return redirect("/")

		form = DonationForm(request.POST)

		if form.is_valid():
			donation = Donation()
			try:
				donation.contact = Contact.objects.get(profile__name = form.cleaned_data["contact"])
			except:
				donation.contact = Contact.objects.get(filter = form.cleaned_data["contact"])[0]
			finally:
				donation.amount = int(form.cleaned_data["amount_euros"] or 0) + float(form.cleaned_data["amount_cents"])
				donation.date_donated = form.cleaned_data["date_donated"]
				donation.payment_mode = PaymentMode.objects.get(payment_mode = form.cleaned_data["payment_mode"])
				donation.organisation = Organisation.objects.get(profile__name = form.cleaned_data["organisation"])
				donation.donation_type = DonationType.objects.get(name = form.cleaned_data["donation_type"])
				donation.save()

			if request.POST["Submit"] == "update":
				disable_donation = Donation.objects.get(id=int(request.POST["id"]))
				disable_donation.disabled = True
				disable_donation.save()

			return redirect(f"/{lang}/")

		else:
			form_values["errors"] = True
			for error in form.errors:
				form_values["errorlist"][error] = "is-invalid"
			form.fields["contact"].initial = request.POST["contact"]
			form.fields["date_donated"].initial = request.POST["date_donated"]
			form.fields["amount_euros"].initial = request.POST["amount_euros"]
			form.fields["amount_cents"].initial = request.POST["amount_cents"]
			form.fields["payment_mode"].initial = request.POST["payment_mode"]
			form.fields["donation_type"].initial = request.POST["donation_type"]
			form.fields["organisation"].initial = request.POST["organisation"]

			scroll = int(request.POST["scroll"] or 0)
			collapse = request.POST["collapse"]
			if collapse == "collapse_show":
				collapse = "collapse show"
			if request.POST["Submit"] == "update":
				form_values["title"] = language_text(lang=lang)["forms"]["donationTitle"]["update"]
				form_values["colour"] = "success"
				form_values["button"] = language_text(lang=lang)["buttons"]["update"]
				form_values["update"] = True
				form_values["type"] = "update"
				form_values["i"] = request.POST["id"]

	# GET requests
	else:
		# update / delete / receipt
		if request.GET.get("delete") != None or request.GET.get("update") != None or request.GET.get("create_receipt") != None:
			if request.GET.get("delete") != None:
				key = "delete"
				value = request.GET["delete"]
			elif request.GET.get("update") != None:
				key = "update"
				value = request.GET["update"]
			else: 
				key = "create_receipt"
				value = request.GET["create_receipt"]

			donation = donations.get(id=value)

			if key == "delete":
				form_values["i"] = value
				form_values["delete"] = True
			elif key == "update" or key == "create_receipt":
				# pre-populated donation_form for update
				form.fields["contact"].initial = donation.contact.profile.name
				form.fields["date_donated"].initial = "" if donation.date_donated == None else "/".join(str(donation.date_donated).split("-")[::-1])
				form.fields["amount_euros"].initial = "" if str(donation.amount).split(".")[0] == "0" else str(donation.amount).split(".")[0]
				form.fields["amount_cents"].initial = "."+str("{:.2f}".format(donation.amount)).split(".")[1]
				form.fields["payment_mode"].initial = "" if donation.payment_mode == None else donation.payment_mode.payment_mode
				form.fields["organisation"].initial = "" if donation.organisation == None else donation.organisation.profile.name
				form.fields["donation_type"].initial = "" if donation.donation_type == None else donation.donation_type.name
				if key == "update":
					# donation_form - update 
					form_values = {
						"title": language_text(lang=lang)["forms"]["donationTitle"]["update"],
						"colour": "success",
						"button": language_text(lang=lang)["buttons"]["update"],
						"update": True,
						"delete": False,
						"confirm_receipt": False,
						"type": "update",
						"i": value,
					}
				else:
					form_values = {
						"title": language_text(lang=lang)["forms"]["donationTitle"]["confirm"],
						"colour": "success",
						"button": language_text(lang=lang)["buttons"]["confirm"],
						"update": False,
						"delete": False,
						"confirm_receipt": True,
						"i": value,
					}

			scroll = int(request.GET["scroll"] or 0)
			collapse = request.GET["collapse"]
			if collapse == "collapse_show":
				collapse = "collapse show"

		if request.GET.get("Submit") != None:
			file_name_extension = ""
			# filter requests
			for key, value in request.GET.items():
				if key == "Submit":
					continue
				if key == "scroll":
					scroll = int(value or 0)
					continue
				if key == "collapse":
					collapse = value
					if collapse == "collapse_show":
						collapse = "collapse show" 
					continue
				if key == "disabled":
					continue
				if value not in ("", None, initial_filter_values[key]):
					initial_filter_values[key] = value
					file_name_extension += f"_{value}"
					if key == "contact":
						donations = donations.filter(contact__profile__name=value)
					if key == "date_donated_gte":
						date__gte = "-".join(value.split("/")[::-1])
						donations = donations.filter(date_donated__gte=date__gte)
					if key == "date_donated_lte":
						date__lte = "-".join(value.split("/")[::-1])
						donations = donations.filter(date_donated__lte=date__lte)
					if key == "amount_gte":
						try:
							donations = donations.filter(amount__gte=float(value))
						except:
							form_values["errorlist"]["amount_gte"] = "is-invalid"
					if key == "amount_lte":
						try:
							donations = donations.filter(amount__lte=float(value))
						except:
							form_values["errorlist"]["amount_lte"] = "is-invalid"
					if key == "payment_mode":
						donations = donations.filter(payment_mode__payment_mode=value)
					if key == "donation_type":
						donations = donations.filter(donation_type__name=value)
					if key == "organisation":
						donations = donations.filter(organisation__profile__name=value)
			columns = ["ID", "Name", "Date Donated", "Amount", "Payment Mode", "Donation Type", "Organisation"]
			data = [[donation.id, donation.contact.profile.name, str(donation.date_donated), 
				float(donation.amount), (None if donation.payment_mode == None else donation.payment_mode.payment_mode), 
				(None if donation.donation_type == None else donation.donation_type.name), (None if donation.organisation == None else donation.organisation.profile.name)] 
				for donation in donations]
			# export_xls:
			if request.GET.get("Submit") == "export_xls":
				return export_xls("Donations", data, columns, file_name_extension)
			# export csv
			if request.GET.get("Submit") == "export_csv":
				return export_csv("Donations", data, file_name_extension)
				
			scroll = int(request.GET["scroll"] or 0)
			collapse = request.GET["collapse"]
			if collapse == "collapse_show":
				collapse = "collapse show"

				
	# context after filter 	
	donation_count_filter = donations.count()
	total_donated_filter = sum([d.amount for d in donations])
	donation_types = [(t.organisation.profile.name, t.name) for t in DonationType.objects.all()]
	donation_types = json.dumps(donation_types)

	context = {
		'show_modal_pdf': show_modal_pdf,
		'pdf_path': pdf_path,
		'initial_filter_values': initial_filter_values,
		'collapse': collapse,
		'scroll': scroll,
		'tags': tags,
		'donations': donations,
		'donations_count': donations_count,
		'total_donated': total_donated,
		'donation_count_filter': donation_count_filter,
		'total_donated_filter': total_donated_filter,
		'form': form,
		'form_values': form_values,
		'donation_types': donation_types,
		'receipt_conditions': receipt_conditions,
		'language': language_text(lang=lang),
	}
	return render(request, 'dashboard.html', context)

@login_required(login_url='/fr/login')
def contact(request, pk, lang, change=None):

	# language change whilst mainting current url
	if change != None:
		return redirect(f'/{change}/contact/{pk}')

	# context
	contact = Contact.objects.get(profile__seminar_desk_id=pk)
	address = eval(contact.profile.primary_address)
	tags = contact.tags.all()
	donations = Donation.objects.filter(contact__profile__name=contact.profile.name)
	donations_count = donations.count()
	total_donated = sum([d.amount for d in donations])

	context = {
		'tags': tags,
		'address': address,
		'contact': contact,
		'donations': donations,
		'donations_count': donations_count,
		'total_donated': total_donated,
		'language': language_text(lang=lang),
	}
	return render(request, 'contact.html', context)

@login_required(login_url='/fr/login')
def donators(request, lang, change=None):
	
	# language change whilst mainting current url
	if change != None:
		return redirect(f'/{change}/donators')

	# initial filter values
	initial_filter_values = {
		"date_donated_gte": "",
		"date_donated_lte": "",
		"amount_gte": "",
		"amount_lte": "",
	}

	is_invalid = {
		"amount_gte": "",
		"amount_lte": "",
	}

	# context 
	tags = Tag.objects.all()
	donations = Donation.objects.all().filter(disabled=False).order_by('-date_donated')
	donations_count = donations.count()
	total_donated = sum([d.amount for d in donations])
	pdf_path = None

	# front-end functionality
	scroll = 0 # to load with page scroll number so the page appears static on request
	collapse = 'collapse show' # to register collapse status of filter collapse button

	'''if request.GET.get("view_pdf"):
		i = request.GET.get("view_pdf")
		listdir = os.listdir("dm_page/static/pdf/receipts/")
		pdf_path = list(filter(lambda x: x.split(".pdf")[0][-len(i):] == i, listdir))[0]'''

	# filter requests
	if request.GET.get("Submit") != None:
		file_name_extension = ""
		for key, value in request.GET.items():
			if key == "Submit":
				continue
			if key == "scroll":
				scroll = int(value or 0)
				continue
			if key == "collapse":
				collapse = value
				if collapse == "collapse_show":
					collapse = "collapse show" 
				continue
			if value not in ("", None, initial_filter_values[key]):
				initial_filter_values[key] = value
				file_name_extension += f"_{value}"
				if key == "date_donated_gte":
					date__gte = "-".join(value.split("/")[::-1])
					donations = donations.filter(date_donated__gte=date__gte)
				if key == "date_donated_lte":
					date__lte = "-".join(value.split("/")[::-1])
					donations = donations.filter(date_donated__lte=date__lte)
				if key == "amount_gte":
					try:
						donations = donations.filter(amount__gte=float(value))
					except:
						is_invalid["amount_gte"] = "is-invalid"
				if key == "amount_lte":
					try:
						donations = donations.filter(amount__lte=float(value))
					except:
						is_invalid["amount_lte"] = "is-invalid"
		columns = ["Id", "Name", "Email Address", "Total_donated"]
		contacts = set([donation.contact for donation in donations])
		data = [[contact.id, contact.profile.name, contact.profile.email, 
			sum([d.amount for d in donations.filter(contact=contact)])] for contact in contacts]
		# export_xls:
		if request.GET.get("Submit") == "export_xls":
			return export_xls("Contacts", data, columns, file_name_extension)
		# export_csv
		if request.GET.get("Submit") == "export_csv":
			return export_csv("Contacts", data, file_name_extension)

	# contacts
	contacts = Contact.objects.all()
	contacts = [{
		"id": contact.id,
		"tags": contact.tags,
		"name": contact.profile.name,
		"total_donations": len(donations.filter(contact=contact)),
		"total_donated": sum([donation.amount for donation in donations.filter(contact=contact)]),
	} for contact in contacts]
	contacts = list(filter(lambda x: x["total_donated"]>0, contacts))

	# context after filter 	
	donation_count_filter = donations.count()
	total_donated_filter = sum([d.amount for d in donations])

	context = {
		'pdf_path': pdf_path,
		'initial_filter_values': initial_filter_values,
		'collapse': collapse,
		'contacts': contacts,
		'scroll': scroll,
		'is_invalid': is_invalid,
		'tags': tags,
		'donations': donations,
		'donations_count': donations_count,
		'total_donated': total_donated,
		'donation_count_filter': donation_count_filter,
		'total_donated_filter': total_donated_filter,
		'language': language_text(lang=lang),
	}
	return render(request, 'donators.html', context)

@login_required(login_url='/fr/login')
def pdf_receipts(request, lang, change=None):
	
	if change != None:
		return redirect(f'/{change}/pdf_receipts')

	# update receipts
	file_storage_check()

	# annual_receipt tests for Ava Martin
	# if date_trigger.toordinal() <= datetime.date.today().toordinal():
	if request.GET.get('annual_receipt') == "ok":
		date_range = [datetime.date(2019,1,1), datetime.date.today()]
		for x in range(1,11):
			contact = Contact.objects.get(id=x) 
			annual_donations = Donation.objects.filter(contact=contact).filter(eligible=True).filter(pdf=False).order_by("date_donated") # .filter(date_donated__gte = date_range[0]).filter(date_donated__lte = date_range[1])
			if len(annual_donations) > 0:
				receipt = RecettesFiscale()
				receipt.save()
				receipt.contact = contact
				receipt.date_created = datetime.date.today()
				receipt.receipt_type = ('A','Annual')
				receipt.file_name = f"{receipt.id}_{contact.profile.name}_{str(date_range[0])}_{str(date_range[1])}_Annuel.pdf"
				receipt.donation_list = [d.id for d in annual_donations]
				receipt.cancel = False
				receipt.save()
				create_annual_receipt(receipt, contact, annual_donations, date_range, receipt.file_name)
				for donation in annual_donations:
					donation.pdf = True
					donation.save()
				break

	# initial filter values
	initial_filter_values = {
		"contact": "",
		"date_donated_gte": "",
		"date_donated_lte": "",
		"file_name": "",
		"receipt_type": "",
		"canceled": True,
	}

	if request.method == "POST":
		if request.POST["Submit"] not in ("", None):
			receipt = RecettesFiscale.objects.get(id=request.POST["Submit"])
			send_to = request.POST["email"]
			body = request.POST["message"] + "\n\n"
			path = f"{BASE_DIR}/static/pdf/receipts/{receipt.file_name}"
			email_status = send_email(path, send_to, body)
			if email_status == "SENT":
				print(path.split(".pdf")[0][-6:])
				if path.split(".pdf")[0][-6:] == "Annulé":
					receipt.email_cancel = True
				else:
					receipt.email_active = True
				receipt.save()
			return redirect(f'{lang}/pdf_receipts/')

	tags = Tag.objects.all()
	donations = Donation.objects.filter(disabled = False).order_by("-date_donated")
	contact_names = [contact.profile.name for contact in Contact.objects.all()]
	
	donations_count = donations.count()
	total_donated = sum([d.amount for d in donations])
	donation_count_filter = donations.count()
	total_donated_filter = sum([d.amount for d in donations])
	print(request.GET.get("canceled"))
	if request.GET.get("canceled") == 'false':
		initial_filter_values["canceled"] = False
		donation_receipts = RecettesFiscale.objects.filter(cancel=False)
	else:
		donation_receipts = RecettesFiscale.objects.all()
	donation_types = []
	for donation_receipt in donation_receipts:
		try:
			receipt_type = eval(donation_receipt.receipt_type)[1]
			if lang == "fr":
				receipt_type = receipt_type[0:-2] + "e" + receipt_type[-1]
			donation_types.append([donation_receipt.id, receipt_type])
		except:
			donation_types.append([donation_receipt.id, None])

	scroll = int(request.GET.get("scroll") or 0)

	# filter
	if request.GET.get("contact") not in ("", None):
		donation_receipts = donation_receipts.filter(contact__profile__name = request.GET.get("contact"))
		initial_filter_values["contact"] = request.GET.get("contact")
	if request.GET.get("date_donated_gte") not in ("", None):
		date__gte = "-".join(request.GET.get("date_donated_gte").split("/")[::-1])
		donation_receipts = donation_receipts.filter(date_created__gte = date__gte)
		initial_filter_values["date_donated_gte"] = request.GET.get("date_donated_gte")
	if request.GET.get("date_donated_lte") not in ("", None):
		date__lte = "-".join(request.GET.get("date_donated_lte").split("/")[::-1])
		donation_receipts = donation_receipts.filter(date_created__lte = date__lte)
		initial_filter_values["date_donated_lte"] = request.GET.get("date_donated_lte")
	if request.GET.get("file_name") not in ("", None):
		donation_receipts = donation_receipts.filter(file_name = request.GET.get("file_name"))
		initial_filter_values["file_name"] = request.GET.get("file_name")
	if request.GET.get("receipt_type") not in ("", "-----", None):
		choice = request.GET.get("receipt_type").replace("e","a")
		choice = str((choice[0],choice))
		donation_receipts = donation_receipts.filter(receipt_type = choice)
		initial_filter_values["receipt_type"] = request.GET.get("receipt_type")

	# view_pdf, download_pdf
	if request.GET.get("view_pdf"):
		show_modal_pdf = True
		i = request.GET.get("view_pdf")
		file_name = RecettesFiscale.objects.get(id=int(i)).file_name
		file_name = f"/static/pdf/receipts/{file_name}"
	else:
		show_modal_pdf = False
	if request.GET.get("download_pdf"):
		i = request.GET.get("download_pdf")
		file_name = RecettesFiscale.objects.get(id=int(i)).file_name
		full_path = f"{BASE_DIR}/static/pdf/receipts/{file_name}"
		with open(full_path, 'rb') as pdf:
			response = HttpResponse(pdf, content_type='application/pdf')
			response['Content-Disposition'] = f'attachment; filename="{file_name}"'
		return response

	try:
		file_name
	except:
		file_name = ""

	email_content = {"true": False, "id": "", "email": "", "file": ""}
	if request.GET.get("send_email") not in ("", None):
		email_content["true"] = True
		email_content["id"] = RecettesFiscale.objects.get(id=request.GET.get("send_email")).id
		email_content["email"] = RecettesFiscale.objects.get(id=request.GET.get("send_email")).contact.profile.email
		email_content["file"] = RecettesFiscale.objects.get(id=request.GET.get("send_email")).file_name

	context = {
		'tags': tags,
		'donations': donations,
		'contact_names': contact_names,
		'donations_count': donations_count,
		'total_donated': total_donated,
		'total_donated_filter': total_donated_filter,
		'donation_count_filter': donation_count_filter,
		'initial_filter_values': initial_filter_values,
		'donation_receipts': donation_receipts,
		'donation_types': donation_types,
		'show_modal_pdf': show_modal_pdf,
		'file_name': file_name,
		'scroll': scroll,
		'email_content': email_content,
		'language': language_text(lang=lang),
	}
	return render(request, 'pdf_receipts.html', context)

@login_required(login_url='/fr/login')
def receipt(request, file):
	full_path = f'{BASE_DIR}/static/pdf/receipts/{file}'
	with open(full_path, 'rb') as pdf:
		response = HttpResponse(pdf, content_type='application/pdf')
		response['Content-Disposition'] = f'attachment; filename="{file}"'
	return response
