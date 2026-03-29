"""
Trading Models - Orders, Positions, and Trades
"""
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Order(models.Model):
    """Model for trading orders."""
    
    # Order Types
    ORDER_TYPE_MARKET = 'MARKET'
    ORDER_TYPE_LIMIT = 'LIMIT'
    ORDER_TYPE_SL = 'SL'
    ORDER_TYPE_SLM = 'SL-M'
    ORDER_TYPE_CHOICES = [
        (ORDER_TYPE_MARKET, 'Market'),
        (ORDER_TYPE_LIMIT, 'Limit'),
        (ORDER_TYPE_SL, 'Stop Loss'),
        (ORDER_TYPE_SLM, 'Stop Loss Market'),
    ]
    
    # Product Types
    PRODUCT_INTRADAY = 'INTRADAY'
    PRODUCT_DELIVERY = 'DELIVERY'
    PRODUCT_CO = 'CO'
    PRODUCT_BO = 'BO'
    PRODUCT_AMO = 'AMO'
    PRODUCT_CHOICES = [
        (PRODUCT_INTRADAY, 'Intraday (MIS)'),
        (PRODUCT_DELIVERY, 'Delivery (CNC)'),
        (PRODUCT_CO, 'Cover Order'),
        (PRODUCT_BO, 'Bracket Order'),
        (PRODUCT_AMO, 'After Market Order'),
    ]
    
    # Transaction Types
    TRANSACTION_BUY = 'BUY'
    TRANSACTION_SELL = 'SELL'
    TRANSACTION_CHOICES = [
        (TRANSACTION_BUY, 'Buy'),
        (TRANSACTION_SELL, 'Sell'),
    ]
    
    # Order Status
    STATUS_PENDING = 'PENDING'
    STATUS_OPEN = 'OPEN'
    STATUS_COMPLETE = 'COMPLETE'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_MODIFIED = 'MODIFIED'
    STATUS_AMO = 'AMO'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_OPEN, 'Open'),
        (STATUS_COMPLETE, 'Complete'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_MODIFIED, 'Modified'),
        (STATUS_AMO, 'AMO'),
    ]
    
    # Exchange
    EXCHANGE_NSE = 'NSE'
    EXCHANGE_BSE = 'BSE'
    EXCHANGE_NFO = 'NFO'
    EXCHANGE_BFO = 'BFO'
    EXCHANGE_MCX = 'MCX'
    EXCHANGE_CDS = 'CDS'
    EXCHANGE_CHOICES = [
        (EXCHANGE_NSE, 'NSE'),
        (EXCHANGE_BSE, 'BSE'),
        (EXCHANGE_NFO, 'NFO'),
        (EXCHANGE_BFO, 'BFO'),
        (EXCHANGE_MCX, 'MCX'),
        (EXCHANGE_CDS, 'CDS'),
    ]
    
    # Primary Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    
    # Order Identification
    order_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        help_text="Order ID from Kotak"
    )
    parent_order_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Parent order ID for CO/BO"
    )
    
    # Scrip Details
    exchange = models.CharField(
        max_length=10,
        choices=EXCHANGE_CHOICES,
        default=EXCHANGE_NSE
    )
    trading_symbol = models.CharField(max_length=50)
    symbol_token = models.CharField(
        max_length=50,
        help_text="Unique token for the scrip"
    )
    instrument_type = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="EQ, FUT, CE, PE, etc."
    )
    
    # Order Details
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_CHOICES
    )
    order_type = models.CharField(
        max_length=10,
        choices=ORDER_TYPE_CHOICES,
        default=ORDER_TYPE_MARKET
    )
    product_type = models.CharField(
        max_length=15,
        choices=PRODUCT_CHOICES,
        default=PRODUCT_INTRADAY
    )
    
    # Quantity and Price
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)]
    )
    disclosed_quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Price for limit orders"
    )
    trigger_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Trigger price for SL orders"
    )
    
    # Bracket Order / Cover Order Fields
    stop_loss = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Stop loss price for BO"
    )
    target = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Target price for BO"
    )
    trailing_stop_loss = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Trailing stop loss value"
    )
    
    # Status and Execution
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    status_message = models.TextField(
        blank=True,
        null=True,
        help_text="Status message from exchange"
    )
    
    # Execution Details
    filled_quantity = models.IntegerField(default=0)
    pending_quantity = models.IntegerField(default=0)
    cancelled_quantity = models.IntegerField(default=0)
    average_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    
    # Validity
    validity = models.CharField(
        max_length=10,
        default='DAY',
        help_text="DAY, IOC, etc."
    )
    
    # AMO Fields
    is_amo = models.BooleanField(default=False)
    amo_time = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="AMO execution time"
    )
    
    # Risk Management
    max_loss = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Maximum loss allowed for this order"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    executed_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    tags = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata"
    )
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['order_id']),
            models.Index(fields=['trading_symbol']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
    
    def __str__(self):
        return f"{self.order_id or 'PENDING'} - {self.trading_symbol} - {self.transaction_type}"
    
    @property
    def is_complete(self):
        return self.status == self.STATUS_COMPLETE
    
    @property
    def is_pending(self):
        return self.status in [self.STATUS_PENDING, self.STATUS_OPEN]
    
    @property
    def is_cancellable(self):
        return self.status in [self.STATUS_PENDING, self.STATUS_OPEN, self.STATUS_AMO]
    
    @property
    def is_modifiable(self):
        return self.status in [self.STATUS_PENDING, self.STATUS_OPEN, self.STATUS_AMO]
    
    def update_status(self, new_status, message=None):
        """Update order status with message."""
        self.status = new_status
        if message:
            self.status_message = message
        self.save(update_fields=['status', 'status_message', 'updated_at'])


class Position(models.Model):
    """Model for open positions."""
    
    # Position Types
    POSITION_LONG = 'LONG'
    POSITION_SHORT = 'SHORT'
    POSITION_CHOICES = [
        (POSITION_LONG, 'Long'),
        (POSITION_SHORT, 'Short'),
    ]
    
    # Exchange (same as Order)
    EXCHANGE_CHOICES = Order.EXCHANGE_CHOICES
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='positions'
    )
    
    # Scrip Details
    exchange = models.CharField(max_length=10, choices=EXCHANGE_CHOICES)
    trading_symbol = models.CharField(max_length=50)
    symbol_token = models.CharField(max_length=50)
    instrument_type = models.CharField(max_length=20, blank=True, null=True)
    
    # Position Details
    position_type = models.CharField(
        max_length=10,
        choices=POSITION_CHOICES
    )
    product_type = models.CharField(
        max_length=15,
        choices=Order.PRODUCT_CHOICES
    )
    
    # Quantity
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    buy_quantity = models.IntegerField(default=0)
    sell_quantity = models.IntegerField(default=0)
    
    # Prices
    average_price = models.DecimalField(max_digits=15, decimal_places=2)
    buy_average = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    sell_average = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    
    # Current Market Data
    last_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    close_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Previous close price"
    )
    
    # P&L
    realized_pnl = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    unrealized_pnl = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    
    # Risk Management
    stop_loss = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True
    )
    target = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # Status
    is_open = models.BooleanField(default=True)
    
    # Related Orders
    entry_order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        related_name='entry_position',
        blank=True,
        null=True
    )
    exit_order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        related_name='exit_position',
        blank=True,
        null=True
    )
    
    # Timestamps
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'positions'
        ordering = ['-opened_at']
        indexes = [
            models.Index(fields=['user', 'is_open']),
            models.Index(fields=['trading_symbol']),
            models.Index(fields=['exchange']),
        ]
        verbose_name = 'Position'
        verbose_name_plural = 'Positions'
    
    def __str__(self):
        return f"{self.trading_symbol} - {self.position_type} - {self.quantity}"
    
    @property
    def total_pnl(self):
        return self.realized_pnl + self.unrealized_pnl
    
    @property
    def pnl_percentage(self):
        if self.average_price and self.average_price > 0:
            return (self.unrealized_pnl / (self.average_price * self.quantity)) * 100
        return 0
    
    @property
    def current_value(self):
        return self.last_price * self.quantity
    
    @property
    def invested_value(self):
        return self.average_price * self.quantity
    
    def update_unrealized_pnl(self):
        """Calculate unrealized P&L based on current price."""
        if self.position_type == self.POSITION_LONG:
            self.unrealized_pnl = (self.last_price - self.average_price) * self.quantity
        else:
            self.unrealized_pnl = (self.average_price - self.last_price) * self.quantity
        self.save(update_fields=['unrealized_pnl', 'updated_at'])


