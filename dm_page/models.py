from django.db import models
from .colours import colours


# Create your models here.
class Tag(models.Model):
	tag = models.CharField(max_length=200)

	def bg_colour(self):
		return colours[str(self.id%20)][0]
	def text_colour(self):
		return colours[str(self.id%20)][1]
	def __str__(self):
		return self.tag

class Profile(models.Model):
	seminar_desk_id = models.PositiveIntegerField(default= None, null=True)
	salutation = models.CharField(max_length= 200, default=None, null=True)
	object_type = models.CharField(max_length= 200, default=None, null=True)
	title = models.CharField(max_length= 200, default=None, null=True)
	name = models.CharField(max_length= 200, default=None, null=True)
	language = models.CharField(max_length= 200, default=None, null=True)
	labels = models.TextField(default=None, null=True)
	email = models.CharField(max_length= 200, default=None, null=True)
	alternative_email = models.CharField(max_length= 200, default=None, null=True)
	website = models.CharField(max_length= 200, default=None, null=True)
	fax_number = models.CharField(max_length= 200, default=None, null=True)
	primary_address = models.TextField(default=None, null=True)
	billing_address_active = models.CharField(max_length= 200, default=None, null=True)
	billing_address = models.TextField(default=None, null=True)
	remarks = models.TextField(default=None, null=True)
	information = models.TextField(default=None, null=True)
	is_blocked = models.CharField(max_length= 200, default=None, null=True)
	blocked_reason = models.CharField(max_length= 200, default=None, null=True)
	bank_account_data = models.TextField(default=None, null=True)
	tax_number = models.CharField(max_length= 200, default=None, null=True)
	vat_id = models.CharField(max_length= 200, default=None, null=True)
	customer_number = models.CharField(max_length= 200, default=None, null=True)
	additional_fields = models.TextField(default=None, null=True)
	disabled = models.BooleanField(default=False)

class Contact(models.Model):
	tags = models.ManyToManyField('Tag')
	profile = models.ForeignKey('Profile', on_delete=models.CASCADE, null=True, blank=True)
	first_name = models.CharField(max_length= 200, default=None, null=True, blank=True)
	last_name = models.CharField(max_length= 200, default=None, null=True)
	additional_title = models.CharField(max_length= 200, default=None, null=True)
	date_of_birth = models.DateField(default=None, null=True)
	profession = models.CharField(max_length= 200, default=None, null=True)
	salutation_type = models.CharField(max_length= 200, default=None, null=True)
	private_phone_number = models.CharField(max_length= 200, default=None, null=True)
	alternative_phone_number = models.CharField(max_length= 200, default=None, null=True)
	work_phone_number = models.CharField(max_length= 200, default=None, null=True)
	preferred_address = models.CharField(max_length= 200, default=None, null=True)
	preferred_email = models.CharField(max_length= 200, default=None, null=True)
	preferred_phone_number = models.CharField(max_length= 200, default=None, null=True)
	is_subscribed_to_newsletter = models.CharField(max_length= 200, default=None, null=True)
	is_facilitator = models.CharField(max_length= 200, default=None, null=True)
	def __str__(self):
		return self.first_name + " " + self.last_name

class PaymentMode(models.Model):
	payment_mode = models.CharField(max_length=200, null=True, blank=True)
	def __str__(self):
		return self.payment_mode

class Organisation(models.Model):
	profile = models.ForeignKey('Profile', on_delete=models.CASCADE, null=True, blank=True)
	additional_name = models.CharField(max_length= 200, default=None, null=True)
	def __str__(self):
		return self.profile.name

class DonationType(models.Model):
	organisation = models.ForeignKey('Organisation', on_delete=models.CASCADE, null=True, blank=True)
	name = models.CharField(max_length=200, null=True, blank=True)
	def __str__(self):
		return self.name

class Donation(models.Model):
	contact = models.ForeignKey('Contact', on_delete=models.SET_NULL, null=True, blank=True)
	date_donated = models.DateField(null=True)
	amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	payment_mode = models.ForeignKey('PaymentMode', on_delete=models.SET_NULL, null=True, blank=True)
	donation_type = models.ForeignKey('DonationType', on_delete=models.SET_NULL, null=True, blank=True)
	organisation = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True)
	disabled = models.BooleanField(default=False)
	eligible = models.BooleanField(default=False)
	pdf = models.BooleanField(default=False)
	def __str__(self):
		return str(self.id) + "_" + self.contact.profile.name + "_" + str(self.date_donated)

class RecettesFiscale(models.Model):
	contact = models.ForeignKey('Contact', on_delete=models.SET_NULL, null=True, blank=True)
	date_created = models.DateField(auto_now_add=True, null=True)
	receipt_type = models.CharField(max_length=200, choices=(('A','Annual'),('I','Individual'),))
	file_name = models.CharField(max_length=200, null=True, blank=True)
	donation_list = models.TextField(null=True, blank=True)
	cancel = models.BooleanField(default=False)
	email_active = models.BooleanField(default=False)
	email_cancel = models.BooleanField(default=False)

class Image(models.Model):
	name = models.CharField(max_length=200, null=True)
	image = models.CharField(max_length=200,null=True, blank=True)

class PDF(models.Model):
	models.FileField()

class Paramètre(models.Model):
	date_range_start = models.DateField(null=True, blank=True, verbose_name="Date de début")
	date_range_end = models.DateField(null=True, blank=True, verbose_name="Date de fin")
	release_date = models.DateField(null=True, blank=True, verbose_name="Date de Libération")
	automatic = models.BooleanField(default=False, verbose_name="Automatique")
	manual = models.URLField(max_length=200, null=True, blank=True, verbose_name="Manuel")
	organisation_1 = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Organisation", related_name="organisation1")
	donation_type_1 = models.ForeignKey('DonationType', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type de don", related_name="donation_type1")
	organisation_2 = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Organisation", related_name="organisation2")
	donation_type_2 = models.ForeignKey('DonationType', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type de don", related_name="donation_type2")
	organisation_3 = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Organisation", related_name="organisation3")
	donation_type_3 = models.ForeignKey('DonationType', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type de don", related_name="donation_type3")
	organisation_4 = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Organisation", related_name="organisation4")
	donation_type_4 = models.ForeignKey('DonationType', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type de don", related_name="donation_type4")
	organisation_5 = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Organisation", related_name="organisation5")
	donation_type_5 = models.ForeignKey('DonationType', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type de don", related_name="donation_type5")
	def __str__(self):
		if self.id == 1:
			return "Plage de dates pour l'Année Fiscale"
		if self.id == 2:
			return "Date de Libération / de Contrôle"
		if self.id == 3:
			return "Conditions d'éligibilité des reçus"

class WebhookLogs(models.Model):
	received_at = models.DateTimeField(help_text="When we received the event.")
	payload = models.JSONField(default=None, null=True)

	class Meta:
		indexes = [
			models.Index(fields=["received_at"]),
		]
