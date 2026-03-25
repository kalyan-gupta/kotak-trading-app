"""
Accounts Views - Authentication and User Management
"""
import logging
from django.utils import timezone
from django.contrib.auth import login, logout
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.authtoken.models import Token
from django_ratelimit.decorators import ratelimit

from .models import User, UserProfile, LoginHistory
from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserProfileSerializer,
    UserProfileUpdateSerializer, LoginSerializer, KotakLoginSerializer,
    TOTPVerifySerializer, SessionStatusSerializer, LoginHistorySerializer,
    ChangePasswordSerializer, DashboardSerializer
)
from .services.kotak_auth import KotakAuthService

logger = logging.getLogger(__name__)


class RegistrationThrottle(AnonRateThrottle):
    rate = '5/hour'


class LoginThrottle(AnonRateThrottle):
    rate = '10/minute'


class UserRegistrationView(generics.CreateAPIView):
    """View for user registration."""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [RegistrationThrottle]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        # Generate auth token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'User registered successfully.'
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@throttle_classes([LoginThrottle])
def login_view(request):
    """View for user login."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = serializer.validated_data['user']
    login(request, user)
    
    # Update last login
    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])
    
    # Generate or get token
    token, created = Token.objects.get_or_create(user=user)
    
    # Log login history
    LoginHistory.objects.create(
        user=user,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        status='success',
        message='Login successful'
    )
    
    return Response({
        'user': UserSerializer(user).data,
        'token': token.key,
        'message': 'Login successful.'
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """View for user logout."""
    user = request.user
    
    # Log logout
    LoginHistory.objects.create(
        user=user,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        status='logout',
        message='User logged out'
    )
    
    # Clear Kotak session if active
    try:
        profile = user.profile
        if profile.session_status == 'active':
            auth_service = KotakAuthService(profile)
            auth_service.logout()
    except Exception as e:
        logger.error(f"Error clearing Kotak session: {e}")
    
    # Delete auth token
    Token.objects.filter(user=user).delete()
    
    logout(request)
    
    return Response({'message': 'Logout successful.'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile_view(request):
    """View to get user profile."""
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    serializer = UserProfileSerializer(profile)
    return Response({
        'user': UserSerializer(user).data,
        'profile': serializer.data
    })


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_profile_view(request):
    """View to update user profile."""
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    serializer = UserProfileUpdateSerializer(
        profile, 
        data=request.data, 
        partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    
    # Update user fields if provided
    user_fields = ['first_name', 'last_name', 'email', 'phone_number']
    for field in user_fields:
        if field in request.data:
            setattr(user, field, request.data[field])
    user.save()
    
    return Response({
        'user': UserSerializer(user).data,
        'profile': UserProfileSerializer(profile).data,
        'message': 'Profile updated successfully.'
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def kotak_login_view(request):
    """View to login with Kotak Neo API."""
    user = request.user
    serializer = KotakLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    data = serializer.validated_data
    
    try:
        # Get or create profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Update credentials
        profile.consumer_key = data['consumer_key']
        profile.consumer_secret = data['consumer_secret']
        profile.mobile_number = data['mobile_number']
        profile.ucc = data['ucc']
        profile.mpin = data['mpin']
        profile.totp_secret = data['totp_secret']
        profile.save()
        
        # Initialize Kotak Auth Service
        auth_service = KotakAuthService(profile)
        
        # Step 1: Generate TOTP and initiate login
        result = auth_service.initiate_login()
        
        if result.get('success'):
            # Store intermediate data in session
            request.session['kotak_login_step'] = 'totp'
            request.session['kotak_auth_data'] = result.get('data', {})
            
            return Response({
                'success': True,
                'message': 'TOTP generated. Please verify with TOTP.',
                'step': 'totp',
                'qr_code': result.get('qr_code'),  # For manual TOTP setup
            })
        else:
            return Response({
                'success': False,
                'message': result.get('message', 'Login initiation failed.'),
                'error': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Kotak login error: {e}")
        return Response({
            'success': False,
            'message': 'An error occurred during login.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_totp_view(request):
    """View to verify TOTP and complete login."""
    user = request.user
    serializer = TOTPVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        profile = user.profile
        auth_service = KotakAuthService(profile)
        
        # Verify TOTP and complete login
        result = auth_service.verify_totp_and_login(
            serializer.validated_data['otp']
        )
        
        if result.get('success'):
            # Update user and profile
            user.is_kotak_linked = True
            user.save(update_fields=['is_kotak_linked'])
            
            # Clear session data
            request.session.pop('kotak_login_step', None)
            request.session.pop('kotak_auth_data', None)
            
            return Response({
                'success': True,
                'message': 'Kotak login successful.',
                'session_status': profile.session_status,
                'token_expiry': profile.token_expiry,
            })
        else:
            return Response({
                'success': False,
                'message': result.get('message', 'TOTP verification failed.'),
                'error': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"TOTP verification error: {e}")
        return Response({
            'success': False,
            'message': 'An error occurred during TOTP verification.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def kotak_logout_view(request):
    """View to logout from Kotak Neo API."""
    user = request.user
    
    try:
        profile = user.profile
        auth_service = KotakAuthService(profile)
        result = auth_service.logout()
        
        user.is_kotak_linked = False
        user.save(update_fields=['is_kotak_linked'])
        
        return Response({
            'success': True,
            'message': 'Logged out from Kotak successfully.',
            'details': result
        })
        
    except Exception as e:
        logger.error(f"Kotak logout error: {e}")
        return Response({
            'success': False,
            'message': 'An error occurred during logout.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def session_status_view(request):
    """View to check Kotak session status."""
    user = request.user
    
    try:
        profile = user.profile
        
        # Check if session needs refresh
        if profile.session_status == 'active' and not profile.is_session_valid():
            profile.session_status = 'expired'
            profile.save(update_fields=['session_status'])
        
        serializer = SessionStatusSerializer(profile)
        return Response({
            'success': True,
            'data': serializer.data,
            'is_valid': profile.is_session_valid()
        })
        
    except UserProfile.DoesNotExist:
        return Response({
            'success': False,
            'message': 'User profile not found.',
            'is_valid': False
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def refresh_session_view(request):
    """View to refresh Kotak session."""
    user = request.user
    
    try:
        profile = user.profile
        auth_service = KotakAuthService(profile)
        result = auth_service.refresh_session()
        
        if result.get('success'):
            return Response({
                'success': True,
                'message': 'Session refreshed successfully.',
                'session_status': profile.session_status,
                'token_expiry': profile.token_expiry,
            })
        else:
            return Response({
                'success': False,
                'message': result.get('message', 'Session refresh failed.'),
                'error': result.get('error')
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Session refresh error: {e}")
        return Response({
            'success': False,
            'message': 'An error occurred during session refresh.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password_view(request):
    """View to change user password."""
    serializer = ChangePasswordSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    
    user = request.user
    user.set_password(serializer.validated_data['new_password'])
    user.save()
    
    # Generate new token
    Token.objects.filter(user=user).delete()
    token, created = Token.objects.get_or_create(user=user)
    
    return Response({
        'success': True,
        'message': 'Password changed successfully.',
        'token': token.key
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def login_history_view(request):
    """View to get user login history."""
    history = LoginHistory.objects.filter(user=request.user)[:50]
    serializer = LoginHistorySerializer(history, many=True)
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_view(request):
    """View to get dashboard data."""
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Get trading statistics
    from trading.models import Order, Position, Trade
    from django.db.models import Sum, Count, Q
    from django.utils import timezone
    from datetime import datetime, time
    
    today = timezone.now().date()
    today_start = datetime.combine(today, time.min)
    today_end = datetime.combine(today, time.max)
    
    open_positions_count = Position.objects.filter(
        user=user, 
        is_open=True
    ).count()
    
    pending_orders_count = Order.objects.filter(
        user=user,
        status__in=['PENDING', 'OPEN', 'AMO']
    ).count()
    
    today_trades = Trade.objects.filter(
        user=user,
        created_at__range=(today_start, today_end)
    )
    
    today_pnl = today_trades.aggregate(
        total_pnl=Sum('realized_pnl')
    )['total_pnl'] or 0
    
    today_trades_count = today_trades.count()
    
    data = {
        'user': UserSerializer(user).data,
        'profile': UserProfileSerializer(profile).data,
        'open_positions_count': open_positions_count,
        'pending_orders_count': pending_orders_count,
        'today_pnl': today_pnl,
        'today_trades_count': today_trades_count,
    }
    
    serializer = DashboardSerializer(data)
    return Response({
        'success': True,
        'data': serializer.data
    })


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
