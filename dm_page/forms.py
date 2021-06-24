from django import forms
from .models import *

CONTACTS = [(c.name, c.name) for c in Contact.objects.all()]
MODES = [("","-----")]+[(m.payment_mode, m.payment_mode) for m in PaymentMode.objects.all()]
TYPES = [("","-----")]+[(d.donation_type, d.donation_type) for d in DonationType.objects.all()]
ORGANISATIONS = [("","-----")]+[(o.organisation, o.organisation) for o in Organisation.objects.all()]

class DonationForm(forms.Form):
	contact = forms.TypedChoiceField(
		initial = "",
		choices = CONTACTS,
		coerce = str,
	)
	date_donated = forms.DateField(
		initial = "",
		)
	amount_euros = forms.IntegerField(
		initial = "",
	)
	amount_cents = forms.DecimalField(
		initial = ".00",
		decimal_places = 2,
	)
	payment_mode = forms.ChoiceField(
		initial = "-----",
		choices = MODES,
	)
	donation_type = forms.ChoiceField(
		initial = "-----",
		choices = TYPES,
	)
	organisation = forms.ChoiceField(
		initial = "-----",
		choices = ORGANISATIONS,
	)
