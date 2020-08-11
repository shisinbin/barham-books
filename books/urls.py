from django.urls import path

from . import views

urlpatterns = [
	path('', views.index, name='books'),
	path('<int:book_id>/<str:slug>/', views.book, name='book'),
	path('<int:book_id>/add_review', views.add_review, name='add_review'),
	path('search', views.search, name='search'),
	path('genre/<int:genre_id>', views.genre, name='genre'),

    # a to z list and tags
    path('all/', views.books_filtered, name='books_all'),
    path('all/<str:letter_choice>/', views.books_filtered, name='books_by_alphabet'),
    path('tag/<slug:tag_slug>/', views.books_filtered, name='books_by_tag')
]

urlpatterns += [
	path('books/<int:pk>/update/', views.BookUpdate.as_view(), name='book_update'),
	]