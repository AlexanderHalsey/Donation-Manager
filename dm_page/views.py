from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.transaction import non_atomic_requests
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone

from donations.settings import BASE_DIR, DMS_WEBHOOK_TOKEN
from .models import *
from .utils import *
from .receive_webhook import process_webhook_payload
from .forms import DonationForm

import json
import datetime
import os
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
				print(request.META)
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
	# Verify token
	given_token = request.headers.get("Dms-Webhook-Token", "")
	if not compare_digest(given_token, DMS_WEBHOOK_TOKEN):
		return HttpResponseForbidden(
				"Incorrect token in Dms-Webhook-Token header.",
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
def webhooklogs(request, lang):
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
def dashboard(request, lang):

	# intial form_values
	form_values = {
		"title": language_text(lang=lang)["forms"]["donationTitle"]["create"], 
		"colour": "primary",
		"button": language_text(lang=lang)["buttons"]["submit"],
		"update": False,
		"delete": False,
		"type": "create",
		"i": None,
		"errors": False,
		"errorlist": {},
	}

	# initial filter values
	initial_filter_values = {
		"contact": "Type to search...",
		"date_donated_gte": "DD/MM/YYYY",
		"date_donated_lte": "DD/MM/YYYY",
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
	donations_count = donations.count()
	total_donated = sum([d.amount for d in donations])

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

		form = DonationForm(request.POST)
		if form.is_valid():
			donation = Donation(
				contact = Contact.objects.get(
					profile__name = form.cleaned_data["contact"]
				),
				amount = int(form.cleaned_data["amount_euros"] or 0) + float(form.cleaned_data["amount_cents"]),
				date_donated = form.cleaned_data["date_donated"],
				payment_mode = None if form.cleaned_data["payment_mode"] 
				== "" else PaymentMode.objects.get(
					payment_mode = form.cleaned_data["payment_mode"]
				),
				donation_type = None if form.cleaned_data["donation_type"] 
				== "" else DonationType.objects.get(
					donation_type = form.cleaned_data["donation_type"]
				),
				organisation = None if form.cleaned_data["organisation"] 
				== "" else Organisation.objects.get(
					profile__name = form.cleaned_data["organisation"]
				),
			)
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
		# update delete
		if request.GET.get("delete") != None or request.GET.get("update") != None:
			if request.GET.get("delete") != None:
				key = "delete"
				value = request.GET["delete"]
			else:
				key = "update"
				value = request.GET["update"]

			donation = donations.get(id=value)

			if key == "delete":
				form_values["i"] = value
				form_values["delete"] = True
			elif key == "update":
				# pre-populated donation_form for update
				form.fields["contact"].initial = donation.contact.profile.name
				form.fields["date_donated"].initial = "" if donation.date_donated == None else "/".join(str(donation.date_donated).split("-")[::-1])
				form.fields["amount_euros"].initial = "" if str(donation.amount).split(".")[0] == "0" else str(donation.amount).split(".")[0]
				form.fields["amount_cents"].initial = "."+str("{:.2f}".format(donation.amount)).split(".")[1]
				form.fields["payment_mode"].initial = "" if donation.payment_mode == None else donation.payment_mode.payment_mode
				form.fields["donation_type"].initial = "" if donation.donation_type == None else donation.donation_type.donation_type
				form.fields["organisation"].initial = "" if donation.organisation == None else donation.organisation.profile.name
				# donation_form - update 
				form_values = {
					"title": language_text(lang=lang)["forms"]["donationTitle"]["update"],
					"colour": "success",
					"button": language_text(lang=lang)["buttons"]["update"],
					"update": True,
					"delete": False,
					"type": "update",
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
						donations = donations.filter(amount__gte=float(value))
					if key == "amount_lte":
						donations = donations.filter(amount__lte=float(value))
					if key == "payment_mode":
						donations = donations.filter(payment_mode__payment_mode=value)
					if key == "donation_type":
						donations = donations.filter(donation_type__donation_type=value)
					if key == "organisation":
						donations = donations.filter(organisation__profile__name=value)
			columns = ["ID", "Name", "Date Donated", "Amount", "Payment Mode", "Donation Type", "Organisation"]
			data = [[donation.id, donation.contact.profile.name, str(donation.date_donated), 
				float(donation.amount), (None if donation.payment_mode == None else donation.payment_mode.payment_mode), 
				(None if donation.donation_type == None else donation.donation_type.donation_type), (None if donation.organisation == None else donation.organisation.profile.name)] 
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
		'language': language_text(lang=lang),
	}
	return render(request, 'dashboard.html', context)

@login_required(login_url='/fr/login')
def contact(request, pk, lang):

	# context
	contact = Contact.objects.get(id=pk)
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
def donators(request, lang):

	# initial filter values
	initial_filter_values = {
		"date_donated_gte": "DD/MM/YYYY",
		"date_donated_lte": "DD/MM/YYYY",
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
					donations = donations.filter(amount__gte=float(value))
				if key == "amount_lte":
					donations = donations.filter(amount__lte=float(value))
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
def pdf_receipts(request, lang):
	tags = Tag.objects.all()
	donations = Donation.objects.filter(disabled=False).order_by("-date_donated")
	file_storage_check(donations)
	donations_count = donations.count()
	total_donated = sum([d.amount for d in donations])

	donation_count_filter = donations.count()
	total_donated_filter = sum([d.amount for d in donations])
	context = {
		'tags': tags,
		'donations': donations,
		'donations_count': donations_count,
		'total_donated': total_donated,
		'total_donated_filter': total_donated_filter,
		'donation_count_filter': donation_count_filter,
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

	# view_pdf, download_pdf
	"""if request.GET.get("view_pdf"):
		show_modal_pdf = True
		i = request.GET.get("view_pdf")
		pdf_path = donations.get(id=int(i)).pdf_path
		scroll = int(request.GET["scroll"] or 0)
		collapse = request.GET["collapse"]
		if collapse == "collapse_show":
			collapse = "collapse show"

	if request.GET.get("download_pdf"):
		i = request.GET.get("download_pdf")
		filename = donations.get(id=int(i)).pdf_path
		full_path = f"{BASE_DIR}/dm_page/static/pdf/receipts/{filename}"
		print(full_path)
		with open(full_path, 'rb') as pdf:
			response = HttpResponse(pdf, content_type='application/pdf')
			response['Content-Disposition'] = f'attachment; filename="{filename}"'
		return response"""

