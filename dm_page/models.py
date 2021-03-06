from django.db import models
from django.core.exceptions import ValidationError
from .colours import colours
import datetime

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
	seminar_desk_id = models.PositiveIntegerField(default= "", null=True, blank=True)
	salutation = models.CharField(max_length= 200, default="", null=True, blank=True)
	object_type = models.CharField(max_length= 200, default="", null=True, blank=True)
	title = models.CharField(max_length= 200, default="", null=True, blank=True)
	name = models.CharField(max_length= 200, default="", null=True, blank=True)
	language = models.CharField(max_length= 200, default="", null=True, blank=True)
	labels = models.TextField(default="", null=True)
	email = models.CharField(max_length= 200, default="", null=True, blank=True)
	alternative_email = models.CharField(max_length= 200, default="", null=True, blank=True)
	website = models.CharField(max_length= 200, default="", null=True, blank=True)
	fax_number = models.CharField(max_length= 200, default="", null=True, blank=True)
	primary_address = models.JSONField(default=None, null=True)
	billing_address_active = models.CharField(max_length= 200, default="", null=True, blank=True)
	billing_address = models.TextField(default="", null=True, blank=True)
	remarks = models.TextField(default="", null=True, blank=True)
	information = models.TextField(default="", null=True, blank=True)
	is_blocked = models.CharField(max_length= 200, default="", null=True, blank=True)
	blocked_reason = models.CharField(max_length= 200, default="", null=True, blank=True)
	bank_account_data = models.TextField(default="", null=True, blank=True)
	tax_number = models.CharField(max_length= 200, default="", null=True, blank=True)
	vat_id = models.CharField(max_length= 200, default="", null=True, blank=True)
	customer_number = models.CharField(max_length= 200, default="", null=True, blank=True)
	additional_fields = models.TextField(default="", null=True, blank=True)
	disabled = models.BooleanField(default=False)
	def __str__(self):
		return self.name

class Contact(models.Model):
	tags = models.ManyToManyField('Tag')
	profile = models.ForeignKey('Profile', on_delete=models.CASCADE, null=True, blank=True)
	first_name = models.CharField(max_length= 200, default="", null=True, blank=True)
	last_name = models.CharField(max_length= 200, default="", null=True, blank=True)
	additional_title = models.CharField(max_length= 200, default="", null=True, blank=True)
	date_of_birth = models.DateField(default=None, null=True, blank=True)
	profession = models.CharField(max_length= 200, default="", null=True, blank=True)
	salutation_type = models.CharField(max_length= 200, default="", null=True, blank=True)
	private_phone_number = models.CharField(max_length= 200, default="", null=True, blank=True)
	alternative_phone_number = models.CharField(max_length= 200, default="", null=True, blank=True)
	work_phone_number = models.CharField(max_length= 200, default="", null=True, blank=True)
	preferred_address = models.CharField(max_length= 200, default="", null=True, blank=True)
	preferred_email = models.CharField(max_length= 200, default="", null=True, blank=True)
	preferred_phone_number = models.CharField(max_length= 200, default="", null=True, blank=True)
	is_subscribed_to_newsletter = models.CharField(max_length= 200, default="", null=True, blank=True)
	is_facilitator = models.CharField(max_length= 200, default="", null=True, blank=True)
	def __str__(self):
		return self.first_name + " " + self.last_name
	class Meta:
		order_with_respect_to = 'profile'

class PaymentMode(models.Model):
	payment_mode = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nom")
	def __str__(self):
		return self.payment_mode
	class Meta:
		verbose_name = "Mode de paiement"
		verbose_name_plural = "Mode de paiement"

def path_to_institut_image(instance, filename):
	return f'organisation/{instance.name}/institutImage/{filename}'

def path_to_president_signature(instance, filename):
	return f'organisation/{instance.name}/presidentSignature/{filename}'

def validate_image(value):
	if str(value)[-4:] != ".png":
		raise ValidationError(
			"Cette image n'est pas en format .png"
		)

