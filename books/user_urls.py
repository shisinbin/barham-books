from django.urls import path
from . import views

urlpatterns = [
    path('<str:username>/', views.user_reviews, name='user_reviews')
]