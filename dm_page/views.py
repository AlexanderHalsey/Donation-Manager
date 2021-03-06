from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.transaction import non_atomic_requests
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core import serializers
from django.core.cache import cache
from django.forms.models import model_to_dict

from donations.settings import *
from .models import *
from .utils import *
from .tasks import *
from .receive_webhook import process_webhook_payload
from .forms import DonationForm

import json
import math
import datetime
import dropbox
import os
from itertools import chain
from decimal import *
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
	payload = json.loads(request.body)
	
	WebhookLogs.objects.create(
		payload = payload,
		received_at = timezone.now(),
	)
	WebhookLogs.objects.filter(
		received_at__lte = timezone.now() - datetime.timedelta(days=7)
	).delete()
	process_webhook_payload.delay()
	return HttpResponse("Payload to be processed.")

@login_required(login_url="/fr/login")
def webhooklogs(request, lang, change=None):
	logs = WebhookLogs.objects.all().order_by("-received_at")
	logs_json = json.dumps([log.payload for log in logs])
	return render(request, 'webhooklogs.html',{'logs': logs, 'logs_json': logs_json, 'language': language_text(lang=lang)})

@login_required(login_url='/fr/login')
def dashboard(request, lang, change=None):

	if os.getenv("errortoggle") == 'True':
		x = y
	# language change whilst mainting current url
	if change != None:
		return redirect(f'/{change}')

	# update receipts
	file_storage_check()

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
		"email_address": ""
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
		donations = Donation.objects.all()
		initial_filter_values["disabled"] = True
	else:
		donations = Donation.objects.all().filter(disabled=False)
	unadulterated_donations = Donation.objects.filter(disabled=False)
	donations_count = unadulterated_donations.count()
	total_donated = sum([d.amount for d in unadulterated_donations])

	# front-end functionality
	scroll = 0 # to load with page scroll number so the page appears static on request
	collapse = 'collapse show' # to register collapse status of filter collapse button
	show_modal_pdf = False
	pdf_path = None

	# forms
	form = DonationForm()
	if request.method == 'POST':

		if request.POST.get("Submit") == "notification_read":
			notification = Param??tre.objects.get(id=2)
			notification.release_notification = False
			notification.save()
			return redirect(f"/{lang}/")

		if request.POST.get("Submit") == "email_confirmation_read":
			notification = Param??tre.objects.get(id=3)
			notification.email_notification = False
			notification.email_notification_list = None
			notification.save()
			return redirect(f"/{lang}/")

		if request.POST.get("Submit") == "delete":
			disable_donation = Donation.objects.get(id=int(request.POST["id"]))
			disable_donation.disabled = True
			disable_donation.eligible = False
			disable_donation.save()

			return redirect(f"/{lang}/")

		# confirm receipt
		if request.POST.get("Submit") == "confirm":
			donation = Donation.objects.get(id=int(request.POST["id"]))
			donation.pdf = True
			donation.save()
			receipt = Re??usFiscaux()
			receipt.save()
			receipt.contact = donation.contact
			receipt.date_created = datetime.date.today()
			receipt.receipt_type = ('I','Individual')
			receipt.file_name = f"{receipt.id}_{'_'.join(str(donation.contact.profile.name).split(' '))}_{str(donation.date_donated)}_Individuel_{donation.id}.pdf"
			receipt.donation_list = [donation.id]
			receipt.cancel = False
			receipt.save()

			create_individual_receipt.delay(receipt.id, donation.id, receipt.file_name)

			if request.POST.get("email") == 'true':
				e = Param??tre.objects.get(id=3)
				path = f"/media/re??us/{receipt.file_name}"
				body = e.body.replace("R_ID", str(receipt.id))
				if e.email_subject:
					subject = e.email_subject.replace("R_ID", str(receipt.id))
					subject = subject.replace("AAAA", str(datetime.date.today().year))
				else:
					subject = ""
				send_email.delay(receipt.id, path, receipt.contact.profile.email, subject, body, 1, cc=e.cc, bcc=e.bcc)
				email_confirmation.delay(1, [(receipt.contact.id, receipt.id)])
			return redirect("/")

		form = DonationForm(request.POST)
		if form.is_valid():
			# create new donation
			donation = Donation()
			try:
				donation.contact = Contact.objects.get(profile__name = form.cleaned_data["contact"])
			except:
				donation.contact = Contact.objects.filter(profile__name = form.cleaned_data["contact"])[0]
			finally:
				donation.contact_name = form.cleaned_data["contact"]
				donation.amount = int(form.cleaned_data["amount_euros"] or 0) + float(form.cleaned_data["amount_cents"])
				donation.date_donated = form.cleaned_data["date_donated"]
				donation.payment_mode = PaymentMode.objects.get(payment_mode = form.cleaned_data["payment_mode"])
				donation.payment_mode_name = form.cleaned_data["payment_mode"]
				donation.organisation = Organisation.objects.get(name = form.cleaned_data["organisation"])
				donation.organisation_name = form.cleaned_data["organisation"]
				donation.donation_type = DonationType.objects.filter(name = form.cleaned_data["donation_type"].split(" - ")[0], organisation=donation.organisation)[0]
				donation.donation_type_name = form.cleaned_data["donation_type"].split(" - ")[0]
				donation.nature_du_don = NatureDuDon.objects.get(name = form.cleaned_data["nature_du_don"])
				donation.nature_du_don_name = form.cleaned_data["nature_du_don"]
				donation.forme_du_don = FormeDuDon.objects.get(name = form.cleaned_data["forme_du_don"])
				donation.forme_du_don_name = form.cleaned_data["forme_du_don"]
				donation.eligible = (donation.organisation, donation.donation_type) in [(e.organisation, e.donation_type) for e in Eligibility.objects.all()]
				donation.save()

			if request.POST["Submit"] == "update":
				disable_donation = Donation.objects.get(id=int(request.POST["id"]))
				disable_donation.disabled = True
				disable_donation.eligible = False
				disable_donation.save()

			return redirect(f"/{lang}/")

		else:
			form_values["errors"] = True
			for error in form.errors:
				if error == "donation_type" and len(form.data['donation_type'].split(" - ")) > 1:
					if form.data['organisation'] != form.data['donation_type'].split(" - ")[1][1:-1]:
						form_values["errorlist"]["donation_type_non_corresponding"] = True
				form_values["errorlist"][error] = "is-invalid"
			form.fields["contact"].initial = request.POST["contact"]
			form.fields["date_donated"].initial = request.POST["date_donated"]
			form.fields["amount_euros"].initial = request.POST["amount_euros"]
			form.fields["amount_cents"].initial = request.POST["amount_cents"]
			form.fields["payment_mode"].initial = request.POST["payment_mode"]
			form.fields["donation_type"].initial = request.POST["donation_type"]
			form.fields["organisation"].initial = request.POST["organisation"]
			form.fields["nature_du_don"].initial = request.POST["nature_du_don"]
			form.fields["forme_du_don"].initial = request.POST["forme_du_don"]

			scroll = int(float(request.POST["scroll"] or 0))
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
	elif request.method == "GET":
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
				form.fields["organisation"].initial = "" if donation.organisation == None else donation.organisation.name
				form.fields["donation_type"].initial = "" if donation.donation_type == None else donation.donation_type.name + f" - ({form.fields['organisation'].initial})"
				form.fields["nature_du_don"].initial = NatureDuDon.objects.get(default_value=True).name
				form.fields["forme_du_don"].initial = FormeDuDon.objects.get(default_value=True).name
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
						"email_address": donation.contact.profile.email,
					}

			scroll = int(float(request.GET["scroll"] or 0))
			collapse = request.GET["collapse"]
			if collapse == "collapse_show":
				collapse = "collapse show"

		file_name_extension = ""
		# filter requests
		for key, value in request.GET.items():
			if key in initial_filter_values.keys() and value not in ("",None,"-----"):
				initial_filter_values[key] = value
				file_name_extension += f"_{'_'.join('-'.join(value.split('/')[::-1]).split(' '))}"
				if key == "contact":
					donations = donations.filter(contact_name=value)
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
					donations = donations.filter(payment_mode_name=value)
				if key == "donation_type":
					donations = donations.filter(donation_type_name=value)
				if key == "organisation":
					donations = donations.filter(organisation_name=value)

		# if exporting
		if request.GET.get("Submit") == "export_xls" or request.GET.get("Submit") == "export_csv":
			columns = ["N??", "Nom", "Date du don", "Montant", "Mode de Paiement", "Type de don", "Organisation", "Forme du don", "Nature du Don"]
			data = [[donation.id, donation.contact.profile.name, str(donation.date_donated), 
				float(donation.amount), donation.payment_mode.payment_mode, 
				donation.donation_type.name, donation.organisation.name, 
				donation.forme_du_don_name, donation.nature_du_don_name] 
				for donation in donations]
			# export_xls:
			if request.GET.get("Submit") == "export_xls":
				return export_xls("Dons", data, columns, file_name_extension)
			# export csv
			if request.GET.get("Submit") == "export_csv":
				return export_csv("Dons", data, file_name_extension)
			
		scroll = int(float(request.GET.get("scroll") or 0))
		collapse = request.GET.get("collapse")
		if collapse == "collapse_show":
			collapse = "collapse show"
		else:
			collapse = "collapse"

				
	# context after filter
	donation_count_filter = donations.count()
	total_donated_filter = sum([d.amount for d in donations])
	donation_types = list(set([(don.organisation_name, don.donation_type_name) for don in Donation.objects.all()]))
	donation_types = json.dumps(donation_types)
	receipt_trigger_notification = Param??tre.objects.get(id=2).release_notification
	email_notification = Param??tre.objects.get(id=3).email_notification
	if Param??tre.objects.get(id=3).email_notification_list not in ("", None):
		email_notification_list = eval(Param??tre.objects.get(id=3).email_notification_list)
	else:
		email_notification_list = ""

	# load partial donations for quicker load time
	if request.GET.get("order_by_form") == "true":
		if request.GET.get("page_number"):
			server_page = int(request.GET.get("page_number"))
		else:
			server_page = 1
		if len(list(filter(lambda x: request.GET.get(f'order_by_{x}'),["id","contact","date","amount","mode","type","org"]))) == 1:
			order_by = list(filter(lambda x: request.GET.get(f'order_by_{x}'),["id","contact","date","amount","mode","type","org"]))[0]
		else:
			order_by = "id"
		direction = request.GET.get(f'order_by_{order_by}').replace("asc","").replace("desc","-") or ""
		order_by_new = order_by.replace('contact','contact_name').replace('date','date_donated').replace('mode','payment_mode_name').replace('org','organisation_name').replace('type','donation_type_name')
		order_for_table = json.dumps(dict({order_by: request.GET.get(f'order_by_{order_by}')}, **dict(filter(lambda y: y[1][0] and y[1][0] != "-----" and y[0] not in ("Submit","scroll","collapse"), list(dict(request.GET).items())))))
		total_donations_for_table = donations.count()
		if server_page == math.ceil(total_donations_for_table/20):
			donations = donations.order_by(f'{direction}{order_by_new}')[total_donations_for_table-100:]
		elif server_page == 5:
			donations = donations.order_by(f'{direction}{order_by_new}')[:100]
		else:
			donations = donations.order_by(f'{direction}{order_by_new}')[((server_page-1)*20):((server_page-1)*20)+100]
		scroll = int(float(request.GET["scroll"] or 0))
		collapse = request.GET["collapse"]
		if collapse == "collapse_show":
			collapse = "collapse show"
	else:
		server_page = 1
		total_donations_for_table = donations.count()
		donations = donations.order_by(f'-id')[:100]
		order_for_table = json.dumps(dict({"id": "desc"}, **dict(filter(lambda y: y[1][0] and y[1][0] != "-----" and y[0] not in ("Submit","scroll","collapse"), list(dict(request.GET).items())))))
		scroll = 0
		collapse = "collapse show"


	context = {
		'show_modal_pdf': show_modal_pdf,
		'pdf_path': pdf_path,
		'initial_filter_values': initial_filter_values,
		'collapse': collapse,
		'scroll': scroll,
		'tags': tags,
		'donations': donations,
		'order_for_table': order_for_table,
		'total_donations_for_table': total_donations_for_table,
		'server_page': server_page,
		'donations_count': donations_count,
		'total_donated': total_donated,
		'donation_count_filter': donation_count_filter,
		'total_donated_filter': total_donated_filter,
		'form': form,
		'form_values': form_values,
		'donation_types': donation_types,
		'receipt_trigger_notification': receipt_trigger_notification,
		'email_notification': email_notification,
		'email_notification_list': email_notification_list,
		'language': language_text(lang=lang),
	}
	return render(request, 'dashboard.html', context)

