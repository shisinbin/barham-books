from django.urls import path

from . import views

urlpatterns = [
	path('', views.index, name='staff'),
	path('users', views.users, name='users'),
	path('users/<int:user_id>', views.user, name='user'),
	path('loan_books/<int:user_id>', views.loan_books, name='loan_books'),
	path('return_books/<int:user_id>', views.return_books, name="return_books"),
    path('return_single_book/<int:record_id>', views.return_single_book, name="return_single_book"),
	path('execute', views.execute, name="execute"),
    path('staff_edit/<int:user_id>', views.staff_edit, name='staff_edit'),
    path('del_copy/<int:book_id>', views.del_copy, name='del_copy'),
    path('add_copy/<int:book_id>', views.add_copy, name='add_copy'),
    path('amend_author/<int:book_id>', views.amend_author, name='amend_author'),
]

# Two paths connected with adding a book image cover for books without a cover
urlpatterns += [
    path('lookup_book_cover/<int:book_id>', views.lookup_book_cover, name='lookup_book_cover'),
    path('associate_book_cover/<int:book_id>', views.associate_book_cover, name='associate_book_cover'),
]

urlpatterns += [
    path('book/<int:book_id>/lookup-cover/', views.book_cover_lookup_page, name='book_cover_lookup_page'),
    path('api/book/<int:book_id>/cover_candidates/', views.lookup_book_cover_candidates, name='lookup_book_cover_candidates'),
    path('api/book/<int:book_id>/attach-cover/', views.attach_book_cover, name='attach_book_cover'),
]

# new add book pages
urlpatterns += [
    path("books/add/", views.AddBookLookupView.as_view(), name="book_add_lookup"),
    path("books/add/select/", views.AddBookSelectView.as_view(), name="book_add_select"),
    path("books/add/edit/", views.AddBookEditView.as_view(), name="book_add_edit"),
    path("books/add/confirm/", views.AddBookConfirmView.as_view(), name="book_add_confirm"),
]