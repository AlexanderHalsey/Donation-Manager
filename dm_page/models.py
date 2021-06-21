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

class Contact(models.Model):
	name = models.CharField(max_length=200)
	tags = models.ManyToManyField('Tag')
	email = models.EmailField(max_length=200, null=True)
	phone = models.CharField(max_length=200, null=True)
	postal_address = models.TextField(null=True)
	details = models.TextField(null=True)
	def __str__(self):
		return self.name

class PaymentMode(models.Model):
	payment_mode = models.CharField(max_length=200, null=True, blank=True)
	def __str__(self):
		return self.payment_mode

class DonationType(models.Model):
	donation_type = models.CharField(max_length=200, null=True, blank=True)
	def __str__(self):
		return self.donation_type

class Organisation(models.Model):
	organisation = models.CharField(max_length=200, null=True, blank=True)
	def __str__(self):
		return self.organisation

class Donation(models.Model):
	contact = models.ForeignKey('Contact', on_delete=models.SET_NULL, null=True, blank=True)
	date_donated = models.DateField(null=True, blank=True)
	amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	payment_mode = models.ForeignKey('PaymentMode', on_delete=models.SET_NULL, null=True, blank=True)
	donation_type = models.ForeignKey('DonationType', on_delete=models.SET_NULL, null=True, blank=True)
	organisation = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True)
	disabled = models.BooleanField(default=False)
