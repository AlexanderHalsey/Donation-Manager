from django.shortcuts import render, redirect
from django.http import HttpResponse
from donations.settings import BASE_DIR
from .models import *
from .utils import *
from .forms import DonationForm
import datetime
import num2words
import os



# Create your views here.
def dashboard(request):
	# intial form_values
	form_values = {
		"title": "New", 
		"colour": "primary",
		"button": "Submit",
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

			return redirect("/")

		form = DonationForm(request.POST)

		if form.is_valid():
			pdf = False
			# if certain conditions are met, an email confirmation is forwarded my way
			if form.cleaned_data["donation_type"] == "DonationType2" and form.cleaned_data["organisation"] == "CBM":
				pdf = True
				address = eval(Contact.objects.get(name=form.cleaned_data["contact"]).postal_address)
				if len(address) == 5:
					address = address[:2]+[address[2]+", "+address[3]]+[address[4]]
				amount = ",".join(("%.2f" % (int(form.cleaned_data["amount_euros"] or 0) + float(form.cleaned_data["amount_cents"]))).split("."))
				text_variables = {
					"institut_address": ["Institut Vajra Yogini pour l'Epanouissement de la Sagesse", "LIEU DIT CLAUZADE", "81500 MARZENS"],
					"donation_id": [str(len(Donation.objects.all())+1)],
					"organisation_object": ["Object:", "Exercise du culte bouddhiste", "Association Culturelle régie par la loi du 9 décembre 1905 du 16 mars 1906. Ce reçu donne droit à une déduction fiscale conformément à l'arrête préfectoral du Tarn du 30 décemebre 2003."],
					"contact": [form.cleaned_data["contact"]], 
					"contact_address": address,
					"date_donated": ["/".join(str(form.cleaned_data["date_donated"]).split("-")[::-1])],
					"amount": ["€ "+amount],
					"other_donation_variables": [num2words.num2words(int(form.cleaned_data["amount_euros"] or 0) + float(form.cleaned_data["amount_cents"]), lang="fr").capitalize() + " euros", "Espèces", "Déclaration de don manuel", "Numéraire"], 
					"institut_village": ["MARZENS"],
					"date_today": ["/".join(str(datetime.date.today()).split("-")[::-1])],
					"president": ["Charles Trébaol"],
				}
				images = {
					"institution": "/dm_page/static/png/IVY_Logo_carré.png",
					"signature": "/dm_page/static/png/signature_Charles_Trebaol.png",
				}
				pdf_path = pdf_receipt(text_variables, images)
				send_email(pdf_path, text_variables["donation_id"][0])
			donation = Donation(
				contact = Contact.objects.get(
					name = form.cleaned_data["contact"]
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
					organisation = form.cleaned_data["organisation"]
				),
				disabled = False,
				pdf = pdf,
				pdf_path = pdf_path,
			)
			donation.save()

			if request.POST["Submit"] == "update":
				disable_donation = Donation.objects.get(id=int(request.POST["id"]))
				disable_donation.disabled = True
				disable_donation.save()

			return redirect("/")

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
					form_values["title"] = "Update"
					form_values["colour"] = "success"
					form_values["button"] = "Update"
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
				form.fields["contact"].initial = donation.contact.name
				form.fields["date_donated"].initial = "" if donation.date_donated == None else "/".join(str(donation.date_donated).split("-")[::-1])
				form.fields["amount_euros"].initial = "" if str(donation.amount).split(".")[0] == "0" else str(donation.amount).split(".")[0]
				form.fields["amount_cents"].initial = "."+str("{:.2f}".format(donation.amount)).split(".")[1]
				form.fields["payment_mode"].initial = "" if donation.payment_mode == None else donation.payment_mode.payment_mode
				form.fields["donation_type"].initial = "" if donation.donation_type == None else donation.donation_type.donation_type
				form.fields["organisation"].initial = "" if donation.organisation == None else donation.organisation.organisation
				# donation_form - update 
				form_values = {
					"title": "Update",
					"colour": "success",
					"button": "Update",
					"update": True,
					"delete": False,
					"type": "update",
					"i": value,
				}

			scroll = int(request.GET["scroll"] or 0)
			collapse = request.GET["collapse"]
			if collapse == "collapse_show":
				collapse = "collapse show"

		if request.GET.get("view_pdf"):
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
			return response

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
						donations = donations.filter(contact__name=value)
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
						donations = donations.filter(organisation__organisation=value)
			columns = ["ID", "Name", "Date Donated", "Amount", "Payment Mode", "Donation Type", "Organisation"]
			data = [[donation.id, donation.contact.name, str(donation.date_donated), 
				float(donation.amount), (None if donation.payment_mode == None else donation.payment_mode.payment_mode), 
				(None if donation.donation_type == None else donation.donation_type.donation_type), (None if donation.organisation == None else donation.organisation.organisation)] 
				for donation in donations]
			# export_xls:
			if request.GET.get("Submit") == "export_xls":
				return export_xls("Donations", data, columns, file_name_extension)
			if request.GET.get("Submit") == "export_csv":
				return export_csv("Donations", data, file_name_extension)

			scroll = int(request.GET["scroll"] or 0)
			collapse = request.GET["collapse"]
			if collapse == "collapse_show":
				collapse = "collapse show"

				
	# context after filter 	
	donation_count_filter = donations.count()
	total_donated_filter = sum([d.amount for d in donations])

	# redirect when filter is empty
	if list(filter(lambda x: x, [request.GET.get(item) for item in request.GET])) in ([], ["Type to search..."]) and request.get_full_path_info() != "/":
		return redirect("/")

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
	}
	return render(request, 'dashboard.html', context)

