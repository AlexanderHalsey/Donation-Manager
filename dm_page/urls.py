from django.urls import path, re_path
from dm_page import views
	
urlpatterns = [
	re_path(r'^(?P<lang>en|fr)/login/$', views.loginUser, name='login'),
	re_path(r'^(?P<lang>en|fr)/logout/$', views.logoutUser, name='logout'),
	path('', views.redir, name='redir'),
	path('webhooks/7f6qy3IqT5L2x75mFoUkaEdrY9Kuutuu2dzbuxOwcfw/', views.dms_webhook),
	re_path(r'^(?P<lang>en|fr)/webhooklogs/$', views.webhooklogs),
	re_path(r'^(?P<lang>en|fr)/$', views.dashboard, name='dashboard'),
	re_path(r'^(?P<lang>en|fr)/donators/$', views.donators, name="donators"),
	re_path(r'^(?P<lang>en|fr)/pdf_receipts/$', views.pdf_receipts, name="pdf-receipts"),
	re_path(r'^receipts/(?P<file>\d{1,}_\w{1,}\s\w{1,}_\d{4}-\d{2}-\d{2}\.pdf)$', views.receipt, name="receipt"),
	re_path(r'^(?P<lang>en|fr)/contact/(?P<pk>\w+)/$', views.contact, name='contact'),
	# path('pdf/', views.pdf, name="pdf"),
]