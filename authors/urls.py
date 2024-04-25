from django.urls import path

from . import views

urlpatterns = [
	path('<int:author_id>/<str:slug>/', views.author, name='author'),
  
	path('<int:pk>/update/', views.AuthorUpdate.as_view(), name='author_update'),
]