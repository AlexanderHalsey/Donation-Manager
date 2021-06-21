from django.shortcuts import render, redirect
from .models import *
from .forms import DonationForm
import re

# Create your views here.
def dashboard(request):
	# form
	form = DonationForm()
	if request.method == 'POST':

		if request.POST["Submit"] == "delete":
			disable_donation = Donation.objects.get(id=int(request.POST["id"]))
			disable_donation.disabled = True
			disable_donation.save()
			redirect("/")

		form = DonationForm(request.POST)

		print(form.errors)

		if form.is_valid():
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

	# context 
	tags = Tag.objects.all()
	donations = Donation.objects.all().order_by('-date_donated')
	donations_count = donations.filter(disabled=False).count()
	total_donated = sum([d.amount for d in donations.filter(disabled=False)])
	
	# front-end functionality
	scroll = 0 # to load with page scroll number so the page appears static on request
	collapse = 'collapse' # to register collapse status of filter collapse button
	form_values = {
		"title": "New", 
		"colour": "primary",
		"button": "Submit",
		"update": False,
		"delete": False,
		"type": "create",
		"i": None,
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
	}

	# GET requests
	for key,value in request.GET.items():
		# update / delete requests
		if key == "csrfmiddlewaretoken":
			continue
		if "update" in key or "delete" in key:
			i = re.search(r'\d+', key).group()
			donation = Donation.objects.get(id=i)
			function = re.search(r'\w+', key).group()
			if function == "delete":
				form_values["i"] = i
				form_values["delete"] = True
			elif function == "update":
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
					"i": i,
				}
			scroll = int(re.search(r'\d*',value).group() or 0)
			collapse = re.search(r'\D+', value).group()
			if collapse == "collapse_show":
				collapse = "collapse show" 
		# filter requests
		else:
			if key == "scroll_value":
				scroll = int(re.search(r'\d*', value).group() or 0)
				collapse = re.search(r'\D+', value).group()
				if collapse == "collapse_show":
					collapse = "collapse show" 
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
	donation_count_filter = donations.filter(disabled=False).count()
	total_donated_filter = sum([d.amount for d in donations.filter(disabled=False)])

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
	tags = [(colours[str(tag.id%20)][0],colours[str(tag.id%20)][1],tag.tag) for tag in contact.tags.all()]
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
