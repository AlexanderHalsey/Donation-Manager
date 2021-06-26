from django.shortcuts import render, redirect
from .models import *
from .forms import DonationForm
import smtplib

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
			# if certain conditions are met, an email confirmation is forwarded my way
			if form.cleaned_data["donation_type"] == "DonationType2" and form.cleaned_data["organisation"] == "CBM":
				smtp_object = smtplib.SMTP('smtp.gmail.com',587)
				smtp_object.ehlo()
				smtp_object.starttls()
				smtp_object.login('alex.halsey5@gmail.com','ovwiymnjotfiacvu')
				message = f'''
				Contact: {form.cleaned_data["contact"]}\n
				Date Donated: {form.cleaned_data["date_donated"]}\n
				Amount: {int(form.cleaned_data["amount_euros"])+float(form.cleaned_data["amount_cents"])}\n
				Payment Mode: {form.cleaned_data["payment_mode"]}\n
				Donation Type: {form.cleaned_data["donation_type"]}\n
				Organisation: {form.cleaned_data["organisation"]}\n
				'''
				smtp_object.sendmail('alex.halsey5@gmail.com','alex.halsey@icloud.com',message)

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
			)
			donation.save()

			if request.POST["Submit"] == "update":
				disable_donation = Donation.objects.get(id=int(request.POST["id"]))
				disable_donation.disabled = True
				disable_donation.save()

			return redirect("/")

		else:
			print(request.POST)
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

		# filter requests
		if request.GET.get("Submit") != None:
			if request.GET["Submit"] == "filter":
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

	# context after filter 	
	donation_count_filter = donations.count()
	total_donated_filter = sum([d.amount for d in donations])

	# redirect when filter is empty
	if list(filter(lambda x: x, [request.GET.get(item) for item in request.GET])) in ([], ["Type to search..."]) and request.get_full_path_info() != "/":
		return redirect("/")

	context = {
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
	tags = contact.tags.all()
	donations = Donation.objects.filter(contact__name=contact.name)
	donations_count = donations.count()
	total_donated = sum([d.amount for d in donations])

	context = {
		'tags': tags,
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

	# front-end functionality
	scroll = 0 # to load with page scroll number so the page appears static on request
	collapse = 'collapse show' # to register collapse status of filter collapse button

	# filter requests
	if request.GET.get("Submit") != None:
		if request.GET["Submit"] == "filter":
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