@login_required(login_url='/fr/login')
def contact(request, pk, lang, change=None):

	# language change whilst mainting current url
	if change != None:
		return redirect(f'/{change}/contact/{pk}')

	if request.POST.get("Submit") == "notification_read":
		return redirect(f"/{lang}/contact/{pk}/")

	if request.POST.get("Submit") == "email_confirmation_read":
		notification = Param??tre.objects.get(id=3)
		notification.email_notification = False
		notification.email_notification_list = None
		notification.save()
		return redirect(f"/{lang}/contact/{pk}/")

	# context
	contact = Contact.objects.get(profile__seminar_desk_id=pk)
	address = contact.profile.primary_address
	address = list(filter(lambda x: x, [address["careOf"], address["streetAddress"], address["streetAddress2"], address["city"], address["zipCode"], address["province"], address["countryCode"]]))
	tags = contact.tags.all()
	donations = Donation.objects.filter(contact__profile__seminar_desk_id=contact.profile.seminar_desk_id).filter(disabled=False).order_by('-id')
	donations_count = donations.count()
	total_donated = sum([d.amount for d in donations])
	receipt_trigger_notification = Param??tre.objects.get(id=2).release_notification
	email_notification = Param??tre.objects.get(id=3).email_notification
	if Param??tre.objects.get(id=3).email_notification_list not in ("", None):
		email_notification_list = eval(Param??tre.objects.get(id=3).email_notification_list)
	else:
		email_notification_list = ""

	context = {
		'tags': tags,
		'address': address,
		'contact': contact,
		'donations': donations,
		'donations_count': donations_count,
		'total_donated': total_donated,
		"receipt_trigger_notification": receipt_trigger_notification,
		'email_notification': email_notification,
		'email_notification_list': email_notification_list,
		'sdid': SDID,
		'language': language_text(lang=lang),
	}
	return render(request, 'contact.html', context)

