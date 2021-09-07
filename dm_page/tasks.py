from celery import shared_task
from dm_page.models import *
from dm_page.utils import annual_pdf_receipt
from collections import defaultdict
import datetime

@scheduled_task
def check_against_automatic_trigger():
	triggers = AutomaticReceiptTrigger.objects.all()
	for trigger in triggers:
		if trigger.date.toordinal() <= datetime.date.today().toordinal():
			donations = Donation.objects.filter(pdf=False)
			contact_donations = defaultdict(list)
			for donation in donations:
				contact_donations[donation.contact].append(donation)
				donation.pdf = True
			for contact, donations in contact_donations.items():
				text = {}
				images = {}
				donation_receipt = DonationReceipt(
					contact = contact,
					date_created = datetime.date.today(),
					receipt_type = ('A', 'Annual'),
					file_name = annual_pdf_receipt(text, images, contact, donations),
				)
				donation_receipt.save()
	return