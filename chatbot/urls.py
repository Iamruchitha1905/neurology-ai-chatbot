from django.urls import path
from . import views, views_auth

urlpatterns = [
    path('', views.home, name='home'),
    path('chat/', views.chat_view, name='chat_view'),
    path('register/', views_auth.register_view, name='register'),
    path('login/', views_auth.login_view, name='login'),
    path('logout/', views_auth.logout_view, name='logout'),
]