class Organisation(models.Model):
	name = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nom interne")
	institut_title = models.CharField(max_length=300, null=True, blank=True, verbose_name="Nom sur le re??u")
	institut_street_name = models.CharField(max_length=200, null=True, blank=True, verbose_name="Adresse")
	institut_town = models.CharField(max_length=200, null=True, blank=True, verbose_name="Ville")
	institut_post_code = models.CharField(max_length=200, null=True, blank=True, verbose_name="Code postal")
	institut_image = models.FileField(upload_to=path_to_institut_image, null=True, blank=True, verbose_name="Logo", help_text="Cette image doit ??tre dans le format .png", validators=[validate_image])
	object_title = models.CharField(max_length=300, null=True, blank=True, verbose_name="Objet")
	object_description = models.TextField(null=True, blank=True, verbose_name="Description de l'objet")
	president = models.CharField(max_length=200, null=True, blank=True, verbose_name="Signataire")
	president_position = models.CharField(max_length=200, null=True, blank=True, verbose_name="Fonction du signataire")
	president_signature = models.FileField(upload_to=path_to_president_signature, null=True, blank=True, verbose_name="Signature", help_text="Cette image doit ??tre dans le format .png", validators=[validate_image])

	def __str__(self):
		return self.name

	class Meta:
		verbose_name = "Organisation"
		verbose_name_plural = "Organisations"

class FormeDuDon(models.Model):
	name = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nom")
	default_value = models.BooleanField(default=False, verbose_name = "Valeur par d??faut")
	def __str__(self):
		return self.name
	def save(self, *args, **kwargs):
		if self.default_value == True:
			for past_instance in FormeDuDon.objects.all():
				past_instance.default_value = False
				super(FormeDuDon, past_instance).save(*args, **kwargs)
		super(FormeDuDon, self).save(*args, **kwargs)
	class Meta:
		verbose_name = "Forme du don"
		verbose_name_plural = "Forme des dons"

class NatureDuDon(models.Model):
	name = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nom")
	default_value = models.BooleanField(default=False, verbose_name = "Valeur par d??faut")
	def __str__(self):
		return self.name
	def save(self, *args, **kwargs):
		if self.default_value == True:
			for past_instance in NatureDuDon.objects.all():
				past_instance.default_value = False
				super(NatureDuDon, past_instance).save(*args, **kwargs)
		super(NatureDuDon, self).save(*args, **kwargs)
	class Meta:
		verbose_name = "Nature du don"
		verbose_name_plural = "Nature des dons"


class DonationType(models.Model):
	organisation = models.ForeignKey('Organisation', on_delete=models.CASCADE, null=True, blank=True)
	name = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nom")
	def __str__(self):
		return self.name + f" - ({self.organisation})" 
	class Meta:
		verbose_name = "Type de don"
		verbose_name_plural = "Types de dons"

class Locked(models.Model):
	name = models.CharField(max_length=200, null=200, blank=True, verbose_name="Nom")
	date_start = models.DateField(null=True, blank=True, verbose_name="Date de d??but")
	date_end = models.DateField(null=True, blank=True, verbose_name="Date de fin")
	# contacts = models.ManyToManyField(Contact, verbose_name="Contacts", help_text="Attention! Laisser ce champ vide si vous voulez tout s??l??ctioner.")
	# donation_types = models.ManyToManyField(DonationType, verbose_name="Types des Dons", help_text="Attention! Laisser ce champ vide si vous voulez tout s??l??ctioner.")
	# organisations = models.ManyToManyField(Organisation, verbose_name="Organisations", help_text="Attention! Laisser ce champ vide si vous voulez tout s??l??ctioner.")
	# donation_list = models.CharField(max_length=200, null=True, blank=True)
	def save(self, *args, **kwargs):	
		super(Locked, self).save(*args, **kwargs)
		date_ranges = [(lock.date_start, lock.date_end) for lock in Locked.objects.all()]
		donations = Donation.objects.all()
		for don in donations:
			if don.locked:
				for s, e in date_ranges:
					if (s or datetime.date.fromordinal(1)) <= don.date_donated <= (e or datetime.date.fromordinal(10**6)):
						break
				else:
					don.locked = False
					don.save()
			else:
				for s, e in date_ranges:
					if (s or datetime.date.fromordinal(1)) <= don.date_donated <= (e or datetime.date.fromordinal(10**6)):
						don.locked = True
						don.save()
						break
	def delete(self, *args, **kwargs):
		super(Locked, self).delete(*args, **kwargs)
		date_ranges = [(lock.date_start, lock.date_end) for lock in Locked.objects.all()]
		donations = Donation.objects.all()
		for don in donations:
			if don.locked:
				for s, e in date_ranges:
					if (s or datetime.date.fromordinal(1)) <= don.date_donated <= (e or datetime.date.fromordinal(10**6)):
						break
				else:
					don.locked = False
					don.save()
			else:
				for s, e in date_ranges:
					if (s or datetime.date.fromordinal(1)) <= don.date_donated <= (e or datetime.date.fromordinal(10**6)):
						don.locked = True
						don.save()
						break
	class Meta:
		verbose_name = "Verrouillage"
		verbose_name_plural = "Verrouillage"

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

