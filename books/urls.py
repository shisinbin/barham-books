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
	path('update/<int:pk>/', views.BookUpdate.as_view(), name='book_update'),
    path('create/', views.BookCreate.as_view(), name='book_create'),

    path('super_update/<int:pk>/', views.BookUpdateSuper.as_view(), name='book_update_super'),

    path('update_instance/<int:pk>/', views.BookInstanceUpdate.as_view(), name='book_instance_update'),
	]

urlpatterns += [
    # books for sale
    path('books-for-sale/', views.books_for_sale_list, name='books_for_sale_list'),
    path('books-for-sale/add/', views.BookForSaleCreateView.as_view(), name='book_for_sale_add'),
    path('books-for-sale/<slug:slug>/', views.book_for_sale_detail, name='book_for_sale_detail'),
    path('books-for-sale/category/<str:sale_category_code>/', views.books_for_sale_list, name='books_for_sale_by_category'),
    path('books-for-sale/<slug:slug>/edit/', views.BookForSaleUpdateView.as_view(), name='book_for_sale_edit'),
]

urlpatterns += [
    path('books-for-sale/<int:book_id>/lookup_book_cover/', views.lookup_book_for_sale_cover, name='lookup_book_for_sale_cover'),
    path('books-for-sale/<int:book_id>/associate_book_cover/', views.associate_book_for_sale_cover, name='associate_book_for_sale_cover'),
]

urlpatterns += [
    path('books_for_sale/<slug:slug>/delete/', views.delete_book_for_sale, name='book_for_sale_delete'),
]

urlpatterns += [
    path('autocomplete/', views.autocomplete_books, name='autocomplete_books'),
]

#collections
urlpatterns += [
    path('collections/', views.collections_index, name='collections'),
    path('collections/<slug:slug>/', views.collection_detail, name='collection_detail'),
]

# explore
urlpatterns += [
    path('explore/', views.explore_books, name='explore_books'),
]

# new book search
urlpatterns += [
    path('search/', views.book_search_redux, name='book_search_redux'),
]

# registering book interest
urlpatterns += [
    path('interest/add/', views.register_interest, name='register_interest'),
    path('interest/remove/', views.delete_interest, name='delete_interest'),
]

# new a-z
urlpatterns += [
    path('a-z/', views.books_a_z, name='books_a_z'),
    path('a-z/<str:letter>/', views.books_a_z, name='books_a_z_letter'),
]

urlpatterns += [
    path('<int:book_id>/review/add/', views.ReviewCreateView.as_view(), name='review_add'),
    path('reviews/<int:pk>/edit/', views.ReviewUpdateView.as_view(), name='review_edit'),
    path('reviews/<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='review_delete'),
]

# temporary production book page
# urlpatterns += [
#     path('v2/book/', views.book_v2, name='book_v2'),
# ]