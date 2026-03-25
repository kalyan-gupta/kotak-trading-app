"""
WebSocket Server URL Configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    # WebSocket status and management
    path('status/', views.websocket_status_view, name='websocket-status'),
    path('broadcast/', views.broadcast_message_view, name='websocket-broadcast'),
]
