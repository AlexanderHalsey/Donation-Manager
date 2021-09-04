from django.urls import path, re_path
from dm_page import views
	
urlpatterns = [
	re_path(r'^(?P<lang>en|fr)/login/$', views.loginUser, name='login'),
	re_path(r'^(?P<lang>en|fr)/logout/$', views.logoutUser, name='logout'),
	path('webhooks/7f6qy3IqT5L2x75mFoUkaEdrY9Kuutuu2dzbuxOwcfw/', views.dms_webhook),
	re_path(r'^(?P<lang>en|fr)/webhooklogs/$', views.webhooklogs),
	re_path(r'^(?P<lang>en|fr)/$', views.dashboard, name='dashboard'),
	re_path(r'^(?P<lang>en|fr)/donators/$', views.donators, name="donators"),
	re_path(r'^(?P<lang>en|fr)/contact/(?P<pk>\w+)/$', views.contact, name='contact'),
	# path('pdf/', views.pdf, name="pdf"),
]