class Trade(models.Model):
    """Model for executed trades."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trades'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='trades'
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        related_name='trades',
        blank=True,
        null=True
    )
    
    # Trade Details
    trade_id = models.CharField(max_length=50, unique=True)
    exchange = models.CharField(max_length=10, choices=Order.EXCHANGE_CHOICES)
    trading_symbol = models.CharField(max_length=50)
    symbol_token = models.CharField(max_length=50)
    
    # Execution Details
    transaction_type = models.CharField(max_length=10, choices=Order.TRANSACTION_CHOICES)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Charges
    brokerage = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stt = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    exchange_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    gst = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    stamp_duty = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sebi_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # P&L
    realized_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Timestamps
    executed_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'trades'
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['user', 'executed_at']),
            models.Index(fields=['trading_symbol']),
            models.Index(fields=['exchange']),
        ]
        verbose_name = 'Trade'
        verbose_name_plural = 'Trades'
    
    def __str__(self):
        return f"{self.trade_id} - {self.trading_symbol} - {self.quantity}@{self.price}"
    
    @property
    def total_charges(self):
        return (
            self.brokerage + self.stt + self.exchange_charges +
            self.gst + self.stamp_duty + self.sebi_charges
        )
    
    @property
    def net_value(self):
        return (self.price * self.quantity) - self.total_charges


class OrderBook(models.Model):
    """Model to cache order book data from Kotak."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='order_book_entries'
    )
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='order_book',
        blank=True,
        null=True
    )
    
    # Order Book Data
    external_order_id = models.CharField(max_length=50)
    exchange = models.CharField(max_length=10, choices=Order.EXCHANGE_CHOICES)
    trading_symbol = models.CharField(max_length=50)
    transaction_type = models.CharField(max_length=10, choices=Order.TRANSACTION_CHOICES)
    order_type = models.CharField(max_length=10, choices=Order.ORDER_TYPE_CHOICES)
    product_type = models.CharField(max_length=15, choices=Order.PRODUCT_CHOICES)
    
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=15, decimal_places=2)
    trigger_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    status_message = models.TextField(blank=True, null=True)
    
    filled_quantity = models.IntegerField(default=0)
    pending_quantity = models.IntegerField(default=0)
    cancelled_quantity = models.IntegerField(default=0)
    average_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Cache metadata
    last_synced_at = models.DateTimeField(auto_now=True)
    raw_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'order_book'
        ordering = ['-last_synced_at']
        verbose_name = 'Order Book Entry'
        verbose_name_plural = 'Order Book Entries'
    
    def __str__(self):
        return f"{self.order_id} - {self.trading_symbol}"


class TradeBook(models.Model):
    """Model to cache trade book data from Kotak."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trade_book_entries'
    )
    trade = models.OneToOneField(
        Trade,
        on_delete=models.CASCADE,
        related_name='trade_book',
        blank=True,
        null=True
    )
    
    # Trade Book Data
    external_trade_id = models.CharField(max_length=50)
    external_order_id = models.CharField(max_length=50)
    exchange = models.CharField(max_length=10, choices=Order.EXCHANGE_CHOICES)
    trading_symbol = models.CharField(max_length=50)
    transaction_type = models.CharField(max_length=10, choices=Order.TRANSACTION_CHOICES)
    
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Cache metadata
    trade_date = models.DateField()
    last_synced_at = models.DateTimeField(auto_now=True)
    raw_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'trade_book'
        ordering = ['-trade_date', '-last_synced_at']
        verbose_name = 'Trade Book Entry'
        verbose_name_plural = 'Trade Book Entries'
    
    def __str__(self):
        return f"{self.trade_id} - {self.trading_symbol} - {self.quantity}@{self.price}"
