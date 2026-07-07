# wifi/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('room/<int:room_id>/ticket/', views.print_ticket, name='print_ticket'),
    path('room/<int:room_id>/process/', views.handle_session, name='handle_session'),
]