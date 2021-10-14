from django.contrib import admin
from django.contrib.auth.models import User
from django import forms
from .models import *
from copy import deepcopy
from django.utils.translation import ugettext_lazy

class MyAdminSite(admin.AdminSite):
	site_header = ugettext_lazy('DMS Admin')
	def get_app_list(self, request):
		"""
		Return a sorted list of all the installed apps that have been
		registered in this site.
		"""
		app_dict = self._build_app_dict(request)
		# a.sort(key=lambda x: b.index(x[0]))
		# Sort the apps alphabetically.
		app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())
		modified_app_list = deepcopy(app_list)
		modified_app_list.insert(1, {
			"name": "Reçus et Paramètres",
			"app_label": "reçusetparamètres",
			"app_url": "/fr/admin/dm_page/",
			"has_module_perms": True,
			"models": modified_app_list[1]["models"][:3]
		})
		modified_app_list[2]["name"] = "Modèles"
		modified_app_list[2]["app_label"] = "modèles"
		modified_app_list[2]["models"] = modified_app_list[2]["models"][3:]
		# Sort the models alphabetically within each app.
		for app in modified_app_list:
		    app['models'].sort(key=lambda x: x['name'])

		return modified_app_list

class ModelAdminDonationReceipt(admin.ModelAdmin):
	list_display = ('id','contact','file_name',)
	list_display_links = ('file_name',)
	fields = ('cancel','cancel_description')
	verbose_name = "Reçus Fiscaux"
	verbose_name_plural = "Reçus Fiscaux"
	def get_readonly_fields(self, request, obj):
		if obj.cancel:
			return ('cancel',)
		else:
			return ()
	def get_actions(self, request):
		actions = super().get_actions(request)
		if 'delete_selected' in actions:
			del actions['delete_selected']
		return actions
	def has_delete_permission(self, request, obj=None):
		return False
	def has_add_permission(self, request, obj=None):
		return False

class SettingsForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		try:
			self.fields['manual'].disabled = True
		except:
			pass
		try:
			self.fields['host_password'].widget = forms.PasswordInput(attrs={'placeholder':'********','autocomplete': 'off','data-toggle': 'password'}, value=Paramètre.objects.get(id=5).host_password)
		except:
			pass
	class Meta:
		model = Paramètre
		fields = '__all__'

class ModelAdminSettings(admin.ModelAdmin):
	ordering = ("id",)
	form = SettingsForm
	def has_add_permission(self, request):
		if self.model.objects.count() >= 1:
			return False
		return super().has_add_permission(request)
	def get_actions(self, request):
		actions = super().get_actions(request)
		if 'delete_selected' in actions:
			del actions['delete_selected']
		return actions
	def has_delete_permission(self, request, obj=None):
		return False
	def get_fields(self, request, obj=None):
		i = int(request.path.split("/change/")[0][-1])
		if i == 1:
			return ('date_range_start','date_range_end')
		if i == 2:
			return ('release_date', 'automatic', 'manual')
		if i == 3:
			return (
				('organisation_1', 'donation_type_1'),
				('organisation_2', 'donation_type_2'),
				('organisation_3', 'donation_type_3'),
				('organisation_4', 'donation_type_4'),
				('organisation_5', 'donation_type_5'),
				('organisation_6', 'donation_type_6'),
				('organisation_7', 'donation_type_7'),
				('organisation_8', 'donation_type_8'),
				('organisation_9', 'donation_type_9'),
				('organisation_10', 'donation_type_10'),
			)
		if i == 4:
			return (
				'institut_title', 
				'institut_street_name',
				'institut_town',
				'institut_post_code',
				'institut_image',
				'object_title',
				'object_description',
				'president',
				'president_signature',
			)
		if i == 5:
			return (
				'host_email',
				'host_password',
				'body',
				'cc',
				'smtp_domain',
				'smtp_port',
			)

'''class OrganisationForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['profile'].required = True
		self.fields['profile'].queryset = Organisation.objects.filter(profile__object_type="ORGANIZATION")
	class Meta:
		model = Organisation
		fields = '__all__'

class ModelAdminOrganisation(admin.ModelAdmin):
	fields = ('profile',)
	form = OrganisationForm'''

class DonationTypeForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['organisation'].required = True
		self.fields['name'].required = True
	class Meta:
		model = DonationType
		fields = '__all__'

class ModelAdminDonationType(admin.ModelAdmin):
	form = DonationTypeForm

class NatureDuDonForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['name'].required = True
	class Meta:
		model = Organisation
		fields = '__all__'

class ModelAdminNatureDuDon(admin.ModelAdmin):
	fields = (('name', 'default_value'),)
	form = NatureDuDonForm

class FormeDuDonForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['name'].required = True
	class Meta:
		model = FormeDuDon
		fields = '__all__'

class ModelAdminFormeDuDon(admin.ModelAdmin):
	fields = (('name', 'default_value'),)
	form = FormeDuDonForm

class LockedForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['date_start'].required = False
		self.fields['date_end'].required = False
		self.fields['name'].required = False
		self.fields['contacts'].required = False
		self.fields['organisations'].required = False
		self.fields['donation_types'].required = False
	class Meta:
		model = Locked
		fields = '__all__'

class ModelAdminLocked(admin.ModelAdmin):
	fields = ('name',('date_start', 'date_end'),'contacts','organisations','donation_types')
	list_display = ('id','name','date_start','date_end',)
	list_display_links = ('name',)
	form = LockedForm

# Register your models here.
mysite = MyAdminSite()
admin.site = mysite
mysite.site_site_header = "DMS Admin"
mysite.register(User)
mysite.register(ReçusFiscaux, ModelAdminDonationReceipt)
mysite.register(Paramètre, ModelAdminSettings)
mysite.register(Locked, ModelAdminLocked)
'''admin.site.register(Organisation, ModelAdminOrganisation)'''
mysite.register(DonationType, ModelAdminDonationType)
mysite.register(NatureDuDon, ModelAdminNatureDuDon)
mysite.register(FormeDuDon, ModelAdminFormeDuDon)

