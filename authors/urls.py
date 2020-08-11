from django.urls import path

from . import views

urlpatterns = [
	path('<int:author_id>/<str:slug>/', views.author, name='author'),
]