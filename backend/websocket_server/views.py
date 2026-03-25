"""
WebSocket Server Views
"""
import logging
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def websocket_status_view(request):
    """Get WebSocket server status."""
    return Response({
        'success': True,
        'data': {
            'status': 'active',
            'endpoints': [
                '/ws/market-data/',
                '/ws/order-updates/',
                '/ws/portfolio-updates/'
            ]
        }
    })


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def broadcast_message_view(request):
    """Broadcast message to all connected clients (admin only)."""
    message = request.data.get('message')
    message_type = request.data.get('message_type', 'notification')
    
    if not message:
        return Response({
            'success': False,
            'message': 'Message is required'
        }, status=400)
    
    try:
        channel_layer = get_channel_layer()
        
        # Broadcast to all market data consumers
        async_to_sync(channel_layer.group_send)(
            'broadcast',
            {
                'type': 'broadcast_message',
                'message_type': message_type,
                'message': message
            }
        )
        
        return Response({
            'success': True,
            'message': 'Message broadcasted successfully'
        })
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)
