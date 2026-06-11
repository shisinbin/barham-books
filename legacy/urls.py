from django.urls import path
from . import views

app_name = 'legacy'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('books/', views.books, name='books'),
    path('book/', views.book, name='book'),
    path('author/', views.author, name='author'),
    path('all/', views.books_filtered, name='books_all'),
    path('all/<str:letter_choice>/', views.books_filtered, name='books_by_alphabet'),
    path('tags/', views.filter_by_tags, name='filter_by_tags'),
    path('tags/tag_search/', views.tag_search, name='tag_search'),
    path('tags/<slug:tag_slug>/', views.books_filtered, name='books_by_tag'),
    path('category/', views.category, name='category'),
    path('users/', views.users, name='users'),
    path('add-book/', views.add_book, name='add_book'),
]