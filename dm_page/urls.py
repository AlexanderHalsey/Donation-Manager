from django.urls import path
from dm_page import views
	
urlpatterns = [
	path('', views.dashboard, name='dashboard'),
	path('contact/<str:pk>/', views.contact, name='contact'),
]