from django.urls import path
from dm_page import views
	
urlpatterns = [
	path('login/', views.loginUser, name='login'),
	path('logout/', views.logoutUser, name='logout'),
	path('webhooks/7f6qy3IqT5L2x75mFoUkaEdrY9Kuutuu2dzbuxOwcfw/', views.dms_webhook),
	path('webhooklogs/', views.webhooklogs),
	path('', views.dashboard, name='dashboard'),
	path('donators/', views.donators, name="donators"),
	path('contact/<str:pk>/', views.contact, name='contact'),
	# path('pdf/', views.pdf, name="pdf"),
]