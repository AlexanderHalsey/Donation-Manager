import os
from celery import Celery
from celery.schedules import crontab


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donations.settings')

app = Celery('donations')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
	'annual_receipts_check': {
		'task': 'donations.receipt_trigger_notification',
		'schedule': crontab(minute="0", hour="0", day_of_week="*") # runs once a day at 00:00
	}
}
app.conf.timezone = 'UTC'

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
