from django.urls import path
from dm_page import views
	
urlpatterns = [
	path('login/', views.loginUser, name='login'),
	path('logout/', views.logoutUser, name='logout'),
	path('webhooks/', views.webhooks),
	path('', views.dashboard, name='dashboard'),
	path('donators/', views.donators, name="donators"),
	path('contact/<str:pk>/', views.contact, name='contact'),
	path('pdf/', views.pdf, name="pdf"),
]