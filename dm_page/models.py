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

class DonationType(models.Model):
	donation_type = models.CharField(max_length=200, null=True, blank=True)
	def __str__(self):
		return self.donation_type

class Organisation(models.Model):
	profile = models.ForeignKey('Profile', on_delete=models.CASCADE, null=True, blank=True)
	additional_name = models.CharField(max_length= 200, default=None, null=True)

	def __str__(self):
		return self.profile.name

class Donation(models.Model):
	contact = models.ForeignKey('Contact', on_delete=models.SET_NULL, null=True, blank=True)
	date_donated = models.DateField(null=True)
	amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	payment_mode = models.ForeignKey('PaymentMode', on_delete=models.SET_NULL, null=True, blank=True)
	donation_type = models.ForeignKey('DonationType', on_delete=models.SET_NULL, null=True, blank=True)
	organisation = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True)
	disabled = models.BooleanField(default=False)
	pdf = models.BooleanField(default=False)

	def __str__(self):
		return str(self.id) + "_" + self.contact.profile.name + "_" + str(self.date_donated)

class DonationReceipt(models.Model):
	contact = models.ForeignKey('Contact', on_delete=models.SET_NULL, null=True, blank=True)
	date_created = models.DateField(auto_now_add=True, null=True)
	receipt_type = models.CharField(max_length=200, choices=(('A','Annual'),('I','Individual'),))
	file_name = models.CharField(max_length=200, null=True, blank=True)
	canceled = models.BooleanField(default=False)

class AutomaticReceiptTrigger(models.Model):
	date = models.DateField()

class WebhookLogs(models.Model):
	received_at = models.DateTimeField(help_text="When we received the event.")
	payload = models.JSONField(default=None, null=True)

	class Meta:
		indexes = [
			models.Index(fields=["received_at"]),
		]