class Re??usFiscaux(models.Model):
	contact = models.ForeignKey('Contact', on_delete=models.SET_NULL, null=True, blank=True)
	contact_name = models.CharField(max_length=200, null=True, blank=True)
	date_created = models.DateField(auto_now_add=True, null=True)
	receipt_type = models.CharField(max_length=200, choices=(('A','Annual'),('I','Individual'),))
	file_name = models.CharField(max_length=200, null=True, blank=True)
	donation_list = models.TextField(null=True, blank=True)
	cancel = models.BooleanField(default=False, verbose_name="Annuler")
	cancel_description = models.TextField(null=True, blank=True, verbose_name="Description de l'annulation")
	email_active = models.BooleanField(default=False)
	email_sent_time = models.DateTimeField(null=True, blank=True)
	email_cancel = models.BooleanField(default=False)

	class Meta:
		verbose_name = "Re??us fiscaux"
		verbose_name_plural = "Re??us fiscaux"


def check_new_eligibility():
	eligibility_list = [(e.organisation, e.donation_type) for e in Eligibility.objects.all()]
	for donation in Donation.objects.filter(disabled=False ):
		if (donation.organisation, donation.donation_type) in eligibility_list:
			if not donation.eligible:
				donation.eligible = True
				donation.save()
		else:
			if donation.eligible:
				donation.eligible = False
				donation.save()

class Eligibility(models.Model):
	organisation = models.ForeignKey('Organisation', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Organisation", related_name="organisation")
	donation_type = models.ForeignKey('DonationType', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Type de don", related_name="donation_type")

	def save(self, *args, **kwargs):
		super(Eligibility, self).save(*args, **kwargs)
		check_new_eligibility()
	def delete(self, *args, **kwargs):
		super(Eligibility, self).delete(*args, **kwargs)
		check_new_eligibility()

	class Meta:
		verbose_name = "Eligibilit??"
		verbose_name_plural = "Eligibilit??"

class Param??tre(models.Model):
	date_range_start = models.DateField(null=True, blank=True, verbose_name="Date de d??but")
	date_range_end = models.DateField(null=True, blank=True, verbose_name="Date de fin")
	release_date = models.DateField(null=True, blank=True, verbose_name="Date de notification")
	release_notification = models.BooleanField(default=False)
	annual_process_button = models.BooleanField(default=False)
	manual = models.URLField(max_length=200, null=True, blank=True, verbose_name="Lien")
	host_email = models.CharField(max_length=200, null=True, blank=True, verbose_name="Adresse de l'exp??diteur")
	host_email_name = models.CharField(max_length=200, null=True, blank=True, verbose_name="Nom de l'exp??diteur")
	host_password = models.CharField(max_length=200, null=True, blank=True, verbose_name="Mot de passe")
	cc = models.CharField(max_length=200, null=True, blank=True)
	bcc = models.CharField(max_length=200, null=True, blank=True)
	email_subject = models.CharField(max_length=200, null=True, blank=True, verbose_name="Sujet", help_text="??crivez 'R_ID' dans le message pour rajouter l'identifiant actuel du re??u<br>??crivez 'AAAA' dans le message pour rajouter l'ann??e actuelle")
	body = models.TextField(max_length=10000, null=True, blank=True, verbose_name="Message", help_text="??crivez 'R_ID' dans le message pour remplacer l'identifiant actuel du re??u<br>??crivez 'AAAA' dans le message pour rajouter l'ann??e actuelle")
	smtp_domain = models.CharField(max_length=200, null=True, blank=True, verbose_name="SMTP Domaine")
	smtp_port = models.CharField(max_length=200, null=True, blank=True, verbose_name="SMTP Port")
	email_notification = models.BooleanField(default=False)
	email_notification_list = models.TextField(null=True, blank=True)
	def __str__(self):
		if self.id == 1:
			return "Plage de dates pour l'ann??e fiscale"
		if self.id == 2:
			return "Date d'ouverture des re??us annuels"
		if self.id == 3:
			return "Configuration des emails"

	class Meta:
		verbose_name = "Param??tres g??n??raux"
		verbose_name_plural = "Param??tres g??n??raux"

class WebhookLogs(models.Model):
	received_at = models.DateTimeField(help_text="When we received the event.")
	payload = models.JSONField(default=None, null=True)
	processed = models.BooleanField(default=False)
	class Meta:
		indexes = [
			models.Index(fields=["received_at"]),
		]

