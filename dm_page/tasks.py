from celery import shared_task
from dm_page.models import *
from dm_page.utils import annual_pdf_receipt
from collections import defaultdict
import datetime

@scheduled_task
def check_against_automatic_trigger():
	trigger = Paramètre.objects.exclude(automatic=None)[0]
	if trigger.release_date.toordinal() <= datetime.date.today().toordinal():
		pass
	return