def contact(request, pk):

	# context
	contact = Contact.objects.get(id=pk)
	address = eval(contact.postal_address)
	tags = contact.tags.all()
	donations = Donation.objects.filter(contact__name=contact.name)
	donations_count = donations.count()
	total_donated = sum([d.amount for d in donations])

	context = {
		'tags': tags,
		'address': address,
		'contact': contact,
		'donations': donations,
		'donations_count': donations_count,
		'total_donated': total_donated,
	}
	return render(request, 'contact.html', context)

def donators(request):

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

	if request.GET.get("view_pdf"):
		i = request.GET.get("view_pdf")
		listdir = os.listdir("dm_page/static/pdf/receipts/")
		pdf_path = list(filter(lambda x: x.split(".pdf")[0][-len(i):] == i, listdir))[0]

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
		data = [[contact.id, contact.name, contact.email, 
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
		"name": contact.name,
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
	}
	return render(request, 'donators.html', context)

def pdf(request):
	donations = Donation.objects.all()
	for donation in donations:
		if donation.donation_type != None and donation.organisation != None:
			if donation.donation_type.donation_type == "DonationType2" and donation.organisation.organisation == "CBM":
				donation.pdf = True
				address = eval(donation.contact.postal_address)
				if len(address) == 5:
					address = address[:2]+[address[2]+", "+address[3]]+[address[4]]
				text_variables = {
					"institut_address": ["Institut Vajra Yogini pour l'Epanouissement de la Sagesse", "LIEU DIT CLAUZADE", "81500 MARZENS"],
					"donation_id": [str(donation.id)],
					"organisation_object": ["Object:", "Exercise du culte bouddhiste", "Association Culturelle régie par la loi du 9 décembre 1905 du 16 mars 1906. Ce reçu donne droit à une déduction fiscale conformément à l'arrête préfectoral du Tarn du 30 décemebre 2003."],
					"contact": [donation.contact.name], 
					"contact_address": address,
					"date_donated": ["/".join(str(donation.date_donated).split("-")[::-1])],
					"amount": ["€ "+ str(donation.amount)],
					"other_donation_variables": [num2words.num2words(int(donation.amount or 0), lang="fr").capitalize() + " euros", "Espèces", "Déclaration de don manuel", "Numéraire"], 
					"institut_village": ["MARZENS"],
					"date_today": ["/".join(str(datetime.date.today()).split("-")[::-1])],
					"president": ["Charles Trébaol"],
				}
				images = {
					"institution": "/dm_page/static/png/IVY_Logo_carré.png",
					"signature": "/dm_page/static/png/signature_Charles_Trebaol.png",
				}
				donation.pdf_path = pdf_receipt(text_variables, images).split("/receipts/")[1]
				donation.save()
	return dashboard(request)

