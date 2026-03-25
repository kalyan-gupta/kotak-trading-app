"""
Trading Admin Configuration
"""
from django.contrib import admin
from .models import Order, Position, Trade, OrderBook, TradeBook


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin for Order model."""
    list_display = [
        'order_id', 'user', 'trading_symbol', 'transaction_type',
        'order_type', 'product_type', 'quantity', 'price',
        'status', 'created_at'
    ]
    list_filter = [
        'status', 'order_type', 'product_type', 'transaction_type',
        'exchange', 'created_at'
    ]
    search_fields = ['order_id', 'trading_symbol', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'executed_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Order Identification', {
            'fields': ('id', 'order_id', 'parent_order_id', 'user')
        }),
        ('Scrip Details', {
            'fields': ('exchange', 'trading_symbol', 'symbol_token', 'instrument_type')
        }),
        ('Order Details', {
            'fields': ('transaction_type', 'order_type', 'product_type', 'validity')
        }),
        ('Quantity & Price', {
            'fields': ('quantity', 'disclosed_quantity', 'price', 'trigger_price')
        }),
        ('Bracket/Cover Order', {
            'fields': ('stop_loss', 'target', 'trailing_stop_loss'),
            'classes': ('collapse',)
        }),
        ('Execution', {
            'fields': ('status', 'status_message', 'filled_quantity', 
                      'pending_quantity', 'cancelled_quantity', 'average_price')
        }),
        ('AMO', {
            'fields': ('is_amo', 'amo_time'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'executed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """Admin for Position model."""
    list_display = [
        'trading_symbol', 'user', 'position_type', 'product_type',
        'quantity', 'average_price', 'last_price', 'unrealized_pnl',
        'is_open', 'opened_at'
    ]
    list_filter = ['position_type', 'product_type', 'is_open', 'exchange', 'opened_at']
    search_fields = ['trading_symbol', 'user__username']
    readonly_fields = ['id', 'opened_at', 'closed_at', 'updated_at']
    ordering = ['-opened_at']


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    """Admin for Trade model."""
    list_display = [
        'trade_id', 'user', 'trading_symbol', 'transaction_type',
        'quantity', 'price', 'realized_pnl', 'executed_at'
    ]
    list_filter = ['transaction_type', 'exchange', 'executed_at']
    search_fields = ['trade_id', 'trading_symbol', 'user__username']
    readonly_fields = ['id', 'created_at']
    ordering = ['-executed_at']


@admin.register(OrderBook)
class OrderBookAdmin(admin.ModelAdmin):
    """Admin for OrderBook model."""
    list_display = ['order_id', 'trading_symbol', 'status', 'last_synced_at']
    list_filter = ['status', 'exchange']
    readonly_fields = ['id', 'last_synced_at']
    ordering = ['-last_synced_at']


@admin.register(TradeBook)
class TradeBookAdmin(admin.ModelAdmin):
    """Admin for TradeBook model."""
    list_display = ['trade_id', 'trading_symbol', 'trade_date', 'last_synced_at']
    list_filter = ['exchange', 'trade_date']
    readonly_fields = ['id', 'last_synced_at']
    ordering = ['-trade_date']
