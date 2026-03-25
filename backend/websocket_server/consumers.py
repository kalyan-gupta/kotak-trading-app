"""
WebSocket Consumers for Real-time Market Data
"""
import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache

logger = logging.getLogger(__name__)


class MarketDataConsumer(AsyncWebsocketConsumer):
    """Consumer for real-time market data WebSocket."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscribed_symbols = set()
        self.ping_task = None
        self.user = None
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope.get('user')
        
        if not self.user or not self.user.is_authenticated:
            logger.warning("Unauthorized WebSocket connection attempt")
            await self.close(code=4001)
            return
        
        await self.accept()
        logger.info(f"WebSocket connected for user: {self.user.username}")
        
        # Start ping task
        self.ping_task = asyncio.create_task(self.send_ping())
        
        # Send connection success message
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'status': 'connected',
            'message': 'WebSocket connected successfully'
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Cancel ping task
        if self.ping_task:
            self.ping_task.cancel()
        
        # Unsubscribe from all symbols
        for symbol in list(self.subscribed_symbols):
            await self.unsubscribe_symbol(symbol)
        
        logger.info(f"WebSocket disconnected for user: {self.user.username if self.user else 'unknown'}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'subscribe':
                await self.handle_subscribe(data)
            elif message_type == 'unsubscribe':
                await self.handle_unsubscribe(data)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            elif message_type == 'get_quote':
                await self.handle_get_quote(data)
            elif message_type == 'subscribe_depth':
                await self.handle_subscribe_depth(data)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def handle_subscribe(self, data):
        """Handle symbol subscription."""
        symbols = data.get('symbols', [])
        
        if not symbols:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'No symbols provided'
            }))
            return
        
        for symbol_data in symbols:
            symbol_token = symbol_data.get('symbol_token')
            exchange = symbol_data.get('exchange', 'NSE')
            
            if not symbol_token:
                continue
            
            symbol_key = f"{exchange}:{symbol_token}"
            
            if symbol_key not in self.subscribed_symbols:
                self.subscribed_symbols.add(symbol_key)
                
                # Add to channel group for this symbol
                await self.channel_layer.group_add(
                    f"market_data_{symbol_key}",
                    self.channel_name
                )
                
                # Send initial quote
                quote = await self.get_quote_from_cache(symbol_token, exchange)
                if quote:
                    await self.send(text_data=json.dumps({
                        'type': 'quote',
                        'symbol': symbol_key,
                        'data': quote
                    }))
        
        await self.send(text_data=json.dumps({
            'type': 'subscribed',
            'symbols': list(self.subscribed_symbols)
        }))
    
    async def handle_unsubscribe(self, data):
        """Handle symbol unsubscription."""
        symbols = data.get('symbols', [])
        
        for symbol_data in symbols:
            symbol_token = symbol_data.get('symbol_token')
            exchange = symbol_data.get('exchange', 'NSE')
            symbol_key = f"{exchange}:{symbol_token}"
            
            await self.unsubscribe_symbol(symbol_key)
        
        await self.send(text_data=json.dumps({
            'type': 'unsubscribed',
            'symbols': list(self.subscribed_symbols)
        }))
    
    async def unsubscribe_symbol(self, symbol_key):
        """Unsubscribe from a symbol."""
        if symbol_key in self.subscribed_symbols:
            self.subscribed_symbols.discard(symbol_key)
            await self.channel_layer.group_discard(
                f"market_data_{symbol_key}",
                self.channel_name
            )
    
    async def handle_get_quote(self, data):
        """Handle get quote request."""
        symbol_token = data.get('symbol_token')
        exchange = data.get('exchange', 'NSE')
        
        if not symbol_token:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Symbol token is required'
            }))
            return
        
        quote = await self.get_quote_from_cache(symbol_token, exchange)
        
        if quote:
            await self.send(text_data=json.dumps({
                'type': 'quote',
                'symbol': f"{exchange}:{symbol_token}",
                'data': quote
            }))
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Quote not found'
            }))
    
    async def handle_subscribe_depth(self, data):
        """Handle market depth subscription."""
        symbol_token = data.get('symbol_token')
        exchange = data.get('exchange', 'NSE')
        
        if not symbol_token:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Symbol token is required'
            }))
            return
        
        symbol_key = f"{exchange}:{symbol_token}"
        
        # Add to depth channel group
        await self.channel_layer.group_add(
            f"market_depth_{symbol_key}",
            self.channel_name
        )
        
        # Send initial depth
        depth = await self.get_depth_from_cache(symbol_token, exchange)
        if depth:
            await self.send(text_data=json.dumps({
                'type': 'depth',
                'symbol': symbol_key,
                'data': depth
            }))
        
        await self.send(text_data=json.dumps({
            'type': 'depth_subscribed',
            'symbol': symbol_key
        }))
    
    async def market_data_update(self, event):
        """Handle market data update from channel layer."""
        await self.send(text_data=json.dumps({
            'type': 'quote_update',
            'symbol': event.get('symbol'),
            'data': event.get('data')
        }))
    
    async def market_depth_update(self, event):
        """Handle market depth update from channel layer."""
        await self.send(text_data=json.dumps({
            'type': 'depth_update',
            'symbol': event.get('symbol'),
            'data': event.get('data')
        }))
    
    async def order_update(self, event):
        """Handle order status update."""
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'order_id': event.get('order_id'),
            'data': event.get('data')
        }))
    
    async def position_update(self, event):
        """Handle position update."""
        await self.send(text_data=json.dumps({
            'type': 'position_update',
            'data': event.get('data')
        }))
    
    async def send_ping(self):
        """Send periodic ping to keep connection alive."""
        try:
            while True:
                await asyncio.sleep(30)  # Ping every 30 seconds
                await self.send(text_data=json.dumps({
                    'type': 'ping',
                    'timestamp': asyncio.get_event_loop().time()
                }))
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Ping task error: {e}")
    
    @database_sync_to_async
    def get_quote_from_cache(self, symbol_token, exchange):
        """Get quote from cache or database."""
        try:
            cache_key = f"quote_{exchange}_{symbol_token}"
            quote = cache.get(cache_key)
            
            if quote:
                return quote
            
            # Try to get from database
            from market_data.models import Scrip, Quote
            scrip = Scrip.objects.get(symbol_token=symbol_token, exchange=exchange)
            quote_obj = Quote.objects.get(scrip=scrip)
            
            return {
                'last_price': str(quote_obj.last_price),
                'change': str(quote_obj.change),
                'change_percentage': str(quote_obj.change_percentage),
                'volume': quote_obj.volume,
                'open': str(quote_obj.open_price),
                'high': str(quote_obj.high_price),
                'low': str(quote_obj.low_price),
                'close': str(quote_obj.close_price),
                'bid_price': str(quote_obj.bid_price),
                'ask_price': str(quote_obj.ask_price),
                'timestamp': quote_obj.last_updated.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting quote: {e}")
            return None
    
    @database_sync_to_async
    def get_depth_from_cache(self, symbol_token, exchange):
        """Get market depth from cache or database."""
        try:
            from market_data.models import Scrip, MarketDepth
            scrip = Scrip.objects.get(symbol_token=symbol_token, exchange=exchange)
            depth = MarketDepth.objects.get(quote__scrip=scrip)
            
            return {
                'buy': depth.get_buy_levels(),
                'sell': depth.get_sell_levels()
            }
        except Exception as e:
            logger.error(f"Error getting depth: {e}")
            return None


class OrderUpdatesConsumer(AsyncWebsocketConsumer):
    """Consumer for order status updates."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope.get('user')
        
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        # Join user-specific group
        await self.channel_layer.group_add(
            f"user_orders_{self.user.id}",
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Order updates WebSocket connected for user: {self.user.username}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self.user and self.user.is_authenticated:
            await self.channel_layer.group_discard(
                f"user_orders_{self.user.id}",
                self.channel_name
            )
        
        logger.info(f"Order updates WebSocket disconnected for user: {self.user.username if self.user else 'unknown'}")
    
    async def receive(self, text_data):
        """Handle incoming messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
                
        except json.JSONDecodeError:
            pass
    
    async def order_update(self, event):
        """Send order update to client."""
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'order_id': event.get('order_id'),
            'status': event.get('status'),
            'message': event.get('message'),
            'data': event.get('data')
        }))
    
    async def trade_update(self, event):
        """Send trade update to client."""
        await self.send(text_data=json.dumps({
            'type': 'trade_update',
            'trade_id': event.get('trade_id'),
            'data': event.get('data')
        }))


class PortfolioUpdatesConsumer(AsyncWebsocketConsumer):
    """Consumer for portfolio updates (positions, P&L)."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope.get('user')
        
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        # Join user-specific group
        await self.channel_layer.group_add(
            f"user_portfolio_{self.user.id}",
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Portfolio updates WebSocket connected for user: {self.user.username}")
        
        # Send initial portfolio data
        await self.send_portfolio_snapshot()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self.user and self.user.is_authenticated:
            await self.channel_layer.group_discard(
                f"user_portfolio_{self.user.id}",
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            elif message_type == 'refresh':
                await self.send_portfolio_snapshot()
                
        except json.JSONDecodeError:
            pass
    
    async def send_portfolio_snapshot(self):
        """Send current portfolio snapshot."""
        portfolio_data = await self.get_portfolio_data()
        await self.send(text_data=json.dumps({
            'type': 'portfolio_snapshot',
            'data': portfolio_data
        }))
    
    async def position_update(self, event):
        """Send position update to client."""
        await self.send(text_data=json.dumps({
            'type': 'position_update',
            'data': event.get('data')
        }))
    
    async def pnl_update(self, event):
        """Send P&L update to client."""
        await self.send(text_data=json.dumps({
            'type': 'pnl_update',
            'data': event.get('data')
        }))
    
    @database_sync_to_async
    def get_portfolio_data(self):
        """Get portfolio data for user."""
        try:
            from trading.models import Position
            from accounts.models import UserProfile
            
            positions = Position.objects.filter(user=self.user, is_open=True)
            profile = UserProfile.objects.get(user=self.user)
            
            return {
                'account_balance': str(profile.account_balance),
                'available_margin': str(profile.available_margin),
                'used_margin': str(profile.used_margin),
                'open_positions_count': positions.count(),
                'positions': [
                    {
                        'id': str(pos.id),
                        'symbol': pos.trading_symbol,
                        'type': pos.position_type,
                        'quantity': pos.quantity,
                        'average_price': str(pos.average_price),
                        'last_price': str(pos.last_price),
                        'unrealized_pnl': str(pos.unrealized_pnl),
                        'total_pnl': str(pos.total_pnl)
                    }
                    for pos in positions
                ]
            }
        except Exception as e:
            logger.error(f"Error getting portfolio data: {e}")
            return {}
