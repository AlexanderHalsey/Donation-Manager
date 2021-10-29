from django import forms
from .models import *
from django.core.exceptions import ValidationError

class DonationForm(forms.Form):

	contact = forms.TypedChoiceField(initial = "", choices = [])
	date_donated = forms.DateField(initial = "")
	amount_euros = forms.IntegerField(initial = "")
	amount_cents = forms.DecimalField(initial = ".00", decimal_places = 2)
	payment_mode = forms.ChoiceField(initial = "", choices = [])
	donation_type = forms.ChoiceField(initial = "", choices = [])
	organisation = forms.ChoiceField(initial = "", choices = [])
	nature_du_don = forms.ChoiceField(initial = "", choices = [])
	forme_du_don = forms.ChoiceField(initial = "", choices = [])

	def __init__(self, *args, **kwargs):
		super(DonationForm, self).__init__(*args, **kwargs)
		self.fields['contact'].choices = [(str(contact), str(contact)) for contact in Profile.objects.filter(disabled=False)]
		self.fields['payment_mode'].choices = [(str(mode), str(mode)) for mode in PaymentMode.objects.all()]
		self.fields['donation_type'].choices = [(str(t), str(t)) for t in DonationType.objects.all()]
		self.fields['organisation'].choices = [(str(organisation), str(organisation)) for organisation in Organisation.objects.all()]
		self.fields['forme_du_don'].initial = FormeDuDon.objects.get(default_value=True).name
		self.fields['forme_du_don'].choices = [(str(forme), str(forme)) for forme in FormeDuDon.objects.all()]
		self.fields['nature_du_don'].initial = NatureDuDon.objects.get(default_value=True).name
		self.fields['nature_du_don'].choices = [(str(nature), str(nature)) for nature in NatureDuDon.objects.all()]

	def clean_donation_type(self):
		for d in DonationType.objects.all():
			if str(d).split(" - ")[0] == self.cleaned_data['donation_type'].split(" - ")[0]:
				if str(d.organisation) != self.data['organisation']:
					raise ValidationError('Not a compatible donation type.')
				return self.cleaned_data['donation_type']
		
