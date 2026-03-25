"""
Market Data URL Configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    # Scrip Search
    path('scrips/search/', views.search_scrips_view, name='scrip-search'),
    path('scrips/detail/<str:symbol_token>/', views.scrip_detail_view, name='scrip-detail'),
    path('scrips/by-symbol/', views.scrip_by_symbol_view, name='scrip-by-symbol'),
    
    # Quotes
    path('quotes/', views.get_quote_view, name='get-quote'),
    path('quotes/multiple/', views.get_multiple_quotes_view, name='get-multiple-quotes'),
    path('quotes/depth/', views.get_market_depth_view, name='market-depth'),
    
    # Watchlists
    path('watchlists/', views.watchlist_list_view, name='watchlist-list'),
    path('watchlists/create/', views.watchlist_create_view, name='watchlist-create'),
    path('watchlists/<int:watchlist_id>/', views.watchlist_detail_view, name='watchlist-detail'),
    path('watchlists/<int:watchlist_id>/add/', views.watchlist_add_scrip_view, name='watchlist-add-scrip'),
    path('watchlists/<int:watchlist_id>/remove/', views.watchlist_remove_scrip_view, name='watchlist-remove-scrip'),
    
    # Scrip Master Data
    path('scrips/cache-status/', views.scrip_cache_status_view, name='scrip-cache-status'),
    path('scrips/sync/', views.sync_scrip_master_view, name='scrip-sync'),
    
    # Historical Data
    path('historical/', views.historical_data_view, name='historical-data'),
    
    # Indices
    path('indices/', views.index_quotes_view, name='index-quotes'),
    path('top-movers/', views.top_gainers_losers_view, name='top-movers'),
]
