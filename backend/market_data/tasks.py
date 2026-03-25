"""
Celery Tasks for Market Data App
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from .models import Scrip, Quote, MarketDepth, ScripCache

logger = logging.getLogger(__name__)


@shared_task
def sync_scrip_master(exchange='NSE'):
    """
    Sync scrip master data from Kotak API.
    Run daily at 6:00 AM.
    """
    from accounts.models import UserProfile
    from accounts.services.kotak_auth import KotakAuthService
    from neo_api_client import NeoAPI
    
    logger.info(f"Starting scrip master sync for {exchange}")
    
    # Get any active profile for API access
    profile = UserProfile.objects.filter(session_status='active').first()
    
    if not profile:
        logger.warning("No active Kotak session found for scrip sync")
        return {'success': False, 'message': 'No active session'}
    
    try:
        # Update cache status
        cache_status, created = ScripCache.objects.get_or_create(exchange=exchange)
        cache_status.is_syncing = True
        cache_status.save()
        
        # Initialize client
        auth_service = KotakAuthService(profile)
        client = auth_service.get_client()
        
        # Fetch master data
        response = client.scrip_master(exchange=exchange)
        
        if response and 'data' in response:
            scrips_data = response['data']
            count = 0
            
            for scrip_data in scrips_data:
                try:
                    Scrip.objects.update_or_create(
                        symbol_token=scrip_data.get('token'),
                        exchange=exchange,
                        defaults={
                            'trading_symbol': scrip_data.get('symbol'),
                            'symbol_name': scrip_data.get('name', scrip_data.get('symbol')),
                            'instrument_type': scrip_data.get('instrument_type', 'EQ'),
                            'company_name': scrip_data.get('company_name'),
                            'lot_size': scrip_data.get('lot_size', 1),
                            'tick_size': scrip_data.get('tick_size', 0.05),
                            'expiry_date': scrip_data.get('expiry'),
                            'strike_price': scrip_data.get('strike_price'),
                            'is_fno': scrip_data.get('is_fno', False),
                            'is_active': True,
                        }
                    )
                    count += 1
                except Exception as e:
                    logger.error(f"Error saving scrip: {e}")
                    continue
            
            # Update cache status
            cache_status.last_synced = timezone.now()
            cache_status.record_count = count
            cache_status.is_syncing = False
            cache_status.save()
            
            logger.info(f"Synced {count} scrips for {exchange}")
            return {
                'success': True,
                'count': count,
                'exchange': exchange
            }
        else:
            cache_status.is_syncing = False
            cache_status.save()
            logger.error(f"Failed to sync scrip master: {response}")
            return {
                'success': False,
                'message': 'API request failed'
            }
            
    except Exception as e:
        logger.error(f"Error syncing scrip master: {e}")
        return {
            'success': False,
            'message': str(e)
        }


@shared_task
def update_quotes():
    """
    Update quotes for frequently traded scrips.
    Run every 5 seconds during market hours.
    """
    from django.core.cache import cache
    from accounts.models import UserProfile
    from accounts.services.kotak_auth import KotakAuthService
    
    # Get active profile
    profile = UserProfile.objects.filter(session_status='active').first()
    
    if not profile:
        return
    
    try:
        # Get popular scrips (those in watchlists or with open positions)
        from trading.models import Position
        
        # Get symbols from open positions
        position_symbols = Position.objects.filter(
            is_open=True
        ).values('symbol_token', 'exchange').distinct()[:50]
        
        auth_service = KotakAuthService(profile)
        client = auth_service.get_client()
        
        for symbol_data in position_symbols:
            try:
                response = client.quotes(
                    symbol_token=symbol_data['symbol_token'],
                    exchange=symbol_data['exchange']
                )
                
                if response and 'data' in response:
                    quote_data = response['data']
                    
                    # Update or create quote
                    scrip = Scrip.objects.get(
                        symbol_token=symbol_data['symbol_token'],
                        exchange=symbol_data['exchange']
                    )
                    
                    Quote.objects.update_or_create(
                        scrip=scrip,
                        defaults={
                            'last_price': quote_data.get('last_price', 0),
                            'change': quote_data.get('change', 0),
                            'change_percentage': quote_data.get('change_percentage', 0),
                            'open_price': quote_data.get('open', 0),
                            'high_price': quote_data.get('high', 0),
                            'low_price': quote_data.get('low', 0),
                            'close_price': quote_data.get('close', 0),
                            'volume': quote_data.get('volume', 0),
                            'bid_price': quote_data.get('bid_price', 0),
                            'ask_price': quote_data.get('ask_price', 0),
                            'bid_quantity': quote_data.get('bid_quantity', 0),
                            'ask_quantity': quote_data.get('ask_quantity', 0),
                        }
                    )
                    
                    # Cache the quote
                    cache_key = f"quote_{symbol_data['exchange']}_{symbol_data['symbol_token']}"
                    cache.set(cache_key, quote_data, 5)
                    
            except Exception as e:
                logger.error(f"Error updating quote: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error in update quotes task: {e}")


@shared_task
def update_market_depth():
    """
    Update market depth for active scrips.
    Run every 5 seconds.
    """
    from accounts.models import UserProfile
    from accounts.services.kotak_auth import KotakAuthService
    
    profile = UserProfile.objects.filter(session_status='active').first()
    
    if not profile:
        return
    
    try:
        # Get scrips with recent quotes
        recent_quotes = Quote.objects.filter(
            last_updated__gte=timezone.now() - timedelta(minutes=5)
        ).select_related('scrip')[:20]
        
        auth_service = KotakAuthService(profile)
        client = auth_service.get_client()
        
        for quote in recent_quotes:
            try:
                response = client.market_depth(
                    symbol_token=quote.scrip.symbol_token,
                    exchange=quote.scrip.exchange
                )
                
                if response and 'data' in response:
                    depth_data = response['data']
                    
                    # Update market depth
                    MarketDepth.objects.update_or_create(
                        quote=quote,
                        defaults={
                            'buy_quantity_1': depth_data.get('buy_quantity_1', 0),
                            'buy_price_1': depth_data.get('buy_price_1', 0),
                            'buy_orders_1': depth_data.get('buy_orders_1', 0),
                            'sell_quantity_1': depth_data.get('sell_quantity_1', 0),
                            'sell_price_1': depth_data.get('sell_price_1', 0),
                            'sell_orders_1': depth_data.get('sell_orders_1', 0),
                            # ... add more levels as needed
                        }
                    )
                    
            except Exception as e:
                logger.error(f"Error updating market depth: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error in update market depth task: {e}")


@shared_task
def cleanup_old_quotes():
    """
    Clean up old quote data.
    Run daily.
    """
    cutoff_date = timezone.now() - timedelta(days=7)
    
    old_quotes = Quote.objects.filter(last_updated__lt=cutoff_date)
    count = old_quotes.count()
    old_quotes.delete()
    
    logger.info(f"Deleted {count} old quotes")
    return {'deleted': count}


@shared_task
def update_index_quotes():
    """
    Update major index quotes (NIFTY, BANKNIFTY, SENSEX).
    Run every 10 seconds.
    """
    from accounts.models import UserProfile
    from accounts.services.kotak_auth import KotakAuthService
    
    profile = UserProfile.objects.filter(session_status='active').first()
    
    if not profile:
        return
    
    indices = [
        {'name': 'NIFTY 50', 'token': '99926000', 'exchange': 'NSE'},
        {'name': 'NIFTY BANK', 'token': '99926009', 'exchange': 'NSE'},
        {'name': 'SENSEX', 'token': '99919000', 'exchange': 'BSE'},
    ]
    
    try:
        auth_service = KotakAuthService(profile)
        client = auth_service.get_client()
        
        for index in indices:
            try:
                response = client.quotes(
                    symbol_token=index['token'],
                    exchange=index['exchange']
                )
                
                if response and 'data' in response:
                    # Cache index quote
                    from django.core.cache import cache
                    cache_key = f"index_{index['name'].replace(' ', '_')}"
                    cache.set(cache_key, response['data'], 10)
                    
            except Exception as e:
                logger.error(f"Error updating {index['name']}: {e}")
                
    except Exception as e:
        logger.error(f"Error in update index quotes task: {e}")
