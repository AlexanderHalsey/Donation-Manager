from django import forms
from .models import *

class DonationForm(forms.Form):

	contact = forms.TypedChoiceField(
		initial = "",
		choices = [(c.name, c.name) for c in Contact.objects.all()],
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
		choices = [("","-----")]+[(m.payment_mode, m.payment_mode) for m in PaymentMode.objects.all()],
	)
	donation_type = forms.ChoiceField(
		initial = "-----",
		choices = [("","-----")]+[(d.donation_type, d.donation_type) for d in DonationType.objects.all()],
	)
	organisation = forms.ChoiceField(
		initial = "-----",
		choices = [("","-----")]+[(o.organisation, o.organisation) for o in Organisation.objects.all()],
	)
