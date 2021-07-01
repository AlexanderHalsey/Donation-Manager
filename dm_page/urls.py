from django.urls import path
from dm_page import views
	
urlpatterns = [
	path('', views.dashboard, name='dashboard'),
	path('donators/', views.donators, name="donators"),
	path('contact/<str:pk>/', views.contact, name='contact'),
	path('receipt/', views.receipt, name="receipt"),
]