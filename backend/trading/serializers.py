"""
Trading Serializers
"""
from rest_framework import serializers
from .models import Order, Position, Trade, OrderBook, TradeBook


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model."""
    
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    order_type_display = serializers.CharField(
        source='get_order_type_display',
        read_only=True
    )
    product_type_display = serializers.CharField(
        source='get_product_type_display',
        read_only=True
    )
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )
    exchange_display = serializers.CharField(
        source='get_exchange_display',
        read_only=True
    )
    
    is_cancellable = serializers.BooleanField(read_only=True)
    is_modifiable = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'parent_order_id', 'exchange', 'exchange_display',
            'trading_symbol', 'symbol_token', 'instrument_type',
            'transaction_type', 'transaction_type_display',
            'order_type', 'order_type_display',
            'product_type', 'product_type_display',
            'quantity', 'disclosed_quantity', 'price', 'trigger_price',
            'stop_loss', 'target', 'trailing_stop_loss',
            'status', 'status_display', 'status_message',
            'filled_quantity', 'pending_quantity', 'cancelled_quantity',
            'average_price', 'validity', 'is_amo', 'amo_time',
            'max_loss', 'tags', 'is_cancellable', 'is_modifiable',
            'created_at', 'updated_at', 'executed_at'
        ]
        read_only_fields = [
            'id', 'order_id', 'status', 'status_message',
            'filled_quantity', 'pending_quantity', 'cancelled_quantity',
            'average_price', 'created_at', 'updated_at', 'executed_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders."""
    
    class Meta:
        model = Order
        fields = [
            'exchange', 'trading_symbol', 'symbol_token', 'instrument_type',
            'transaction_type', 'order_type', 'product_type',
            'quantity', 'disclosed_quantity', 'price', 'trigger_price',
            'stop_loss', 'target', 'trailing_stop_loss',
            'validity', 'is_amo', 'amo_time', 'max_loss', 'tags'
        ]
    
    def validate(self, data):
        """Validate order data."""
        order_type = data.get('order_type')
        price = data.get('price', 0)
        trigger_price = data.get('trigger_price', 0)
        
        # Validate limit orders
        if order_type == Order.ORDER_TYPE_LIMIT and price <= 0:
            raise serializers.ValidationError({
                'price': 'Price is required for limit orders.'
            })
        
        # Validate SL orders
        if order_type in [Order.ORDER_TYPE_SL, Order.ORDER_TYPE_SLM]:
            if trigger_price <= 0:
                raise serializers.ValidationError({
                    'trigger_price': 'Trigger price is required for SL orders.'
                })
        
        # Validate BO/CO fields
        product_type = data.get('product_type')
        if product_type == Order.PRODUCT_BO:
            if not data.get('stop_loss'):
                raise serializers.ValidationError({
                    'stop_loss': 'Stop loss is required for bracket orders.'
                })
            if not data.get('target'):
                raise serializers.ValidationError({
                    'target': 'Target is required for bracket orders.'
                })
        
        if product_type == Order.PRODUCT_CO:
            if not data.get('stop_loss'):
                raise serializers.ValidationError({
                    'stop_loss': 'Stop loss is required for cover orders.'
                })
        
        return data


class OrderModifySerializer(serializers.Serializer):
    """Serializer for modifying orders."""
    quantity = serializers.IntegerField(required=False, min_value=1)
    price = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False
    )
    trigger_price = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False
    )
    stop_loss = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False
    )
    target = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False
    )


class PositionSerializer(serializers.ModelSerializer):
    """Serializer for Position model."""
    
    position_type_display = serializers.CharField(
        source='get_position_type_display',
        read_only=True
    )
    product_type_display = serializers.CharField(
        source='get_product_type_display',
        read_only=True
    )
    exchange_display = serializers.CharField(
        source='get_exchange_display',
        read_only=True
    )
    
    total_pnl = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    pnl_percentage = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    current_value = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    invested_value = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = Position
        fields = [
            'id', 'exchange', 'exchange_display', 'trading_symbol',
            'symbol_token', 'instrument_type', 'position_type',
            'position_type_display', 'product_type', 'product_type_display',
            'quantity', 'buy_quantity', 'sell_quantity',
            'average_price', 'buy_average', 'sell_average',
            'last_price', 'close_price',
            'realized_pnl', 'unrealized_pnl', 'total_pnl', 'pnl_percentage',
            'current_value', 'invested_value',
            'stop_loss', 'target', 'is_open',
            'opened_at', 'closed_at', 'updated_at'
        ]
        read_only_fields = fields


