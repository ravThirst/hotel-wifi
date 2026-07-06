# wifi/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('room/<int:room_id>/generate/', views.generate_session, name='generate_session'),
]