@login_required(login_url='/fr/login')
def donators(request, lang, change=None):
	
	# language change whilst mainting current url
	if change != None:
		return redirect(f'/{change}/donators')

	if request.POST.get("Submit") == "notification_read":
		notification = Param??tre.objects.get(id=2)
		notification.release_notification = False
		notification.save()
		return redirect(f"/{lang}/donators/")

	if request.POST.get("Submit") == "email_confirmation_read":
		notification = Param??tre.objects.get(id=3)
		notification.email_notification = False
		notification.email_notification_list = None
		notification.save()
		return redirect(f"/{lang}/donators/")

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
	file_name_extension = ""
	for key, value in request.GET.items():
		if key == "Submit":
			continue
		if key == "scroll":
			scroll = int(float(value or 0))
			continue
		if key == "collapse":
			collapse = value
			if collapse == "collapse_show":
				collapse = "collapse show" 
			continue
		if key in initial_filter_values.keys() and value not in ("", None):
			initial_filter_values[key] = value
			file_name_extension += f"_{'_'.join('-'.join(value.split('/')[::-1]).split(' '))}"
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

	# contacts to be used for iteration on the table - this is created after filter
	contacts = list()
	for contact in Contact.objects.all():
		contact_dons = contact.donation_set.all()
		if len(contact_dons) > 0:
			contacts.append({
				"id": contact.profile.seminar_desk_id,
				"name": contact.profile.name,
				"total_donations": len(contact_dons),
				"total_donated": sum([d.amount for d in contact_dons])
			})
	contacts = sorted(contacts, key=lambda x: x["id"])

	# if exporting
	if request.GET.get("Submit") == "export_xls" or request.GET.get("Submit") == "export_csv":
		columns = ["N??", "Nom", "Email", "Montant_total", "Total_de_dons", "Modes de Paiement", "Organisations", "Types de dons", "Nature des dons", "Forme des dons"]
		contacts = set([donation.contact for donation in donations])
		data = [
			[contact.id, contact.profile.name, contact.profile.email, 
			sum([d.amount for d in donations.filter(contact=contact)]), 
			len([d for d in donations.filter(contact=contact)]), 
			", ".join(list(set([d.payment_mode_name for d in donations.filter(contact=contact)]))),
			", ".join(list(set([d.organisation_name for d in donations.filter(contact=contact)]))),
			", ".join(list(set([d.donation_type_name for d in donations.filter(contact=contact)]))),
			", ".join(list(set([d.nature_du_don_name for d in donations.filter(contact=contact)]))),
			", ".join(list(set([d.forme_du_don_name for d in donations.filter(contact=contact)])))] 
		for contact in contacts]
		# export_xls:
		if request.GET.get("Submit") == "export_xls":
			return export_xls("Contacts", data, columns, file_name_extension)
		# export_csv
		if request.GET.get("Submit") == "export_csv":
			return export_csv("Contacts", data, file_name_extension)

	# context after filter 	
	donation_count_filter = donations.count()
	total_donated_filter = sum([d.amount for d in donations])
	receipt_trigger_notification = Param??tre.objects.get(id=2).release_notification
	email_notification = Param??tre.objects.get(id=3).email_notification
	if Param??tre.objects.get(id=3).email_notification_list not in ("", None):
		email_notification_list = eval(Param??tre.objects.get(id=3).email_notification_list)
	else:
		email_notification_list = ""

	# load partial contacts for quicker load time
	if request.GET.get("order_by_form") == "true":
		if request.GET.get("page_number"):
			server_page = int(request.GET.get("page_number"))
		else:
			server_page = 1
		if len(list(filter(lambda x: request.GET.get(f'order_by_{x}'),["id","contact","total_amount","total_number"]))) == 1:
			order_by = list(filter(lambda x: request.GET.get(f'order_by_{x}'),["id","contact","total_amount","total_number"]))[0]
		else:
			order_by = "id"
		direction = request.GET.get(f'order_by_{order_by}').replace("asc","False").replace("desc","True") or "False"
		order_by_new = order_by.replace('contact','name').replace("total_amount","total_donated").replace("total_number","total_donations")
		order_for_table = json.dumps(dict({order_by: request.GET.get(f'order_by_{order_by}')}, **dict(filter(lambda y: y[1][0] and y[1][0] != "-----" and y[0] not in ("Submit","scroll","collapse"), list(dict(request.GET).items())))))
		total_contacts_for_table = len(contacts)
		if server_page == math.ceil(total_contacts_for_table/20):
			contacts.sort(reverse=eval(direction), key=lambda x: x[order_by_new])
			contacts = contacts[total_contacts_for_table-100:]
		elif server_page == 5:
			contacts.sort(reverse=eval(direction), key=lambda x: x[order_by_new])
			contacts = contacts[:100]
		else:
			contacts.sort(reverse=eval(direction), key=lambda x: x[order_by_new])
			contacts = contacts[((server_page-1)*20):((server_page-1)*20)+100]
		scroll = int(float(request.GET["scroll"] or 0))
		collapse = request.GET["collapse"]
		if collapse == "collapse_show":
			collapse = "collapse show"
	else:
		server_page = 1
		total_contacts_for_table = Contact.objects.all().count()
		contacts.sort(reverse=True, key=lambda x: x["id"])
		contacts = contacts[:100]
		order_for_table = json.dumps(dict({"id": "desc"}, **dict(filter(lambda y: y[1][0] and y[1][0] != "-----" and y[0] not in ("Submit","scroll","collapse"), list(dict(request.GET).items())))))
		scroll = 0
		collapse = "collapse show"

	context = {
		'pdf_path': pdf_path,
		'initial_filter_values': initial_filter_values,
		'collapse': collapse,
		'contacts': contacts,
		'order_for_table': order_for_table,
		'total_contacts_for_table': total_contacts_for_table,
		'server_page': server_page,
		'scroll': scroll,
		'is_invalid': is_invalid,
		'tags': tags,
		'donations': donations,
		'donations_count': donations_count,
		'total_donated': total_donated,
		'donation_count_filter': donation_count_filter,
		'total_donated_filter': total_donated_filter,
		'receipt_trigger_notification': receipt_trigger_notification,
		'email_notification': email_notification,
		'email_notification_list': email_notification_list,
		'language': language_text(lang=lang),
	}
	return render(request, 'donators.html', context)

