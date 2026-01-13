from django.urls import path

from . import views

urlpatterns = [
	path('<int:author_id>/<str:slug>/', views.author, name='author'),
	path('update/<int:pk>/', views.AuthorUpdate.as_view(), name='author_update'),
]