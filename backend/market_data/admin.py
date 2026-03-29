"""
Market Data Admin Configuration
"""
from django.contrib import admin
from .models import Scrip, Quote, MarketDepth, Watchlist, ScripCache


@admin.register(Scrip)
class ScripAdmin(admin.ModelAdmin):
    """Admin for Scrip model."""
    list_display = [
        'trading_symbol', 'exchange', 'symbol_name', 'instrument_type',
        'is_fno', 'is_active', 'last_updated'
    ]
    list_filter = ['exchange', 'instrument_type', 'is_fno', 'is_active', 'last_updated']
    search_fields = ['trading_symbol', 'symbol_name', 'company_name', 'isin']
    readonly_fields = ['created_at', 'last_updated']
    ordering = ['trading_symbol']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('symbol_token', 'exchange', 'trading_symbol', 'symbol_name')
        }),
        ('Instrument Details', {
            'fields': ('instrument_type', 'company_name', 'industry', 'sector', 'isin')
        }),
        ('F&O Details', {
            'fields': ('expiry_date', 'strike_price', 'lot_size', 'tick_size'),
            'classes': ('collapse',)
        }),
        ('Price Bands', {
            'fields': ('price_high', 'price_low', 'upper_circuit', 'lower_circuit'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_fno')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    """Admin for Quote model."""
    list_display = [
        'scrip', 'last_price', 'change', 'change_percentage',
        'volume', 'last_updated'
    ]
    list_filter = ['last_updated']
    search_fields = ['scrip__trading_symbol', 'scrip__symbol_name']
    readonly_fields = ['last_updated']
    ordering = ['-last_updated']


@admin.register(MarketDepth)
class MarketDepthAdmin(admin.ModelAdmin):
    """Admin for MarketDepth model."""
    list_display = ['quote', 'last_updated']
    readonly_fields = ['last_updated']


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    """Admin for Watchlist model."""
    list_display = ['user', 'name', 'get_scrips_count', 'is_default', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['user__username', 'name']
    filter_horizontal = ['scrips']

    def get_scrips_count(self, obj):
        return obj.scrips.count()
    get_scrips_count.short_description = 'Scrips Count'


@admin.register(ScripCache)
class ScripCacheAdmin(admin.ModelAdmin):
    """Admin for ScripCache model."""
    list_display = ['exchange', 'last_synced', 'record_count', 'is_syncing']
    readonly_fields = ['last_synced']