@login_required(login_url='/fr/login')
def pdf_receipts(request, lang, change=None):
	if change != None:
		return redirect(f'/{change}/pdf_receipts')

	# update receipts
	file_storage_check()

	if request.POST.get("Submit") == "notification_read":
		notification = Param??tre.objects.get(id=2)
		notification.release_notification = False
		notification.save()
		return redirect(f"/{lang}/pdf_receipts/")

	if request.POST.get("Submit") == "email_confirmation_read":
		notification = Param??tre.objects.get(id=3)
		notification.email_notification = False
		notification.email_notification_list = None
		notification.save()
		return redirect(f"/{lang}/pdf_receipts/")

	# initial filter values
	initial_filter_values = {
		"contact": "",
		"date_donated_gte": "",
		"date_donated_lte": "",
		"file_name": "",
		"receipt_type": "",
		"canceled": True,
	}

	unadulterated_receipts = Re??usFiscaux.objects.all()
	email_content = {"true": False, "id": "", "email": "","cc": "","bcc": "","subject": "", "file": ""}
	if request.GET.get("send_email") not in ("", None):
		email_content["true"] = True
		email_content["id"] = unadulterated_receipts.get(id=request.GET.get("send_email")).id
		email_content["email"] = unadulterated_receipts.get(id=request.GET.get("send_email")).contact.profile.email
		email_content["subject"] = ""
		email_content["cc"] = "" if Param??tre.objects.get(id=3).cc == None else Param??tre.objects.get(id=3).cc
		email_content["bcc"] = "" if Param??tre.objects.get(id=3).bcc == None else Param??tre.objects.get(id=3).bcc
		email_content["file"] = unadulterated_receipts.get(id=request.GET.get("send_email")).file_name

	if request.method == "POST":
		if request.POST["Submit"] not in ("", None):
			receipt = Re??usFiscaux.objects.get(id=request.POST["Submit"])
			send_to = request.POST["email"]
			cc = request.POST["cc"]
			bcc = request.POST["bcc"]
			body = request.POST["message"] + "\n\n"
			body = body.replace("R_ID", str(receipt.id))
			path = f"/media/re??us/{receipt.file_name}"
			subject = request.POST["subject"]
			send_email.delay(receipt.id, path, send_to, subject, body, 1, cc=cc, bcc=bcc)
			email_confirmation.delay(1, [(receipt.contact.id, receipt.id)])
			return redirect(f'{lang}/pdf_receipts/')

	tags = Tag.objects.all()
	donations = Donation.objects.filter(disabled = False)	
	donations_count = donations.count()
	total_donated = sum([d.amount for d in donations])
	donation_count_filter = donations_count
	total_donated_filter = sum([d.amount for d in donations])
	if request.GET.get("canceled") == 'false':
		initial_filter_values["canceled"] = False
		donation_receipts = Re??usFiscaux.objects.filter(cancel=False).order_by("-id")
	else:
		donation_receipts = unadulterated_receipts
	donation_types = []
	for donation_receipt in donation_receipts:
		try:
			receipt_type = eval(donation_receipt.receipt_type)[1]
			if lang == "fr":
				receipt_type = receipt_type[0:-2] + "e" + receipt_type[-1]
			donation_types.append([donation_receipt.id, receipt_type])
		except:
			donation_types.append([donation_receipt.id, None])

	scroll = int(float(request.GET.get("scroll") or 0))

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
		file_name = Re??usFiscaux.objects.get(id=int(i)).file_name
		dbx = dropbox.Dropbox(DROPBOX_OAUTH2_TOKEN)
		m, res = dbx.files_download(f'/media/re??us/{file_name}')
		return HttpResponse(io.BytesIO(res.content), content_type='application/pdf')

	else:
		show_modal_pdf = False
	if request.GET.get("download_pdf"):
		i = request.GET.get("download_pdf")
		file_name = Re??usFiscaux.objects.get(id=int(i)).file_name
		dbx = dropbox.Dropbox(DROPBOX_OAUTH2_TOKEN)
		m, res = dbx.files_download(f"/media/re??us/{file_name}")
		response = HttpResponse(io.BytesIO(res.content), content_type='application/pdf')
		response['Content-Disposition'] = f'attachment; filename={file_name}'
		return response

	try:
		file_name
	except:
		file_name = ""
	receipt_trigger_notification = Param??tre.objects.get(id=2).release_notification
	annual_processing = Param??tre.objects.get(id=2).release_date.toordinal() <= datetime.date.today().toordinal()
	email_notification = Param??tre.objects.get(id=3).email_notification
	if Param??tre.objects.get(id=3).email_notification_list not in ("", None):
		email_notification_list = eval(Param??tre.objects.get(id=3).email_notification_list)
	else:
		email_notification_list = ""

	# load partial receipts for quicker load time
	if request.GET.get("order_by_form") == "true":
		if request.GET.get("page_number"):
			server_page = int(request.GET.get("page_number"))
		else:
			server_page = 1
		if len(list(filter(lambda x: request.GET.get(f'order_by_{x}'),["id","contact","date","type","name"]))) == 1:
			order_by = list(filter(lambda x: request.GET.get(f'order_by_{x}'),["id","contact","date","type","name"]))[0]
		else:
			order_by = "id"
		direction = request.GET.get(f'order_by_{order_by}').replace("asc","").replace("desc","-") or ""
		order_by_new = order_by.replace("name","file_name").replace('contact','contact_name').replace('date','date_created').replace('type','receipt_type')
		order_for_table = json.dumps(dict({order_by: request.GET.get(f'order_by_{order_by}')}, **dict(filter(lambda y: y[1][0] and y[1][0] != "-----" and y[0] not in ("Submit","scroll","collapse"), list(dict(request.GET).items())))))
		total_receipts_for_table = donation_receipts.count()
		if server_page == math.ceil(total_receipts_for_table/20):
			donation_receipts = donation_receipts.order_by(f'{direction}{order_by_new}')[total_receipts_for_table-100:]
		elif server_page == 5:
			donation_receipts = donation_receipts.order_by(f'{direction}{order_by_new}')[:100]
		else:
			donation_receipts = donation_receipts.order_by(f'{direction}{order_by_new}')[((server_page-1)*20):((server_page-1)*20)+100]
		scroll = int(float(request.GET["scroll"] or 0))
		collapse = request.GET["collapse"]
		if collapse == "collapse_show":
			collapse = "collapse show"
	else:
		server_page = 1
		total_receipts_for_table = donation_receipts.count()
		donation_receipts = donation_receipts.order_by(f'-id')[:100]
		order_for_table = json.dumps({"id": "desc"})
		order_for_table = json.dumps(dict({"id": "desc"}, **dict(filter(lambda y: y[1][0] and y[1][0] != "-----" and y[0] not in ("Submit","scroll","collapse"), list(dict(request.GET).items())))))
		scroll = 0
		collapse = "collapse show"

	context = {
		'tags': tags,
		'donations': donations,
		'donations_count': donations_count,
		'total_donated': total_donated,
		'total_donated_filter': total_donated_filter,
		'donation_count_filter': donation_count_filter,
		'initial_filter_values': initial_filter_values,
		'donation_receipts': donation_receipts,
		'order_for_table': order_for_table,
		'total_receipts_for_table': total_receipts_for_table,
		'server_page': server_page,
		'donation_types': donation_types,
		'show_modal_pdf': show_modal_pdf,
		'scroll': scroll,
		'email_content': email_content,
		'receipt_trigger_notification': receipt_trigger_notification,
		'annual_processing': annual_processing,
		'email_notification': email_notification,
		'email_notification_list': email_notification_list,
		'language': language_text(lang=lang),
	}
	return render(request, 'pdf_receipts.html', context)

