from django import forms
from .models import *

class DonationForm(forms.Form):

	contact = forms.TypedChoiceField(
		initial = "",
		choices = "",
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
		choices = "",
	)
	donation_type = forms.ChoiceField(
		initial = "-----",
		choices = "",
	)
	organisation = forms.ChoiceField(
		initial = "-----",
		choices = "",
	)
