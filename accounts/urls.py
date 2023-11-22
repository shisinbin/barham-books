from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf.urls import url

from . import views

urlpatterns = [
	path('login', views.login, name='login'),
	path('register', views.register, name='register'),
	path('logout', views.logout, name='logout'),
	path('dashboard', views.dashboard, name='dashboard'),
    path('records', views.view_records, name='view_records'),
	path('delete', views.delete_reservation, name='delete_reservation'),
    path('extend_all_loans', views.extend_all_loans, name='extend_all_loans'),

    url(r'^password/$', views.change_password, name='change_password'),
    path('password_reset/',
         auth_views.PasswordResetView.as_view(),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'),
    path('edit/', views.edit, name='edit'),
]
