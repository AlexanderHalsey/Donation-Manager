from django.contrib import admin
from .models import ReçusFiscaux, Paramètre

class ModelAdminDonationReceipt(admin.ModelAdmin):
	list_display = ('id','contact','file_name',)
	list_display_links = ('file_name',)
	fields = ('cancel',)
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

class ModelAdminReceiptSettings(admin.ModelAdmin):
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
			return ('release_date', ('automatic', 'manual'))
		if i == 3:
			return (
				('organisation_1', 'donation_type_1'),
				('organisation_2', 'donation_type_2'),
				('organisation_3', 'donation_type_3'),
				('organisation_4', 'donation_type_4'),
				('organisation_5', 'donation_type_5'),
			)

# Register your models here.
admin.site.register(ReçusFiscaux, ModelAdminDonationReceipt)
admin.site.register(Paramètre, ModelAdminReceiptSettings)
