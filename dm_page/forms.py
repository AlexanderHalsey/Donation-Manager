from django import forms
from .models import *
from django.core.exceptions import ValidationError

class DonationForm(forms.Form):

	contact = forms.TypedChoiceField(initial = "", choices = [])
	contact_name = forms.TypedChoiceField(initial = "", choices = [])
	date_donated = forms.DateField(initial = "")
	amount_euros = forms.IntegerField(initial = "")
	amount_cents = forms.DecimalField(initial = ".00", decimal_places = 2)
	payment_mode = forms.ChoiceField(initial = "", choices = [])
	payment_mode_name = forms.ChoiceField(initial = "", choices = [])
	donation_type = forms.ChoiceField(initial = "", choices = [])
	donation_type_name = forms.ChoiceField(initial = "", choices = [])
	organisation = forms.ChoiceField(initial = "", choices = [])
	organisation_name = forms.ChoiceField(initial = "", choices = [])
	nature_du_don = forms.ChoiceField(initial = "", choices = [])
	nature_du_don_name = forms.ChoiceField(initial = "", choices = [])
	forme_du_don = forms.ChoiceField(initial = "", choices = [])
	forme_du_don_name = forms.ChoiceField(initial = "", choices = [])

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
		donations = Donation.objects.all()
		self.fields['contact_name'].required = False
		self.fields['contact_name'].choices = list(set([(don.contact_name, don.contact_name) for don in donations]))
		self.fields['payment_mode_name'].required = False
		self.fields['payment_mode_name'].choices = list(set([(don.payment_mode_name, don.payment_mode_name) for don in donations]))
		self.fields['donation_type_name'].required = False
		self.fields['donation_type_name'].choices = list(set([(don.donation_type_name, don.donation_type_name) for don in donations]))
		self.fields['organisation_name'].required = False
		self.fields['organisation_name'].choices = list(set([(don.organisation_name, don.organisation_name) for don in donations]))
		self.fields['forme_du_don_name'].required = False
		self.fields['forme_du_don_name'].choices = list(set([(don.forme_du_don_name, don.forme_du_don_name) for don in donations]))
		self.fields['nature_du_don_name'].required = False
		self.fields['nature_du_don_name'].choices = list(set([(don.nature_du_don_name, don.nature_du_don_name) for don in donations]))

	def clean_donation_type(self):
		for d in DonationType.objects.all():
			print("does this come through at all?")
			if str(d) == self.data['donation_type']:
				print("first step")
				if str(d.organisation) != self.data['organisation']:
					print("this shouldn't be the case")
					print(str(d.organisation))
					print(self.data['organisation'])
					raise ValidationError('Not a compatible donation type.')
				return self.data['donation_type']
		
