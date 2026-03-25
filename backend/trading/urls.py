"""
Trading URL Configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    # Order Endpoints
    path('orders/', views.order_list_view, name='order-list'),
    path('orders/place/', views.place_order_view, name='order-place'),
    path('orders/validate/', views.validate_order_view, name='order-validate'),
    path('orders/<uuid:order_id>/', views.order_detail_view, name='order-detail'),
    path('orders/<uuid:order_id>/modify/', views.modify_order_view, name='order-modify'),
    path('orders/<uuid:order_id>/cancel/', views.cancel_order_view, name='order-cancel'),
    path('orders/<uuid:order_id>/status/', views.order_status_view, name='order-status'),
    
    # Position Endpoints
    path('positions/', views.position_list_view, name='position-list'),
    path('positions/live/', views.positions_live_view, name='positions-live'),
    path('positions/<uuid:position_id>/', views.position_detail_view, name='position-detail'),
    path('positions/<uuid:position_id>/close/', views.close_position_view, name='position-close'),
    path('positions/<uuid:position_id>/update/', views.update_position_view, name='position-update'),
    
    # Portfolio Endpoints
    path('holdings/', views.holdings_view, name='holdings'),
    path('funds/', views.funds_view, name='funds'),
    path('order-book/', views.order_book_view, name='order-book'),
    path('trade-book/', views.trade_book_view, name='trade-book'),
    
    # Trade History
    path('trades/', views.trade_history_view, name='trade-history'),
]
