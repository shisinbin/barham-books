from django.urls import path
from . import views

app_name = 'legacy'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('books/', views.books, name='books'),
    path('book/', views.book, name='book'),
    path('author/', views.author, name='author'),
]