@login_required(login_url='/fr/login')
def confirm_annual(request, lang, change=None):

	if change != None:
		return redirect(f'/{change}/recusannuels')

	date_range = (
		Param??tre.objects.get(id=1).date_range_start, 
		Param??tre.objects.get(id=1).date_range_end
	)
	donations = Donation.objects.filter(disabled=False)\
		.filter(pdf=False)\
		.filter(eligible=True)\
		.filter(date_donated__range=date_range)

	if request.method == "POST":
		if request.POST.get("orgs") not in ("", None):
			orgs = [int(i) for i in request.POST.get("orgs").split(",")]
		else:
			return redirect(f'/{lang}/re??usannuels/')
		# getting contacts and donations to be processed
		if request.POST.get("contacts_checked") == "on":
			dtbp = donations
			if request.POST.get("contacts") not in ("", None):
				sdbp = [int(i) for i in request.POST.get("contacts").split(",")]
				dtbp = donations.exclude(contact__profile__seminar_desk_id__in=sdbp)
		else:
			if request.POST.get("contacts") not in ("", None):
				sdbp = [int(i) for i in request.POST.get("contacts").split(",")]
				dtbp = donations.filter(contact__profile__seminar_desk_id__in=sdbp) 
			else:
				return redirect(f'/{lang}/recusannuels/')

		# creating receipts and sending emails
		seminar_desk_ids = list(set([d.contact.profile.seminar_desk_id for d in dtbp]))
		for o in orgs:
			email_statuses = []
			for t, s_id in enumerate(seminar_desk_ids):
				annual_donations = dtbp.filter(contact__profile__seminar_desk_id=s_id).filter(organisation__id=o)
				if len(annual_donations) > 0:
					receipt = Re??usFiscaux()
					receipt.save()
					receipt.contact = Contact.objects.get(profile__seminar_desk_id=s_id)
					receipt.date_created = datetime.date.today()
					receipt.receipt_type = ('A','Annual')
					receipt.file_name = f"{receipt.id}_{'_'.join(str(Contact.objects.get(profile__seminar_desk_id=s_id)).split(' '))}_{str(date_range[0])}_{str(date_range[1])}_Annuel.pdf"
					receipt.donation_list = [d.id for d in annual_donations]
					receipt.cancel = False
					receipt.save()
					create_annual_receipt.delay(
						receipt.id, 
						receipt.contact.id, 
						receipt.donation_list, 
						[str(date) for date in date_range], 
						receipt.file_name,
					)
					for donation in annual_donations:
						donation.pdf = True
						donation.save()
					e = Param??tre.objects.get(id=3)
					path = f"/media/re??us/{receipt.file_name}"
					if e.email_subject:
						subject = e.email_subject.replace("R_ID", str(receipt.id))
						subject = subject.replace("AAAA", str(datetime.date.today().year))
					else:
						subject = ""
					body = e.body.replace("R_ID", str(receipt.id))
					if receipt.contact.profile.email not in ("", None):
						#send_email.delay(receipt.id, path, receipt.contact.profile.email, subject, body, t+1, cc=e.cc, bcc=e.bcc)
						email_statuses.append((receipt.contact.id, receipt.id))
			#email_confirmation.delay(len(seminar_desk_ids)+1, email_statuses)
		return redirect(f"/{lang}/")

	prof_for_orgs = [{"id": o.id,"name": o.name, "contacts": list(set([d.contact.profile.seminar_desk_id for d in donations.filter(organisation=o)]))} for o in Organisation.objects.all()]
	orgs = [{
		"id": org["id"],
		"name": org["name"],
		"contacts": [{
			"id": str(p.seminar_desk_id), 
			"name": p.name, 
			"email": p.email or "", 
			"address": format_address(p.primary_address), 
			"donations": [{
				"id": str(d.id),
				"date_donated": str(d.date_donated), 
				"amount": str(d.amount),
				"organisation": d.organisation_name,
				"donation_type_name": d.donation_type_name,
				"payment_mode": d.payment_mode_name,
				"forme_du_don_name": d.forme_du_don_name,
				"nature_du_don_name": d.nature_du_don_name,
			} for d in p.contact_set.all()[0].donation_set.filter(date_donated__range=date_range).filter(eligible=True).filter(pdf=False).filter(organisation__id=org["id"])],
		} for p in Profile.objects.filter(seminar_desk_id__in=org["contacts"])]
	} for org in prof_for_orgs]

	orgs_repr_json = json.dumps([{"id": o.id, "name": o.name} for o in Organisation.objects.all()])
	orgs_json = json.dumps(orgs)

	context = {
		'date_range': date_range,
		'orgs': orgs,
		'orgs_json': orgs_json,
		'orgs_repr_json': orgs_repr_json,
		'language': language_text(lang=lang),
	}
	return render(request, 'confirm_annual_donations.html', context)
