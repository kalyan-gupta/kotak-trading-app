"""
WebSocket Server App Configuration
"""
from django.apps import AppConfig


class WebSocketServerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'websocket_server'
    verbose_name = 'WebSocket Server'
