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
]