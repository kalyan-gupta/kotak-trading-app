"""
Market Data Serializers
"""
from rest_framework import serializers
from .models import Scrip, Quote, MarketDepth, Watchlist, ScripCache


class ScripSerializer(serializers.ModelSerializer):
    """Serializer for Scrip model."""
    
    exchange_display = serializers.CharField(
        source='get_exchange_display',
        read_only=True
    )
    instrument_type_display = serializers.CharField(
        source='get_instrument_type_display',
        read_only=True
    )
    display_name = serializers.CharField(read_only=True)
    is_option = serializers.BooleanField(read_only=True)
    is_future = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Scrip
        fields = [
            'id', 'symbol_token', 'exchange', 'exchange_display',
            'trading_symbol', 'symbol_name', 'instrument_type',
            'instrument_type_display', 'company_name', 'industry',
            'sector', 'isin', 'expiry_date', 'strike_price',
            'lot_size', 'tick_size', 'price_high', 'price_low',
            'upper_circuit', 'lower_circuit', 'is_active', 'is_fno',
            'display_name', 'is_option', 'is_future',
            'last_updated', 'created_at'
        ]


class ScripSearchSerializer(serializers.ModelSerializer):
    """Lightweight serializer for scrip search results."""
    
    class Meta:
        model = Scrip
        fields = [
            'id', 'symbol_token', 'exchange', 'trading_symbol',
            'symbol_name', 'instrument_type', 'company_name',
            'expiry_date', 'strike_price', 'lot_size', 'is_fno'
        ]


class QuoteSerializer(serializers.ModelSerializer):
    """Serializer for Quote model."""
    
    scrip_details = ScripSerializer(source='scrip', read_only=True)
    spread = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    spread_percentage = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Quote
        fields = [
            'id', 'scrip', 'scrip_details', 'last_price', 'change',
            'change_percentage', 'open_price', 'high_price', 'low_price',
            'close_price', 'volume', 'total_buy_quantity', 'total_sell_quantity',
            'bid_price', 'bid_quantity', 'ask_price', 'ask_quantity',
            'week_52_high', 'week_52_low', 'average_price', 'oi', 'oi_change',
            'spread', 'spread_percentage', 'last_updated'
        ]


class QuoteLiteSerializer(serializers.ModelSerializer):
    """Lightweight quote serializer for lists."""
    
    trading_symbol = serializers.CharField(source='scrip.trading_symbol', read_only=True)
    exchange = serializers.CharField(source='scrip.exchange', read_only=True)
    
    class Meta:
        model = Quote
        fields = [
            'id', 'trading_symbol', 'exchange', 'last_price',
            'change', 'change_percentage', 'volume', 'last_updated'
        ]


class MarketDepthSerializer(serializers.ModelSerializer):
    """Serializer for MarketDepth model."""
    
    buy_levels = serializers.SerializerMethodField()
    sell_levels = serializers.SerializerMethodField()
    
    class Meta:
        model = MarketDepth
        fields = [
            'id', 'buy_levels', 'sell_levels', 'last_updated'
        ]
    
    def get_buy_levels(self, obj):
        return obj.get_buy_levels()
    
    def get_sell_levels(self, obj):
        return obj.get_sell_levels()


class FullQuoteSerializer(serializers.ModelSerializer):
    """Full quote serializer with depth."""
    
    scrip_details = ScripSerializer(source='scrip', read_only=True)
    depth = MarketDepthSerializer(read_only=True)
    spread = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    spread_percentage = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Quote
        fields = [
            'id', 'scrip', 'scrip_details', 'last_price', 'change',
            'change_percentage', 'open_price', 'high_price', 'low_price',
            'close_price', 'volume', 'total_buy_quantity', 'total_sell_quantity',
            'bid_price', 'bid_quantity', 'ask_price', 'ask_quantity',
            'week_52_high', 'week_52_low', 'average_price', 'oi', 'oi_change',
            'spread', 'spread_percentage', 'depth', 'last_updated'
        ]


class WatchlistSerializer(serializers.ModelSerializer):
    """Serializer for Watchlist model."""
    
    scrips_count = serializers.IntegerField(
        source='scrips.count',
        read_only=True
    )
    scrips = ScripSerializer(many=True, read_only=True)
    
    class Meta:
        model = Watchlist
        fields = [
            'id', 'name', 'scrips', 'scrips_count', 'is_default',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class WatchlistCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating watchlists."""
    
    class Meta:
        model = Watchlist
        fields = ['name', 'is_default']


class WatchlistAddScripSerializer(serializers.Serializer):
    """Serializer for adding scrip to watchlist."""
    scrip_id = serializers.IntegerField(required=True)


class WatchlistRemoveScripSerializer(serializers.Serializer):
    """Serializer for removing scrip from watchlist."""
    scrip_id = serializers.IntegerField(required=True)


class ScripCacheSerializer(serializers.ModelSerializer):
    """Serializer for ScripCache model."""
    
    exchange_display = serializers.CharField(
        source='get_exchange_display',
        read_only=True
    )
    
    class Meta:
        model = ScripCache
        fields = [
            'id', 'exchange', 'exchange_display', 'last_synced',
            'record_count', 'is_syncing'
        ]


class HistoricalDataRequestSerializer(serializers.Serializer):
    """Serializer for historical data request."""
    symbol_token = serializers.CharField(required=True)
    exchange = serializers.CharField(required=True)
    interval = serializers.ChoiceField(
        choices=[
            ('1minute', '1 Minute'),
            ('5minute', '5 Minutes'),
            ('15minute', '15 Minutes'),
            ('30minute', '30 Minutes'),
            ('1hour', '1 Hour'),
            ('1day', '1 Day'),
        ],
        default='1day'
    )
    from_date = serializers.DateField(required=True)
    to_date = serializers.DateField(required=True)


class HistoricalDataSerializer(serializers.Serializer):
    """Serializer for historical OHLCV data."""
    timestamp = serializers.DateTimeField()
    open = serializers.DecimalField(max_digits=15, decimal_places=2)
    high = serializers.DecimalField(max_digits=15, decimal_places=2)
    low = serializers.DecimalField(max_digits=15, decimal_places=2)
    close = serializers.DecimalField(max_digits=15, decimal_places=2)
    volume = serializers.BigIntegerField()


class IndexQuoteSerializer(serializers.Serializer):
    """Serializer for index quotes."""
    name = serializers.CharField()
    last_price = serializers.DecimalField(max_digits=15, decimal_places=2)
    change = serializers.DecimalField(max_digits=15, decimal_places=2)
    change_percentage = serializers.DecimalField(max_digits=10, decimal_places=2)
    open = serializers.DecimalField(max_digits=15, decimal_places=2)
    high = serializers.DecimalField(max_digits=15, decimal_places=2)
    low = serializers.DecimalField(max_digits=15, decimal_places=2)
    previous_close = serializers.DecimalField(max_digits=15, decimal_places=2)
