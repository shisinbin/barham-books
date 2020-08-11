from django.urls import path

from . import views

urlpatterns = [
	path('reserve', views.reserve, name="reserve"),
]