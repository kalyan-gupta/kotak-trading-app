"""
Celery Tasks for Accounts App
"""
import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from .models import UserProfile
from .services.kotak_auth import KotakAuthService

logger = logging.getLogger(__name__)


@shared_task
def refresh_kotak_sessions():
    """
    Refresh all active Kotak sessions.
    Run every 30 minutes to keep sessions alive.
    """
    logger.info("Starting Kotak session refresh task")
    
    # Get all profiles with active sessions
    profiles = UserProfile.objects.filter(
        session_status='active',
        refresh_token__isnull=False
    )
    
    refreshed_count = 0
    expired_count = 0
    
    for profile in profiles:
        try:
            auth_service = KotakAuthService(profile)
            
            # Check if session needs refresh (expires in less than 1 hour)
            if profile.token_expiry and profile.token_expiry < timezone.now() + timedelta(hours=1):
                result = auth_service.refresh_session()
                
                if result.get('success'):
                    refreshed_count += 1
                    logger.info(f"Refreshed session for user: {profile.user.username}")
                else:
                    expired_count += 1
                    logger.warning(f"Failed to refresh session for user: {profile.user.username}")
        except Exception as e:
            logger.error(f"Error refreshing session for {profile.user.username}: {e}")
            expired_count += 1
    
    logger.info(f"Session refresh complete. Refreshed: {refreshed_count}, Expired: {expired_count}")
    return {
        'refreshed': refreshed_count,
        'expired': expired_count
    }


@shared_task
def cleanup_expired_sessions():
    """
    Clean up expired sessions.
    Run daily to clear stale session data.
    """
    logger.info("Starting expired session cleanup")
    
    expired_profiles = UserProfile.objects.filter(
        session_status='expired'
    )
    
    count = 0
    for profile in expired_profiles:
        try:
            profile.clear_session()
            count += 1
        except Exception as e:
            logger.error(f"Error clearing session for {profile.user.username}: {e}")
    
    logger.info(f"Cleared {count} expired sessions")
    return {'cleared': count}


@shared_task
def notify_session_expiry():
    """
    Notify users of upcoming session expiry.
    Run every hour.
    """
    logger.info("Checking for sessions expiring soon")
    
    # Find sessions expiring in next 2 hours
    expiring_soon = UserProfile.objects.filter(
        session_status='active',
        token_expiry__range=(
            timezone.now(),
            timezone.now() + timedelta(hours=2)
        )
    )
    
    for profile in expiring_soon:
        try:
            # Here you could send email notification
            # or create an in-app notification
            logger.info(f"Session expiring soon for user: {profile.user.username}")
        except Exception as e:
            logger.error(f"Error notifying user {profile.user.username}: {e}")
    
    return {'notified': expiring_soon.count()}