class PositionUpdateSerializer(serializers.Serializer):
    """Serializer for updating position (SL/Target)."""
    stop_loss = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False
    )
    target = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False
    )


class ClosePositionSerializer(serializers.Serializer):
    """Serializer for closing positions."""
    quantity = serializers.IntegerField(required=False, min_value=1)
    order_type = serializers.ChoiceField(
        choices=Order.ORDER_TYPE_CHOICES,
        default=Order.ORDER_TYPE_MARKET
    )
    price = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        default=0
    )


class TradeSerializer(serializers.ModelSerializer):
    """Serializer for Trade model."""
    
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )
    exchange_display = serializers.CharField(
        source='get_exchange_display',
        read_only=True
    )
    total_charges = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    net_value = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = Trade
        fields = [
            'id', 'trade_id', 'order_id', 'exchange', 'exchange_display',
            'trading_symbol', 'symbol_token', 'transaction_type',
            'transaction_type_display', 'quantity', 'price',
            'brokerage', 'stt', 'exchange_charges', 'gst',
            'stamp_duty', 'sebi_charges', 'total_charges',
            'realized_pnl', 'net_value', 'executed_at', 'created_at'
        ]
        read_only_fields = fields


class OrderBookSerializer(serializers.ModelSerializer):
    """Serializer for OrderBook model."""
    
    class Meta:
        model = OrderBook
        fields = [
            'id', 'order_id', 'exchange', 'trading_symbol',
            'transaction_type', 'order_type', 'product_type',
            'quantity', 'price', 'trigger_price', 'status',
            'status_message', 'filled_quantity', 'pending_quantity',
            'average_price', 'last_synced_at'
        ]
        read_only_fields = fields


class TradeBookSerializer(serializers.ModelSerializer):
    """Serializer for TradeBook model."""
    
    class Meta:
        model = TradeBook
        fields = [
            'id', 'trade_id', 'order_id', 'exchange', 'trading_symbol',
            'transaction_type', 'quantity', 'price',
            'trade_date', 'last_synced_at'
        ]
        read_only_fields = fields


class HoldingsSerializer(serializers.Serializer):
    """Serializer for holdings data."""
    exchange = serializers.CharField()
    trading_symbol = serializers.CharField()
    symbol_token = serializers.CharField()
    isin = serializers.CharField()
    quantity = serializers.IntegerField()
    t1_quantity = serializers.IntegerField()
    average_price = serializers.DecimalField(max_digits=15, decimal_places=2)
    last_price = serializers.DecimalField(max_digits=15, decimal_places=2)
    close_price = serializers.DecimalField(max_digits=15, decimal_places=2)
    pnl = serializers.DecimalField(max_digits=15, decimal_places=2)
    day_pnl = serializers.DecimalField(max_digits=15, decimal_places=2)
    investment = serializers.DecimalField(max_digits=15, decimal_places=2)
    current_value = serializers.DecimalField(max_digits=15, decimal_places=2)


class FundsSerializer(serializers.Serializer):
    """Serializer for funds/margin data."""
    available_cash = serializers.DecimalField(max_digits=15, decimal_places=2)
    available_margin = serializers.DecimalField(max_digits=15, decimal_places=2)
    used_margin = serializers.DecimalField(max_digits=15, decimal_places=2)
    opening_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    payin_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    payout_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    span_margin = serializers.DecimalField(max_digits=15, decimal_places=2)
    exposure_margin = serializers.DecimalField(max_digits=15, decimal_places=2)
    available_balance = serializers.DecimalField(max_digits=15, decimal_places=2)


class OrderValidationSerializer(serializers.Serializer):
    """Serializer for order validation response."""
    is_valid = serializers.BooleanField()
    message = serializers.CharField()
    required_margin = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False
    )
    available_margin = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False
    )
    warnings = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    errors = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


class PnLSerializer(serializers.Serializer):
    """Serializer for P&L summary."""
    date = serializers.DateField()
    realized_pnl = serializers.DecimalField(max_digits=15, decimal_places=2)
    unrealized_pnl = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_pnl = serializers.DecimalField(max_digits=15, decimal_places=2)
    charges = serializers.DecimalField(max_digits=15, decimal_places=2)
    net_pnl = serializers.DecimalField(max_digits=15, decimal_places=2)
    trades_count = serializers.IntegerField()
