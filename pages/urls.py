from django.urls import path

from . import views

urlpatterns = [
	path('', views.index, name='index'),
	path('about/', views.about, name='about'),
	path('contact/', views.contact, name='contact'),
	path('contact/thanks/', views.contact_thanks, name='contact_thanks'),
    path('home/', views.home, name='home'),
]