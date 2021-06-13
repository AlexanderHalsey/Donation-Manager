from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Tag)
admin.site.register(Contact)
admin.site.register(Donation)
admin.site.register(PaymentMode)
admin.site.register(DonationType)
admin.site.register(Organisation)