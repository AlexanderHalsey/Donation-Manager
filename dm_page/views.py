from django.shortcuts import render, redirect
from .models import *
from .forms import DonationForm
from django.http import HttpRequest
from .colours import colours

# Create your views here.
def dashboard(request):
	# form
	form = DonationForm()
	if request.method == 'POST':
		print(request.POST)
		if request.POST["Submit"] == "delete":
			disable_donation = Donation.objects.get(id=int(request.POST["id"]))
			disable_donation.disabled = True
			disable_donation.save()
			redirect("/")
		form = DonationForm(request.POST)
		print(form.errors)
		if form.is_valid():
			if form.cleaned_data["amount_euros"] == None:
				amount_euros = "0"
			else:
				amount_euros = form.cleaned_data["amount_euros"]
			donation = Donation(
				contact = Contact.objects.get(
					name = form.cleaned_data["contact"]
				),
				amount = int(amount_euros) + float(form.cleaned_data["amount_cents"]),
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
		form = DonationForm()
		return redirect("/")

	# context 
	tags = [(colours[str(tag.id%20)][0],colours[str(tag.id%20)][1],tag.tag) for tag in Tag.objects.all()]
	donations = Donation.objects.all().order_by('-date_donated')
	donations_count = donations.filter(disabled=False).count()
	total_donated = sum([d.amount for d in donations.filter(disabled=False)])
	
	# front-end functionality
	scroll = 0
	collapse = 'collapse'
	form_values = {
		"title": "New", 
		"colour": "primary",
		"button": "Submit",
		"update": False,
		"delete": False,
		"type": "create",
		"i": None,
	}

	# GET request for update
	for i in range(1, len(donations)+1):
		if request.GET.get("delete/{i}".format(i=i)) not in (None, ""):
			donation = Donation.objects.get(id=i)
			if 'collapse_show' in request.GET.get("delete/{i}".format(i=i)):
				scroll = int("".join(request.GET.get("delete/{i}".format(i=i)).split('collapse_show')) or 0)
				collapse = 'collapse show'
			elif 'collapse' in request.GET.get("delete/{i}".format(i=i)):
				scroll = int("".join(request.GET.get("delete/{i}".format(i=i)).split('collapse')) or 0)
			form_values["i"] = i
			form_values["delete"] = True
			break
		if request.GET.get("update/{i}".format(i=i)) not in (None, ""):
			donation = Donation.objects.get(id=i)
			if 'collapse_show' in request.GET.get("update/{i}".format(i=i)):
				scroll = int("".join(request.GET.get("update/{i}".format(i=i)).split('collapse_show')) or 0)
				collapse = 'collapse show'
			elif 'collapse' in request.GET.get("update/{i}".format(i=i)):
				scroll = int("".join(request.GET.get("update/{i}".format(i=i)).split('collapse')) or 0)
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
			break

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

	# GET request for filter
	if request.GET.get("contact") not in ("", "Type to search...",None):
		donations = donations.filter(contact__name=request.GET.get("contact"))
		initial_filter_values["contact"] = request.GET.get("contact")
	if request.GET.get("date_donated_gte") not in ("", "DD/MM/YYYY", None):
		date__gte = "-".join(request.GET.get("date_donated_gte").split("/")[::-1])
		initial_filter_values["date_donated_gte"] = request.GET.get("date_donated_gte")
		donations = donations.filter(date_donated__gte=date__gte)
	if request.GET.get("date_donated_lte") not in ("", "DD/MM/YYYY",None):
		date__lte = "-".join(request.GET.get("date_donated_lte").split("/")[::-1])
		initial_filter_values["date_donated_lte"] = request.GET.get("date_donated_lte")
		donations = donations.filter(date_donated__lte=date__lte)
	if request.GET.get("amount_gte") not in ("",None):
		amount_gte = float(request.GET.get("amount_gte"))
		initial_filter_values["amount_gte"] = request.GET.get("amount_gte")
		donations = donations.filter(amount__gte=amount_gte)
	if request.GET.get("amount_lte") not in ("", None):
		amount_lte = float(request.GET.get("amount_lte"))
		initial_filter_values["amount_lte"] = request.GET.get("amount_lte")
		donations = donations.filter(amount__lte=amount_lte)
	if request.GET.get("payment_mode") not in ("", None):
		donations = donations.filter(payment_mode__payment_mode=request.GET.get("payment_mode"))
		initial_filter_values["payment_mode"] = request.GET.get("payment_mode")
	if request.GET.get("donation_type") not in ("", None):
		donations = donations.filter(donation_type__donation_type=request.GET.get("donation_type"))
		initial_filter_values["donation_type"] = request.GET.get("donation_type")
	if request.GET.get("organisation") not in ("", None):
		donations = donations.filter(organisation__organisation=request.GET.get("organisation"))
		initial_filter_values["organisation"] = request.GET.get("organisation")
	if request.GET.get("scroll_value") not in ("", None):
		if 'collapse_show' in request.GET.get("scroll_value"):
			scroll = int("".join(request.GET.get("scroll_value").split('collapse_show')) or 0)
			collapse = 'collapse show'
		elif 'collapse' in request.GET.get("scroll_value"):
			scroll = int("".join(request.GET.get("scroll_value").split('collapse')) or 0)

	# context after filter 	
	donation_count_filter = donations.filter(disabled=False).count()
	total_donated_filter = sum([d.amount for d in donations.filter(disabled=False)])

	# redirect when filter is empty
	if list(filter(lambda x: x, [request.GET.get(item) for item in request.GET])) in ([], ["Type to search..."]) and request.get_full_path_info() != "/":
		return redirect("/")

	# donations for table - sync tag colours 
	mod_don = [{
		"id": donation.id,
		"contact": {
			"id": donation.contact.id, 
			"name": donation.contact.name,
		},
		"tags": [(colours[str(tag.id%20)][0],colours[str(tag.id%20)][1], tag.tag) for tag in donation.contact.tags.all()],
		"date_donated": donation.date_donated,
		"amount": donation.amount,
		"payment_mode": donation.payment_mode,
		"donation_type": donation.donation_type,
		"organisation": donation.organisation,
		"disabled": donation.disabled,
		} for donation in donations]



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
		"mod_don": mod_don,
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
