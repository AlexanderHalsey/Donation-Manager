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
	def __str__(self):
		return self.name

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
	name = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nom")
	institut_title = models.CharField(max_length=300, null=True, blank=True, verbose_name="Institution")
	institut_street_name = models.CharField(max_length=200, null=True, blank=True, verbose_name="Rue")
	institut_town = models.CharField(max_length=200, null=True, blank=True, verbose_name="Commune")
	institut_post_code = models.CharField(max_length=200, null=True, blank=True, verbose_name="Code Postal")
	institut_image = models.FileField(null=True, blank=True, verbose_name="Image de l'Institut")
	object_title = models.CharField(max_length=300, null=True, blank=True, verbose_name="Titre de l'Objet")
	object_description = models.TextField(null=True, blank=True, verbose_name="Description de l'Objet")
	president = models.CharField(max_length=200, null=True, blank=True, verbose_name="Président")
	president_signature = models.FileField(null=True, blank=True, verbose_name="Signature du Président")
	used_for_receipt = models.BooleanField(default=False, verbose_name="Détails utilisés pour le reçu")
	def __str__(self):
		return self.name
	def save(self, *args, **kwargs):
		if self.used_for_receipt == True:
			for past_instance in Organisation.objects.all():
				past_instance.used_for_receipt = False
				super(Organisation, past_instance).save(*args, **kwargs)
		super(Organisation, self).save(*args, **kwargs)
	class Meta:
		verbose_name = "Organisation"
		verbose_name_plural = "Organisations"

class FormeDuDon(models.Model):
	name = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nom")
	default_value = models.BooleanField(default=False, verbose_name = "Valeur par Défaut")
	def __str__(self):
		return self.name
	def save(self, *args, **kwargs):
		if self.default_value == True:
			for past_instance in FormeDuDon.objects.all():
				past_instance.default_value = False
				super(FormeDuDon, past_instance).save(*args, **kwargs)
		super(FormeDuDon, self).save(*args, **kwargs)
	class Meta:
		verbose_name = "Forme du Don"
		verbose_name_plural = "Forme des Dons"

class NatureDuDon(models.Model):
	name = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nom")
	default_value = models.BooleanField(default=False, verbose_name = "Valeur par Défaut")
	def __str__(self):
		return self.name
	def save(self, *args, **kwargs):
		if self.default_value == True:
			for past_instance in NatureDuDon.objects.all():
				past_instance.default_value = False
				super(NatureDuDon, past_instance).save(*args, **kwargs)
		super(NatureDuDon, self).save(*args, **kwargs)
	class Meta:
		verbose_name = "Nature du Don"
		verbose_name_plural = "Nature des Dons"


class DonationType(models.Model):
	organisation = models.ForeignKey('Organisation', on_delete=models.CASCADE, null=True, blank=True)
	name = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nom")
	def __str__(self):
		return self.name
	class Meta:
		verbose_name = "Type de Don"
		verbose_name_plural = "Types de Dons"

class Locked(models.Model):
	name = models.CharField(max_length=200, null=200, blank=True, verbose_name="Nom")
	date_start = models.DateField(null=True, blank=True, verbose_name="Date de début")
	date_end = models.DateField(null=True, blank=True, verbose_name="Date de fin")
	contacts = models.ManyToManyField(Contact, verbose_name="Contacts")
	donation_types = models.ManyToManyField(DonationType, verbose_name="Types des Dons")
	organisations = models.ManyToManyField(Organisation, verbose_name="Organisations")
	donation_list = models.CharField(max_length=200, null=True, blank=True)
	
	class Meta:
		verbose_name = "Verouillage"
		verbose_name_plural = "Verouillage"

