"""
Accounts Signals
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when a new user is created."""
    if created:
        try:
            UserProfile.objects.create(user=instance)
            logger.info(f"Profile created for user: {instance.username}")
        except Exception as e:
            logger.error(f"Error creating profile for user {instance.username}: {e}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved."""
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)
    except Exception as e:
        logger.error(f"Error saving profile for user {instance.username}: {e}")
