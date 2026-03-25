"""
Celery Tasks for Trading App
"""
import logging
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone

from .models import Order, Position, Trade, OrderBook, TradeBook
from accounts.services.kotak_auth import KotakAuthService
from .services.kotak_trading import KotakTradingService

logger = logging.getLogger(__name__)


@shared_task
def sync_order_book():
    """
    Sync order book from Kotak API.
    Run every 10 seconds during market hours.
    """
    # Get all users with active Kotak sessions
    from accounts.models import UserProfile
    
    profiles = UserProfile.objects.filter(session_status='active')
    
    for profile in profiles:
        try:
            trading_service = KotakTradingService(profile)
            result = trading_service.get_order_book()
            
            if result.get('success'):
                orders_data = result['data']
                
                # Update local order book cache
                for order_data in orders_data:
                    OrderBook.objects.update_or_create(
                        user=profile.user,
                        order_id=order_data.get('order_id'),
                        defaults={
                            'exchange': order_data.get('exchange'),
                            'trading_symbol': order_data.get('trading_symbol'),
                            'transaction_type': order_data.get('transaction_type'),
                            'order_type': order_data.get('order_type'),
                            'product_type': order_data.get('product_type'),
                            'quantity': order_data.get('quantity'),
                            'price': order_data.get('price'),
                            'trigger_price': order_data.get('trigger_price', 0),
                            'status': order_data.get('status'),
                            'status_message': order_data.get('status_message'),
                            'filled_quantity': order_data.get('filled_quantity', 0),
                            'pending_quantity': order_data.get('pending_quantity', 0),
                            'average_price': order_data.get('average_price', 0),
                            'raw_data': order_data
                        }
                    )
                    
                    # Update corresponding Order model
                    try:
                        order = Order.objects.get(
                            user=profile.user,
                            order_id=order_data.get('order_id')
                        )
                        order.status = order_data.get('status')
                        order.filled_quantity = order_data.get('filled_quantity', 0)
                        order.pending_quantity = order_data.get('pending_quantity', 0)
                        order.average_price = order_data.get('average_price', 0)
                        order.save()
                        
                        # Send WebSocket update
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.group_send)(
                            f"user_orders_{profile.user.id}",
                            {
                                'type': 'order_update',
                                'order_id': order.order_id,
                                'status': order.status,
                                'data': {
                                    'filled_quantity': order.filled_quantity,
                                    'pending_quantity': order.pending_quantity,
                                    'average_price': str(order.average_price),
                                }
                            }
                        )
                    except Order.DoesNotExist:
                        pass
                        
        except Exception as e:
            logger.error(f"Error syncing order book for {profile.user.username}: {e}")


@shared_task
def sync_trade_book():
    """
    Sync trade book from Kotak API.
    Run every minute during market hours.
    """
    from accounts.models import UserProfile
    
    profiles = UserProfile.objects.filter(session_status='active')
    
    for profile in profiles:
        try:
            trading_service = KotakTradingService(profile)
            result = trading_service.get_trade_book()
            
            if result.get('success'):
                trades_data = result['data']
                
                for trade_data in trades_data:
                    TradeBook.objects.update_or_create(
                        user=profile.user,
                        trade_id=trade_data.get('trade_id'),
                        defaults={
                            'order_id': trade_data.get('order_id'),
                            'exchange': trade_data.get('exchange'),
                            'trading_symbol': trade_data.get('trading_symbol'),
                            'transaction_type': trade_data.get('transaction_type'),
                            'quantity': trade_data.get('quantity'),
                            'price': trade_data.get('price'),
                            'trade_date': trade_data.get('trade_date'),
                            'raw_data': trade_data
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Error syncing trade book for {profile.user.username}: {e}")


@shared_task
def sync_positions():
    """
    Sync positions from Kotak API.
    Run every 30 seconds during market hours.
    """
    from accounts.models import UserProfile
    
    profiles = UserProfile.objects.filter(session_status='active')
    
    for profile in profiles:
        try:
            trading_service = KotakTradingService(profile)
            result = trading_service.get_positions()
            
            if result.get('success'):
                positions_data = result['data']
                
                for pos_data in positions_data:
                    Position.objects.update_or_create(
                        user=profile.user,
                        trading_symbol=pos_data.get('trading_symbol'),
                        exchange=pos_data.get('exchange'),
                        is_open=True,
                        defaults={
                            'symbol_token': pos_data.get('symbol_token'),
                            'position_type': 'LONG' if pos_data.get('net_qty', 0) > 0 else 'SHORT',
                            'product_type': pos_data.get('product_type', 'INTRADAY'),
                            'quantity': abs(pos_data.get('net_qty', 0)),
                            'average_price': pos_data.get('avg_price', 0),
                            'last_price': pos_data.get('ltp', 0),
                            'unrealized_pnl': pos_data.get('unrealized', 0),
                            'realized_pnl': pos_data.get('realized', 0),
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Error syncing positions for {profile.user.username}: {e}")


@shared_task
def calculate_pnl():
    """
    Calculate P&L for all open positions.
    Run every minute.
    """
    positions = Position.objects.filter(is_open=True)
    
    for position in positions:
        try:
            position.update_unrealized_pnl()
        except Exception as e:
            logger.error(f"Error calculating P&L for position {position.id}: {e}")


@shared_task
def process_completed_orders():
    """
    Process completed orders and create trades.
    Run every minute.
    """
    completed_orders = Order.objects.filter(
        status='COMPLETE',
        trades__isnull=True
    )
    
    for order in completed_orders:
        try:
            # Create trade record
            Trade.objects.create(
                user=order.user,
                order=order,
                position=order.entry_position,
                trade_id=f"TRADE_{order.order_id}",
                exchange=order.exchange,
                trading_symbol=order.trading_symbol,
                symbol_token=order.symbol_token,
                transaction_type=order.transaction_type,
                quantity=order.filled_quantity,
                price=order.average_price,
                executed_at=order.executed_at or timezone.now()
            )
            
            logger.info(f"Created trade for order {order.order_id}")
            
        except Exception as e:
            logger.error(f"Error processing completed order {order.order_id}: {e}")


@shared_task
def update_funds():
    """
    Update funds/margin for all active users.
    Run every 5 minutes.
    """
    from accounts.models import UserProfile
    
    profiles = UserProfile.objects.filter(session_status='active')
    
    for profile in profiles:
        try:
            trading_service = KotakTradingService(profile)
            trading_service.get_funds()
            
        except Exception as e:
            logger.error(f"Error updating funds for {profile.user.username}: {e}")
