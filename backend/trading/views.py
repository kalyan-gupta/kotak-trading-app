"""
Trading Views - Order and Position Management
"""
import logging
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from django_ratelimit.decorators import ratelimit

from accounts.models import UserProfile
from .models import Order, Position, Trade, OrderBook, TradeBook
from .serializers import (
    OrderSerializer, OrderCreateSerializer, OrderModifySerializer,
    PositionSerializer, PositionUpdateSerializer, ClosePositionSerializer,
    TradeSerializer, OrderBookSerializer, TradeBookSerializer,
    HoldingsSerializer, FundsSerializer, OrderValidationSerializer
)
from .services.kotak_trading import KotakTradingService

logger = logging.getLogger(__name__)


class OrderRateThrottle(UserRateThrottle):
    rate = '100/minute'


class MarketDataRateThrottle(UserRateThrottle):
    rate = '500/minute'


def get_trading_service(user):
    """Get Kotak Trading Service for user."""
    profile = user.profile
    if not profile.is_session_valid():
        raise Exception("Kotak session is not active. Please login.")
    return KotakTradingService(profile)


# Order Views

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([OrderRateThrottle])
def order_list_view(request):
    """Get list of user's orders."""
    orders = Order.objects.filter(user=request.user)
    
    # Filter by status
    status_filter = request.query_params.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Filter by symbol
    symbol = request.query_params.get('symbol')
    if symbol:
        orders = orders.filter(trading_symbol__icontains=symbol)
    
    # Filter by date range
    from_date = request.query_params.get('from')
    to_date = request.query_params.get('to')
    if from_date:
        orders = orders.filter(created_at__date__gte=from_date)
    if to_date:
        orders = orders.filter(created_at__date__lte=to_date)
    
    serializer = OrderSerializer(orders, many=True)
    return Response({
        'success': True,
        'count': orders.count(),
        'data': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def order_detail_view(request, order_id):
    """Get details of a specific order."""
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        serializer = OrderSerializer(order)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([OrderRateThrottle])
def place_order_view(request):
    """Place a new order."""
    serializer = OrderCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        service = get_trading_service(request.user)
        result = service.place_order(serializer.validated_data)
        
        if result.get('success'):
            return Response({
                'success': True,
                'message': result['message'],
                'order_id': result.get('order_id'),
                'local_order_id': result.get('local_order_id'),
                'data': result.get('data')
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'message': result.get('message', 'Order placement failed'),
                'error': result.get('error'),
                'required_margin': result.get('required_margin'),
                'available_margin': result.get('available_margin')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Place order error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([OrderRateThrottle])
def modify_order_view(request, order_id):
    """Modify an existing order."""
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = OrderModifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        service = get_trading_service(request.user)
        result = service.modify_order(order, serializer.validated_data)
        
        if result.get('success'):
            return Response({
                'success': True,
                'message': result['message'],
                'data': result.get('data')
            })
        else:
            return Response({
                'success': False,
                'message': result.get('message', 'Order modification failed'),
                'error': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Modify order error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([OrderRateThrottle])
def cancel_order_view(request, order_id):
    """Cancel an order."""
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        service = get_trading_service(request.user)
        result = service.cancel_order(order)
        
        if result.get('success'):
            return Response({
                'success': True,
                'message': result['message'],
                'data': result.get('data')
            })
        else:
            return Response({
                'success': False,
                'message': result.get('message', 'Order cancellation failed'),
                'error': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Cancel order error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def order_status_view(request, order_id):
    """Get real-time status of an order from Kotak."""
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        service = get_trading_service(request.user)
        result = service.get_order_status(order.order_id)
        
        if result.get('success'):
            return Response({
                'success': True,
                'data': result['data']
            })
        else:
            return Response({
                'success': False,
                'message': result.get('message', 'Failed to get order status'),
                'error': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Get order status error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def validate_order_view(request):
    """Validate order before placement."""
    serializer = OrderCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        service = get_trading_service(request.user)
        margin_check = service.check_margin(serializer.validated_data)
        
        warnings = []
        
        # Check position limits
        profile = request.user.profile
        if profile.enable_margin_check:
            max_position = profile.max_position_size_percentage
            # Add position limit check logic here
        
        return Response({
            'success': True,
            'data': {
                'is_valid': margin_check.get('sufficient', False),
                'message': margin_check.get('message', 'Order is valid'),
                'required_margin': margin_check.get('required_margin'),
                'available_margin': margin_check.get('available_margin'),
                'warnings': warnings
            }
        })
        
    except Exception as e:
        logger.error(f"Validate order error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Position Views

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def position_list_view(request):
    """Get list of user's positions."""
    positions = Position.objects.filter(user=request.user)
    
    # Filter by status
    show_closed = request.query_params.get('show_closed', 'false').lower() == 'true'
    if not show_closed:
        positions = positions.filter(is_open=True)
    
    # Filter by symbol
    symbol = request.query_params.get('symbol')
    if symbol:
        positions = positions.filter(trading_symbol__icontains=symbol)
    
    serializer = PositionSerializer(positions, many=True)
    return Response({
        'success': True,
        'count': positions.count(),
        'data': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def position_detail_view(request, position_id):
    """Get details of a specific position."""
    try:
        position = Position.objects.get(id=position_id, user=request.user)
        serializer = PositionSerializer(position)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except Position.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Position not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([OrderRateThrottle])
def close_position_view(request, position_id):
    """Close a position."""
    try:
        position = Position.objects.get(id=position_id, user=request.user)
    except Position.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Position not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = ClosePositionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        service = get_trading_service(request.user)
        result = service.close_position(position, serializer.validated_data)
        
        if result.get('success'):
            return Response({
                'success': True,
                'message': 'Position close order placed successfully',
                'order_id': result.get('order_id'),
                'data': result.get('data')
            })
        else:
            return Response({
                'success': False,
                'message': result.get('message', 'Failed to close position'),
                'error': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Close position error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_position_view(request, position_id):
    """Update position SL/Target."""
    try:
        position = Position.objects.get(id=position_id, user=request.user)
    except Position.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Position not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = PositionUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # Update position
    if 'stop_loss' in serializer.validated_data:
        position.stop_loss = serializer.validated_data['stop_loss']
    if 'target' in serializer.validated_data:
        position.target = serializer.validated_data['target']
    
    position.save()
    
    return Response({
        'success': True,
        'message': 'Position updated successfully',
        'data': PositionSerializer(position).data
    })


# Portfolio Views

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([MarketDataRateThrottle])
def holdings_view(request):
    """Get user's holdings from Kotak."""
    try:
        service = get_trading_service(request.user)
        result = service.get_holdings()
        
        if result.get('success'):
            return Response({
                'success': True,
                'data': result['data']
            })
        else:
            return Response({
                'success': False,
                'message': result.get('message', 'Failed to get holdings'),
                'error': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Get holdings error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([MarketDataRateThrottle])
def funds_view(request):
    """Get user's funds/margin information."""
    try:
        service = get_trading_service(request.user)
        result = service.get_funds()
        
        if result.get('success'):
            return Response({
                'success': True,
                'data': result['data']
            })
        else:
            return Response({
                'success': False,
                'message': result.get('message', 'Failed to get funds'),
                'error': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Get funds error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([MarketDataRateThrottle])
def order_book_view(request):
    """Get order book from Kotak."""
    try:
        service = get_trading_service(request.user)
        result = service.get_order_book()
        
        if result.get('success'):
            return Response({
                'success': True,
                'data': result['data']
            })
        else:
            return Response({
                'success': False,
                'message': result.get('message', 'Failed to get order book'),
                'error': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Get order book error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([MarketDataRateThrottle])
def trade_book_view(request):
    """Get trade book from Kotak."""
    try:
        service = get_trading_service(request.user)
        result = service.get_trade_book()
        
        if result.get('success'):
            return Response({
                'success': True,
                'data': result['data']
            })
        else:
            return Response({
                'success': False,
                'message': result.get('message', 'Failed to get trade book'),
                'error': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Get trade book error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([MarketDataRateThrottle])
def positions_live_view(request):
    """Get live positions from Kotak."""
    try:
        service = get_trading_service(request.user)
        result = service.get_positions()
        
        if result.get('success'):
            return Response({
                'success': True,
                'data': result['data']
            })
        else:
            return Response({
                'success': False,
                'message': result.get('message', 'Failed to get positions'),
                'error': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Get positions error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Trade History

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def trade_history_view(request):
    """Get user's trade history."""
    trades = Trade.objects.filter(user=request.user)
    
    # Filter by date range
    from_date = request.query_params.get('from')
    to_date = request.query_params.get('to')
    if from_date:
        trades = trades.filter(executed_at__date__gte=from_date)
    if to_date:
        trades = trades.filter(executed_at__date__lte=to_date)
    
    # Filter by symbol
    symbol = request.query_params.get('symbol')
    if symbol:
        trades = trades.filter(trading_symbol__icontains=symbol)
    
    serializer = TradeSerializer(trades, many=True)
    return Response({
        'success': True,
        'count': trades.count(),
        'data': serializer.data
    })
