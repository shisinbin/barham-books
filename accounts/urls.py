from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from .forms import PasswordResetTurnstileForm

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),

    path("home/", views.account_home, name="account_home"),

    path("password/", views.CustomPasswordChangeView.as_view(), name="password_change"),

    path("password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url=reverse_lazy("password_reset_done"),
            form_class=PasswordResetTurnstileForm,
        ),
        name="password_reset"
    ),

    path("password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done"
    ),

    path("reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("password_reset_complete"),
        ),
        name="password_reset_confirm"
    ),

    path("reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete"
    ),
]


# from django.urls import path
# from django.contrib.auth import views as auth_views
# from django.conf.urls import url

# from . import views

# urlpatterns = [
# 	path('login', views.login, name='login'),
# 	path('register', views.register, name='register'),
# 	path('logout', views.logout, name='logout'),
# 	path('dashboard', views.dashboard, name='dashboard'),
#     path('records', views.view_records, name='view_records'),
# 	path('delete', views.delete_reservation, name='delete_reservation'),
#     path('extend_all_loans', views.extend_all_loans, name='extend_all_loans'),

#     url(r'^password/$', views.change_password, name='change_password'),
#     path('password_reset/',
#          auth_views.PasswordResetView.as_view(),
#          name='password_reset'),
#     path('password_reset/done/',
#          auth_views.PasswordResetDoneView.as_view(),
#          name='password_reset_done'),
#     path('reset/<uidb64>/<token>/',
#          auth_views.PasswordResetConfirmView.as_view(),
#          name='password_reset_confirm'),
#     path('reset/done/',
#          auth_views.PasswordResetCompleteView.as_view(),
#          name='password_reset_complete'),
#     path('edit/', views.edit, name='edit'),
# ]