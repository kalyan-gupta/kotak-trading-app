"""
Accounts Models - User and UserProfile for Kotak Trading
"""
import base64
import logging
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


def get_encryption_key():
    """Generate encryption key from settings."""
    key = settings.ENCRYPTION_KEY
    if isinstance(key, str):
        key = key.encode()
    return base64.urlsafe_b64encode(key[:32].ljust(32, b'0'))


def encrypt_data(data: str) -> str:
    """Encrypt sensitive data using Fernet."""
    if not data:
        return ""
    try:
        f = Fernet(get_encryption_key())
        encrypted = f.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        raise


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data using Fernet."""
    if not encrypted_data:
        return ""
    try:
        f = Fernet(get_encryption_key())
        decrypted = f.decrypt(base64.urlsafe_b64decode(encrypted_data.encode()))
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        raise


class User(AbstractUser):
    """Custom User model with additional fields."""
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_kotak_linked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.username


class UserProfile(models.Model):
    """User Profile with Kotak Neo API credentials."""
    
    SESSION_STATUS_CHOICES = [
        ('inactive', 'Inactive'),
        ('active', 'Active'),
        ('expired', 'Expired'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    
    # Kotak Neo API Credentials
    consumer_key = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Kotak Neo Consumer Key"
    )
    consumer_secret = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Kotak Neo Consumer Secret"
    )
    mobile_number = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        help_text="Registered mobile number with Kotak"
    )
    ucc = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="Unique Client Code"
    )
    
    # Encrypted sensitive fields
    _mpin = models.TextField(
        db_column='mpin',
        blank=True, 
        null=True,
        help_text="Encrypted MPIN"
    )
    _totp_secret = models.TextField(
        db_column='totp_secret',
        blank=True, 
        null=True,
        help_text="Encrypted TOTP Secret"
    )
    
    # Session Management
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    session_token = models.TextField(blank=True, null=True)
    session_status = models.CharField(
        max_length=20,
        choices=SESSION_STATUS_CHOICES,
        default='inactive'
    )
    token_expiry = models.DateTimeField(blank=True, null=True)
    last_login_at = models.DateTimeField(blank=True, null=True)
    
    # Account Information (cached from Kotak)
    account_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00
    )
    available_margin = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00
    )
    used_margin = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.00
    )
    
    # Risk Management Settings
    max_loss_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=2.00,
        help_text="Maximum loss percentage per trade"
    )
    max_position_size_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=10.00,
        help_text="Maximum position size as percentage of capital"
    )
    enable_margin_check = models.BooleanField(default=True)
    enable_auto_logout = models.BooleanField(default=True)
    auto_logout_minutes = models.IntegerField(default=30)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.ucc or 'Not Linked'}"
    
    @property
    def mpin(self):
        """Get decrypted MPIN."""
        return decrypt_data(self._mpin) if self._mpin else None
    
    @mpin.setter
    def mpin(self, value):
        """Set encrypted MPIN."""
        self._mpin = encrypt_data(value) if value else None
    
    @property
    def totp_secret(self):
        """Get decrypted TOTP secret."""
        return decrypt_data(self._totp_secret) if self._totp_secret else None
    
    @totp_secret.setter
    def totp_secret(self, value):
        """Set encrypted TOTP secret."""
        self._totp_secret = encrypt_data(value) if value else None
    
    def is_session_valid(self):
        """Check if the current session is valid."""
        from django.utils import timezone
        if self.session_status != 'active':
            return False
        if self.token_expiry and self.token_expiry < timezone.now():
            self.session_status = 'expired'
            self.save(update_fields=['session_status'])
            return False
        return True
    
    def clear_session(self):
        """Clear all session data."""
        self.access_token = None
        self.refresh_token = None
        self.session_token = None
        self.session_status = 'inactive'
        self.token_expiry = None
        self.save(update_fields=[
            'access_token', 'refresh_token', 'session_token',
            'session_status', 'token_expiry'
        ])
    
    def get_kotak_credentials(self):
        """Get Kotak credentials as a dictionary."""
        return {
            'consumer_key': self.consumer_key,
            'consumer_secret': self.consumer_secret,
            'mobile_number': self.mobile_number,
            'ucc': self.ucc,
            'mpin': self.mpin,
            'totp_secret': self.totp_secret,
            'access_token': self.access_token,
        }


class LoginHistory(models.Model):
    """Track user login history for security."""
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('logout', 'Logout'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='login_history'
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'login_history'
        ordering = ['-created_at']
        verbose_name = 'Login History'
        verbose_name_plural = 'Login Histories'
    
    def __str__(self):
        return f"{self.user.username} - {self.status} - {self.created_at}"


class APILog(models.Model):
    """Log API calls for debugging and auditing."""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='api_logs',
        blank=True, 
        null=True
    )
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    request_data = models.JSONField(blank=True, null=True)
    response_data = models.JSONField(blank=True, null=True)
    status_code = models.IntegerField(blank=True, null=True)
    duration_ms = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'api_logs'
        ordering = ['-created_at']
        verbose_name = 'API Log'
        verbose_name_plural = 'API Logs'
    
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status_code}"
