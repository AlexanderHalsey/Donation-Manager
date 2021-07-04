from django.urls import path
from dm_page import views
	
urlpatterns = [
	path('', views.dashboard, name='dashboard'),
	path('donators/', views.donators, name="donators"),
	path('contact/<str:pk>/', views.contact, name='contact'),
	path('pdf', views.pdf, name="pdf"),
	path("pdf_test", views.pdf_test, name="pdf_test"),
]