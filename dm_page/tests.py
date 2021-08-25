import datetime as dt
from http import HTTPStatus

from django.test import Client, override_settings, TestCase
from django.utils import timezone

from .models import WebhookLogs

# Create your tests here.
@override_settings(DMS_WEBHOOK_TOKEN = 'abc123')
class WebhookTests(TestCase):
	def setUp(self):
		self.client = Client(enforce_csrf_checks=True)

	def test_bad_method(self):
		response = self.client.get("/webhooks/7f6qy3IqT5L2x75mFoUkaEdrY9Kuutuu2dzbuxOwcfw/")
		assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

	def test_missing_token(self):
		response = self.client.post("/webhooks/7f6qy3IqT5L2x75mFoUkaEdrY9Kuutuu2dzbuxOwcfw/")
		assert response.status_code == HTTPStatus.FORBIDDEN
		assert (
			response.content.decode() == "Incorrect token in Dms-Webhook-Token header."
			)

	def test_bad_token(self):
		response = self.client.post(
			"/webhooks/7f6qy3IqT5L2x75mFoUkaEdrY9Kuutuu2dzbuxOwcfw/", 
			HTTP_DMS_WEBHOOK_TOKEN = "def456"
		)
		assert response.status_code == HTTPStatus.FORBIDDEN
		assert (
			response.content.decode() == "Incorrect token in Dms-Webhook-Token header."
			)

	def test_success(self):
		start = timezone.now()
		old_message = WebhookLogs.objects.create(
			received_at = start - dt.timedelta(days=100),
			)
		response = self.client.post(
			"/webhooks/7f6qy3IqT5L2x75mFoUkaEdrY9Kuutuu2dzbuxOwcfw/", 
			HTTP_DMS_WEBHOOK_TOKEN = "abc123",
			content_type = "application/json",
			data = {"this": "is a message"},
		)
		print(response.content.decode())
		assert response.status_code == HTTPStatus.OK
		assert (
			response.content.decode() == "Message received okay."
			)
		assert not WebhookLogs.objects.filter(id=old_message.id).exists()
		wls = WebhookLogs.objects.get()
		assert wls.received_at >= start
		assert wls.payload == {'this': 'is a message'}
