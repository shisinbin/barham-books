from django.urls import path

from . import views

urlpatterns = [
	path('', views.index, name='books'),
	path('<int:book_id>/<str:slug>/', views.book, name='book'),
	path('<int:book_id>/add_review', views.add_review, name='add_review'),
    path('delete_review/<int:review_id>/', views.del_review, name='del_review'),
    path('tags/', views.filter_by_tags, name="filter_by_tags"),
	path('tags/tag_search', views.tag_search, name='tag_search'),
    path('book_search', views.book_search, name='book_search'),

    # a to z list and tags
    path('all/', views.books_filtered, name='books_all'),
    path('all/<str:letter_choice>/', views.books_filtered, name='books_by_alphabet'),
    path('tags/<slug:tag_slug>/', views.books_filtered, name='books_by_tag'),

    # for likes, uses AJAX
    path('like/', views.book_like, name='like'),

    # category
    path('category/<str:category_code>/', views.category, name='category'),

    # custom add new book form
    path('add/', views.add_book, name='add_book'),
]

urlpatterns += [
    #class-based views
	path('books/<int:pk>/update/', views.BookUpdate.as_view(), name='book_update'),
    path('books/create/', views.BookCreate.as_view(), name='book_create'),

    path('books/<int:pk>/update_super/', views.BookUpdateSuper.as_view(), name='book_update_super'),

    path('books/<int:pk>/update_instance/', views.BookInstanceUpdate.as_view(), name='book_instance_update'),
	]