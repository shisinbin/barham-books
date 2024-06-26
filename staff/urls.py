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

# This is for a future implementation of adding books
# urlpatterns += [
#   path('search', views.search_books, name='search_books'),
# ]