"""
Market Data Views - Scrip Search and Quotes
"""
import logging
from django.db.models import Q
from django.core.cache import cache
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

from .models import Scrip, Quote, MarketDepth, Watchlist, ScripCache
from .serializers import (
    ScripSerializer, ScripSearchSerializer, QuoteSerializer,
    QuoteLiteSerializer, FullQuoteSerializer, WatchlistSerializer,
    WatchlistCreateSerializer, WatchlistAddScripSerializer,
    ScripCacheSerializer, HistoricalDataRequestSerializer,
    HistoricalDataSerializer, IndexQuoteSerializer
)
from accounts.services.kotak_auth import KotakAuthService

logger = logging.getLogger(__name__)


class MarketDataRateThrottle(UserRateThrottle):
    rate = '500/minute'


def get_kotak_client(user):
    """Get authenticated Kotak client."""
    profile = user.profile
    if not profile.is_session_valid():
        raise Exception("Kotak session is not active. Please login.")
    
    auth_service = KotakAuthService(profile)
    return auth_service.get_client()


# Scrip Search Views

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([MarketDataRateThrottle])
def search_scrips_view(request):
    """
    Search scrips by symbol name or trading symbol.
    Supports filtering by exchange and instrument type.
    """
    query = request.query_params.get('q', '').strip()
    exchange = request.query_params.get('exchange')
    instrument_type = request.query_params.get('instrument_type')
    is_fno = request.query_params.get('is_fno')
    limit = int(request.query_params.get('limit', 20))
    
    if not query or len(query) < 2:
        return Response({
            'success': False,
            'message': 'Search query must be at least 2 characters'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Build query
    scrips = Scrip.objects.filter(is_active=True)
    
    # Search by symbol name or trading symbol
    scrips = scrips.filter(
        Q(trading_symbol__icontains=query) |
        Q(symbol_name__icontains=query) |
        Q(company_name__icontains=query)
    )
    
    # Apply filters
    if exchange:
        scrips = scrips.filter(exchange=exchange.upper())
    if instrument_type:
        scrips = scrips.filter(instrument_type=instrument_type.upper())
    if is_fno is not None:
        scrips = scrips.filter(is_fno=is_fno.lower() == 'true')
    
    # Order by relevance (exact matches first)
    scrips = scrips.order_by('trading_symbol')[:limit]
    
    serializer = ScripSearchSerializer(scrips, many=True)
    return Response({
        'success': True,
        'count': len(serializer.data),
        'data': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([MarketDataRateThrottle])
def scrip_detail_view(request, symbol_token):
    """Get detailed information about a scrip."""
    exchange = request.query_params.get('exchange', 'NSE')
    
    try:
        scrip = Scrip.objects.get(symbol_token=symbol_token, exchange=exchange)
        serializer = ScripSerializer(scrip)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except Scrip.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Scrip not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([MarketDataRateThrottle])
def scrip_by_symbol_view(request):
    """Get scrip by trading symbol."""
    trading_symbol = request.query_params.get('symbol')
    exchange = request.query_params.get('exchange', 'NSE')
    
    if not trading_symbol:
        return Response({
            'success': False,
            'message': 'Trading symbol is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        scrip = Scrip.objects.get(
            trading_symbol=trading_symbol.upper(),
            exchange=exchange.upper()
        )
        serializer = ScripSerializer(scrip)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except Scrip.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Scrip not found'
        }, status=status.HTTP_404_NOT_FOUND)


# Quote Views

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([MarketDataRateThrottle])
def get_quote_view(request):
    """Get real-time quote for a scrip."""
    symbol_token = request.query_params.get('symbol_token')
    exchange = request.query_params.get('exchange', 'NSE')
    
    if not symbol_token:
        return Response({
            'success': False,
            'message': 'Symbol token is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Try to get from cache first
        cache_key = f"quote_{exchange}_{symbol_token}"
        cached_quote = cache.get(cache_key)
        
        if cached_quote:
            return Response({
                'success': True,
                'data': cached_quote,
                'source': 'cache'
            })
        
        # Get from database
        try:
            scrip = Scrip.objects.get(symbol_token=symbol_token, exchange=exchange)
            quote = Quote.objects.get(scrip=scrip)
            serializer = FullQuoteSerializer(quote)
            
            # Cache for 5 seconds
            cache.set(cache_key, serializer.data, 5)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'source': 'database'
            })
        except (Scrip.DoesNotExist, Quote.DoesNotExist):
            # Try to fetch from API
            try:
                client = get_kotak_client(request.user)
                response = client.quotes(
                    symbol_token=symbol_token,
                    exchange=exchange
                )
                
                if response and 'data' in response:
                    return Response({
                        'success': True,
                        'data': response['data'],
                        'source': 'api'
                    })
                else:
                    return Response({
                        'success': False,
                        'message': 'Quote not available'
                    }, status=status.HTTP_404_NOT_FOUND)
                    
            except Exception as e:
                logger.error(f"Error fetching quote from API: {e}")
                return Response({
                    'success': False,
                    'message': 'Quote not found'
                }, status=status.HTTP_404_NOT_FOUND)
                
    except Exception as e:
        logger.error(f"Get quote error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([MarketDataRateThrottle])
def get_multiple_quotes_view(request):
    """Get quotes for multiple scrips at once."""
    symbols = request.data.get('symbols', [])
    
    if not symbols or len(symbols) > 50:
        return Response({
            'success': False,
            'message': 'Please provide 1-50 symbols'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    results = []
    for symbol_data in symbols:
        symbol_token = symbol_data.get('symbol_token')
        exchange = symbol_data.get('exchange', 'NSE')
        
        try:
            scrip = Scrip.objects.get(symbol_token=symbol_token, exchange=exchange)
            quote = Quote.objects.get(scrip=scrip)
            results.append({
                'symbol_token': symbol_token,
                'exchange': exchange,
                'data': QuoteLiteSerializer(quote).data
            })
        except (Scrip.DoesNotExist, Quote.DoesNotExist):
            results.append({
                'symbol_token': symbol_token,
                'exchange': exchange,
                'data': None,
                'error': 'Quote not found'
            })
    
    return Response({
        'success': True,
        'count': len(results),
        'data': results
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([MarketDataRateThrottle])
def get_market_depth_view(request):
    """Get market depth for a scrip."""
    symbol_token = request.query_params.get('symbol_token')
    exchange = request.query_params.get('exchange', 'NSE')
    
    if not symbol_token:
        return Response({
            'success': False,
            'message': 'Symbol token is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        scrip = Scrip.objects.get(symbol_token=symbol_token, exchange=exchange)
        depth = MarketDepth.objects.get(quote__scrip=scrip)
        serializer = MarketDepthSerializer(depth)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except (Scrip.DoesNotExist, MarketDepth.DoesNotExist):
        return Response({
            'success': False,
            'message': 'Market depth not available'
        }, status=status.HTTP_404_NOT_FOUND)


# Watchlist Views

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def watchlist_list_view(request):
    """Get user's watchlists."""
    watchlists = Watchlist.objects.filter(user=request.user)
    serializer = WatchlistSerializer(watchlists, many=True)
    return Response({
        'success': True,
        'count': watchlists.count(),
        'data': serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def watchlist_create_view(request):
    """Create a new watchlist."""
    serializer = WatchlistCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # Check if name already exists
    if Watchlist.objects.filter(
        user=request.user,
        name=serializer.validated_data['name']
    ).exists():
        return Response({
            'success': False,
            'message': 'Watchlist with this name already exists'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    watchlist = Watchlist.objects.create(
        user=request.user,
        **serializer.validated_data
    )
    
    return Response({
        'success': True,
        'message': 'Watchlist created successfully',
        'data': WatchlistSerializer(watchlist).data
    }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def watchlist_detail_view(request, watchlist_id):
    """Get, update or delete a watchlist."""
    try:
        watchlist = Watchlist.objects.get(id=watchlist_id, user=request.user)
    except Watchlist.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Watchlist not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = WatchlistSerializer(watchlist)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    elif request.method == 'PUT':
        serializer = WatchlistCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        watchlist.name = serializer.validated_data.get('name', watchlist.name)
        watchlist.is_default = serializer.validated_data.get('is_default', watchlist.is_default)
        watchlist.save()
        
        return Response({
            'success': True,
            'message': 'Watchlist updated successfully',
            'data': WatchlistSerializer(watchlist).data
        })
    
    elif request.method == 'DELETE':
        watchlist.delete()
        return Response({
            'success': True,
            'message': 'Watchlist deleted successfully'
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def watchlist_add_scrip_view(request, watchlist_id):
    """Add a scrip to watchlist."""
    try:
        watchlist = Watchlist.objects.get(id=watchlist_id, user=request.user)
    except Watchlist.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Watchlist not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = WatchlistAddScripSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        scrip = Scrip.objects.get(id=serializer.validated_data['scrip_id'])
        watchlist.scrips.add(scrip)
        return Response({
            'success': True,
            'message': 'Scrip added to watchlist',
            'data': WatchlistSerializer(watchlist).data
        })
    except Scrip.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Scrip not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def watchlist_remove_scrip_view(request, watchlist_id):
    """Remove a scrip from watchlist."""
    try:
        watchlist = Watchlist.objects.get(id=watchlist_id, user=request.user)
    except Watchlist.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Watchlist not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = WatchlistAddScripSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        scrip = Scrip.objects.get(id=serializer.validated_data['scrip_id'])
        watchlist.scrips.remove(scrip)
        return Response({
            'success': True,
            'message': 'Scrip removed from watchlist',
            'data': WatchlistSerializer(watchlist).data
        })
    except Scrip.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Scrip not found'
        }, status=status.HTTP_404_NOT_FOUND)


# Scrip Master Data Views

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def scrip_cache_status_view(request):
    """Get scrip master data cache status."""
    cache_status = ScripCache.objects.all()
    serializer = ScripCacheSerializer(cache_status, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def sync_scrip_master_view(request):
    """Sync scrip master data from Kotak."""
    exchange = request.data.get('exchange', 'NSE')
    
    try:
        client = get_kotak_client(request.user)
        
        # Update cache status
        cache_status, created = ScripCache.objects.get_or_create(exchange=exchange)
        cache_status.is_syncing = True
        cache_status.save()
        
        # Fetch master data
        response = client.scrip_master(exchange=exchange)
        
        if response and 'data' in response:
            scrips_data = response['data']
            
            # Process and save scrips
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
            
            return Response({
                'success': True,
                'message': f'Synced {count} scrips',
                'data': ScripCacheSerializer(cache_status).data
            })
        else:
            cache_status.is_syncing = False
            cache_status.save()
            return Response({
                'success': False,
                'message': 'Failed to sync scrip master data',
                'error': response
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Scrip sync error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Historical Data Views

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([MarketDataRateThrottle])
def historical_data_view(request):
    """Get historical OHLCV data."""
    serializer = HistoricalDataRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        client = get_kotak_client(request.user)
        
        data = serializer.validated_data
        response = client.historical_data(
            symbol_token=data['symbol_token'],
            exchange=data['exchange'],
            interval=data['interval'],
            from_date=data['from_date'].strftime('%Y-%m-%d'),
            to_date=data['to_date'].strftime('%Y-%m-%d')
        )
        
        if response and 'data' in response:
            return Response({
                'success': True,
                'data': response['data']
            })
        else:
            return Response({
                'success': False,
                'message': 'Failed to get historical data',
                'error': response
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Historical data error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Index Quotes

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([MarketDataRateThrottle])
def index_quotes_view(request):
    """Get major index quotes."""
    indices = [
        {'name': 'NIFTY 50', 'token': '99926000', 'exchange': 'NSE'},
        {'name': 'NIFTY BANK', 'token': '99926009', 'exchange': 'NSE'},
        {'name': 'SENSEX', 'token': '99919000', 'exchange': 'BSE'},
    ]
    
    results = []
    try:
        client = get_kotak_client(request.user)
        
        for index in indices:
            try:
                response = client.quotes(
                    symbol_token=index['token'],
                    exchange=index['exchange']
                )
                if response and 'data' in response:
                    data = response['data']
                    results.append({
                        'name': index['name'],
                        'last_price': data.get('last_price', 0),
                        'change': data.get('change', 0),
                        'change_percentage': data.get('change_percentage', 0),
                        'open': data.get('open', 0),
                        'high': data.get('high', 0),
                        'low': data.get('low', 0),
                        'previous_close': data.get('close', 0),
                    })
            except Exception as e:
                logger.warning(f"Error fetching {index['name']}: {e}")
                continue
        
        return Response({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Index quotes error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Top Gainers/Losers

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([MarketDataRateThrottle])
def top_gainers_losers_view(request):
    """Get top gainers and losers."""
    exchange = request.query_params.get('exchange', 'NSE')
    limit = int(request.query_params.get('limit', 10))
    
    try:
        # Get quotes ordered by change percentage
        gainers = Quote.objects.filter(
            scrip__exchange=exchange,
            change_percentage__gt=0
        ).order_by('-change_percentage')[:limit]
        
        losers = Quote.objects.filter(
            scrip__exchange=exchange,
            change_percentage__lt=0
        ).order_by('change_percentage')[:limit]
        
        return Response({
            'success': True,
            'data': {
                'gainers': QuoteLiteSerializer(gainers, many=True).data,
                'losers': QuoteLiteSerializer(losers, many=True).data,
            }
        })
        
    except Exception as e:
        logger.error(f"Top gainers/losers error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
