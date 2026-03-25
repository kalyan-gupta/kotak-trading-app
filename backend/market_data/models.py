"""
Market Data Models - Scrip Master and Quotes
"""
from django.db import models
from django.core.cache import cache


class Scrip(models.Model):
    """Model for scrip/symbol master data."""
    
    # Instrument Types
    INSTRUMENT_EQ = 'EQ'
    INSTRUMENT_BE = 'BE'
    INSTRUMENT_BZ = 'BZ'
    INSTRUMENT_FUT = 'FUT'
    INSTRUMENT_CE = 'CE'
    INSTRUMENT_PE = 'PE'
    INSTRUMENT_CHOICES = [
        (INSTRUMENT_EQ, 'Equity'),
        (INSTRUMENT_BE, 'Equity (BE)'),
        (INSTRUMENT_BZ, 'Equity (BZ)'),
        (INSTRUMENT_FUT, 'Futures'),
        (INSTRUMENT_CE, 'Call Option'),
        (INSTRUMENT_PE, 'Put Option'),
    ]
    
    # Exchanges
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
    symbol_token = models.CharField(
        max_length=50,
        help_text="Unique token for the scrip"
    )
    exchange = models.CharField(
        max_length=10,
        choices=EXCHANGE_CHOICES
    )
    
    # Symbol Details
    trading_symbol = models.CharField(max_length=50)
    symbol_name = models.CharField(max_length=200)
    instrument_type = models.CharField(
        max_length=10,
        choices=INSTRUMENT_CHOICES
    )
    
    # Company Details
    company_name = models.CharField(max_length=500, blank=True, null=True)
    industry = models.CharField(max_length=200, blank=True, null=True)
    sector = models.CharField(max_length=200, blank=True, null=True)
    
    # ISIN
    isin = models.CharField(max_length=20, blank=True, null=True)
    
    # F&O Details
    expiry_date = models.DateField(blank=True, null=True)
    strike_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True
    )
    lot_size = models.IntegerField(default=1)
    tick_size = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0.05
    )
    
    # Price Bands
    price_high = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True
    )
    price_low = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # Circuit Limits
    upper_circuit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True
    )
    lower_circuit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_fno = models.BooleanField(default=False)
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'scrips'
        ordering = ['trading_symbol']
        unique_together = ['symbol_token', 'exchange']
        indexes = [
            models.Index(fields=['trading_symbol']),
            models.Index(fields=['symbol_name']),
            models.Index(fields=['exchange']),
            models.Index(fields=['instrument_type']),
            models.Index(fields=['is_fno']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = 'Scrip'
        verbose_name_plural = 'Scrips'
    
    def __str__(self):
        return f"{self.trading_symbol} ({self.exchange})"
    
    @property
    def display_name(self):
        """Get display name for the scrip."""
        if self.company_name:
            return f"{self.company_name} ({self.trading_symbol})"
        return self.trading_symbol
    
    @property
    def is_option(self):
        return self.instrument_type in [self.INSTRUMENT_CE, self.INSTRUMENT_PE]
    
    @property
    def is_future(self):
        return self.instrument_type == self.INSTRUMENT_FUT


class Quote(models.Model):
    """Model for real-time quotes."""
    
    scrip = models.OneToOneField(
        Scrip,
        on_delete=models.CASCADE,
        related_name='quote'
    )
    
    # Price Data
    last_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    change = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    change_percentage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    # OHLC
    open_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    high_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    low_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    close_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    
    # Volume
    volume = models.BigIntegerField(default=0)
    total_buy_quantity = models.BigIntegerField(default=0)
    total_sell_quantity = models.BigIntegerField(default=0)
    
    # Bid/Ask
    bid_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    bid_quantity = models.BigIntegerField(default=0)
    ask_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    ask_quantity = models.BigIntegerField(default=0)
    
    # 52 Week Data
    week_52_high = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    week_52_low = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    
    # Additional Data
    average_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00
    )
    oi = models.BigIntegerField(default=0, help_text="Open Interest")
    oi_change = models.BigIntegerField(default=0)
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quotes'
        ordering = ['-last_updated']
        verbose_name = 'Quote'
        verbose_name_plural = 'Quotes'
    
    def __str__(self):
        return f"{self.scrip.trading_symbol} - ₹{self.last_price}"
    
    @property
    def spread(self):
        """Calculate bid-ask spread."""
        if self.ask_price > 0:
            return self.ask_price - self.bid_price
        return 0
    
    @property
    def spread_percentage(self):
        """Calculate spread percentage."""
        if self.last_price > 0:
            return (self.spread / self.last_price) * 100
        return 0


class MarketDepth(models.Model):
    """Model for market depth (5 levels)."""
    
    quote = models.OneToOneField(
        Quote,
        on_delete=models.CASCADE,
        related_name='depth'
    )
    
    # Buy Levels
    buy_quantity_1 = models.BigIntegerField(default=0)
    buy_price_1 = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    buy_orders_1 = models.IntegerField(default=0)
    
    buy_quantity_2 = models.BigIntegerField(default=0)
    buy_price_2 = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    buy_orders_2 = models.IntegerField(default=0)
    
    buy_quantity_3 = models.BigIntegerField(default=0)
    buy_price_3 = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    buy_orders_3 = models.IntegerField(default=0)
    
    buy_quantity_4 = models.BigIntegerField(default=0)
    buy_price_4 = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    buy_orders_4 = models.IntegerField(default=0)
    
    buy_quantity_5 = models.BigIntegerField(default=0)
    buy_price_5 = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    buy_orders_5 = models.IntegerField(default=0)
    
    # Sell Levels
    sell_quantity_1 = models.BigIntegerField(default=0)
    sell_price_1 = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    sell_orders_1 = models.IntegerField(default=0)
    
    sell_quantity_2 = models.BigIntegerField(default=0)
    sell_price_2 = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    sell_orders_2 = models.IntegerField(default=0)
    
    sell_quantity_3 = models.BigIntegerField(default=0)
    sell_price_3 = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    sell_orders_3 = models.IntegerField(default=0)
    
    sell_quantity_4 = models.BigIntegerField(default=0)
    sell_price_4 = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    sell_orders_4 = models.IntegerField(default=0)
    
    sell_quantity_5 = models.BigIntegerField(default=0)
    sell_price_5 = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    sell_orders_5 = models.IntegerField(default=0)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'market_depth'
        verbose_name = 'Market Depth'
        verbose_name_plural = 'Market Depth'
    
    def get_buy_levels(self):
        """Get buy levels as list."""
        return [
            {'quantity': self.buy_quantity_1, 'price': self.buy_price_1, 'orders': self.buy_orders_1},
            {'quantity': self.buy_quantity_2, 'price': self.buy_price_2, 'orders': self.buy_orders_2},
            {'quantity': self.buy_quantity_3, 'price': self.buy_price_3, 'orders': self.buy_orders_3},
            {'quantity': self.buy_quantity_4, 'price': self.buy_price_4, 'orders': self.buy_orders_4},
            {'quantity': self.buy_quantity_5, 'price': self.buy_price_5, 'orders': self.buy_orders_5},
        ]
    
    def get_sell_levels(self):
        """Get sell levels as list."""
        return [
            {'quantity': self.sell_quantity_1, 'price': self.sell_price_1, 'orders': self.sell_orders_1},
            {'quantity': self.sell_quantity_2, 'price': self.sell_price_2, 'orders': self.sell_orders_2},
            {'quantity': self.sell_quantity_3, 'price': self.sell_price_3, 'orders': self.sell_orders_3},
            {'quantity': self.sell_quantity_4, 'price': self.sell_price_4, 'orders': self.sell_orders_4},
            {'quantity': self.sell_quantity_5, 'price': self.sell_price_5, 'orders': self.sell_orders_5},
        ]


class Watchlist(models.Model):
    """Model for user watchlists."""
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='watchlists'
    )
    name = models.CharField(max_length=100)
    scrips = models.ManyToManyField(Scrip, related_name='watchlists')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'watchlists'
        ordering = ['-created_at']
        unique_together = ['user', 'name']
        verbose_name = 'Watchlist'
        verbose_name_plural = 'Watchlists'
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"


class ScripCache(models.Model):
    """Model to track scrip master data cache status."""
    
    exchange = models.CharField(max_length=10, choices=Scrip.EXCHANGE_CHOICES, unique=True)
    last_synced = models.DateTimeField(blank=True, null=True)
    record_count = models.IntegerField(default=0)
    is_syncing = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'scrip_cache'
        verbose_name = 'Scrip Cache'
        verbose_name_plural = 'Scrip Caches'
    
    def __str__(self):
        return f"{self.exchange} - {self.record_count} records"
