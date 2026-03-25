"""
WebSocket Routing Configuration
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Market data WebSocket
    re_path(r'ws/market-data/$', consumers.MarketDataConsumer.as_asgi()),
    
    # Order updates WebSocket
    re_path(r'ws/order-updates/$', consumers.OrderUpdatesConsumer.as_asgi()),
    
    # Portfolio updates WebSocket
    re_path(r'ws/portfolio-updates/$', consumers.PortfolioUpdatesConsumer.as_asgi()),
]