class Donation(models.Model):
	contact = models.ForeignKey('Contact', on_delete=models.SET_NULL, null=True, blank=True)
	contact_name = models.CharField(max_length=200, null=True, blank=True)
	date_donated = models.DateField(null=True, blank=True)
	amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
	payment_mode = models.ForeignKey('PaymentMode', on_delete=models.SET_NULL, null=True, blank=True)
	payment_mode_name = models.CharField(max_length=200, null=True, blank=True)
	donation_type = models.ForeignKey('DonationType', on_delete=models.SET_NULL, null=True, blank=True)
	donation_type_name = models.CharField(max_length=200, null=True, blank=True)
	organisation = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True)
	organisation_name = models.CharField(max_length=200, null=True, blank=True)
	nature_du_don = models.ForeignKey('NatureDuDon', on_delete=models.SET_NULL, null=True, blank=True)
	nature_du_don_name = models.CharField(max_length=200, null=True, blank=True)
	forme_du_don = models.ForeignKey('FormeDuDon', on_delete=models.SET_NULL, null=True, blank=True)
	forme_du_don_name = models.CharField(max_length=200, null=True, blank=True)
	disabled = models.BooleanField(default=False)
	eligible = models.BooleanField(default=False)
	pdf = models.BooleanField(default=False)
	locked = models.BooleanField(default=False)
	def __str__(self):
		return str(self.id) + "_" + self.contact.profile.name + "_" + str(self.date_donated)

class ReçusFiscaux(models.Model):
	contact = models.ForeignKey('Contact', on_delete=models.SET_NULL, null=True, blank=True)
	contact_name = models.CharField(max_length=200, null=True, blank=True)
	date_created = models.DateField(auto_now_add=True, null=True)
	receipt_type = models.CharField(max_length=200, choices=(('A','Annual'),('I','Individual'),))
	file_name = models.CharField(max_length=200, null=True, blank=True)
	donation_list = models.TextField(null=True, blank=True)
	cancel = models.BooleanField(default=False, verbose_name="Annuler")
	cancel_description = models.TextField(null=True, blank=True, verbose_name="Description de l'annulation")
	email_active = models.BooleanField(default=False)
	email_cancel = models.BooleanField(default=False)
	class Meta:
		verbose_name = "Reçus Fiscaux"
		verbose_name_plural = "Reçus Fiscaux"

class Paramètre(models.Model):
	date_range_start = models.DateField(null=True, blank=True, verbose_name="Date de début")
	date_range_end = models.DateField(null=True, blank=True, verbose_name="Date de fin")
	release_date = models.DateField(null=True, blank=True, verbose_name="Date de Libération")
	release_notification = models.BooleanField(default=False)
	automatic = models.BooleanField(default=False, verbose_name="Automatique")
	manual = models.URLField(max_length=200, null=True, blank=True, verbose_name="Lien")
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
	organisation_6 = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Organisation", related_name="organisation6")
	donation_type_6 = models.ForeignKey('DonationType', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type de don", related_name="donation_type6")
	organisation_7 = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Organisation", related_name="organisation7")
	donation_type_7 = models.ForeignKey('DonationType', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type de don", related_name="donation_type7")
	organisation_8 = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Organisation", related_name="organisation8")
	donation_type_8 = models.ForeignKey('DonationType', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type de don", related_name="donation_type8")
	organisation_9 = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Organisation", related_name="organisation9")
	donation_type_9 = models.ForeignKey('DonationType', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type de don", related_name="donation_type9")
	organisation_10 = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Organisation", related_name="organisation10")
	donation_type_10 = models.ForeignKey('DonationType', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Type de don", related_name="donation_type10")
	host_email = models.CharField(max_length=200, null=True, blank=True, verbose_name="Hôte Email")
	host_password = models.CharField(max_length=200, null=True, blank=True, verbose_name="Mot de passe")
	cc = models.CharField(max_length=200, null=True, blank=True)
	body = models.TextField(max_length=200, null=True, blank=True)
	smtp_domain = models.CharField(max_length=200, null=True, blank=True, verbose_name="SMTP Domain")
	smtp_port = models.CharField(max_length=200, null=True, blank=True, verbose_name="SMTP Port")
	email_notification = models.BooleanField(default=False)
	email_notification_list = models.TextField(null=True, blank=True)
	def __str__(self):
		if self.id == 1:
			return "Plage de dates pour l'Année Fiscale"
		if self.id == 2:
			return "Date de Libération / de Contrôle"
		if self.id == 3:
			return "Conditions d'éligibilité des reçus"
		if self.id == 4:
			return "Configuration des Reçus"
		if self.id == 5:
			return "Configuration de l'Email"

class WebhookLogs(models.Model):
	received_at = models.DateTimeField(help_text="When we received the event.")
	payload = models.JSONField(default=None, null=True)
	processed = models.BooleanField(default=False)
	class Meta:
		indexes = [
			models.Index(fields=["received_at"]),
		]
