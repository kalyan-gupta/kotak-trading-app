"""
Kotak Neo API v2 Authentication Service
"""
import logging
import pyotp
import qrcode
import io
import base64
import requests
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from neo_api_client import NeoAPI

logger = logging.getLogger(__name__)


class KotakAuthService:
    """Service for handling Kotak Neo API authentication."""
    
    def __init__(self, user_profile):
        """
        Initialize Kotak Auth Service.
        
        Args:
            user_profile: UserProfile instance with Kotak credentials
        """
        self.profile = user_profile
        self.credentials = user_profile.get_kotak_credentials()
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Neo API client."""
        try:
            self.client = NeoAPI(
                environment='prod',
                consumer_key=self.credentials.get('consumer_key'),
                access_token=None,
                neo_fin_key=None
            )
            logger.info("Neo API v2 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neo API v2 client: {e}")
            raise
    
    def generate_totp(self):
        """Generate TOTP using the stored secret."""
        try:
            totp_secret = self.credentials.get('totp_secret')
            if not totp_secret:
                raise ValueError("TOTP secret not configured")
            
            totp = pyotp.TOTP(totp_secret)
            otp = totp.now()
            
            # Generate QR code for reference
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            provisioning_uri = totp.provisioning_uri(
                name=self.profile.mobile_number,
                issuer_name=settings.KOTAK_CONFIG.get('TOTP_ISSUER', 'KotakSecurities')
            )
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            # Convert QR code to base64
            img = qr.make_image(fill_color="black", back_color="white")
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            return {
                'success': True,
                'otp': otp,
                'qr_code': f"data:image/png;base64,{qr_base64}",
                'provisioning_uri': provisioning_uri
            }
        except Exception as e:
            logger.error(f"TOTP generation error: {e}")
            return {
                'success': False,
                'message': 'Failed to generate TOTP',
                'error': str(e)
            }
    
    def initiate_login(self):
        """
        Initiate login flow with Kotak Neo API.
        Step 1: Generate TOTP and prepare for authentication
        """
        try:
            # Generate TOTP
            totp_result = self.generate_totp()
            if not totp_result['success']:
                return totp_result
            
            # Store TOTP for verification
            self._pending_totp = totp_result['otp']
            
            return {
                'success': True,
                'message': 'TOTP generated successfully',
                'qr_code': totp_result['qr_code'],
                'data': {
                    'totp': totp_result['otp'],
                    'mobile_number': self.credentials.get('mobile_number'),
                    'ucc': self.credentials.get('ucc'),
                }
            }
            
        except Exception as e:
            logger.error(f"Login initiation error: {e}")
            return {
                'success': False,
                'message': 'Failed to initiate login',
                'error': str(e)
            }
    
    def verify_totp_and_login(self, otp):
        """
        Verify TOTP and complete login with Kotak Neo API.
        
        Args:
            otp: TOTP entered by user
        """
        try:
            mobile_number = self.credentials.get('mobile_number')
            mpin = self.credentials.get('mpin')
            
            if not all([mobile_number, mpin]):
                return {
                    'success': False,
                    'message': 'Missing credentials (mobile number or MPIN)'
                }
            
            # Login with Kotak Neo API v2
            # Step 1: TOTP Login
            totp_login_response = self.client.totp_login(
                mobile_number=mobile_number,
                ucc=ucc,
                totp=otp
            )
            
            logger.info(f"TOTP Login response: {totp_login_response}")
            
            if not totp_login_response or 'data' not in totp_login_response:
                error_msg = totp_login_response.get('message', 'TOTP Login failed') if isinstance(totp_login_response, dict) else 'TOTP Login failed'
                return {
                    'success': False,
                    'message': error_msg,
                    'error': totp_login_response
                }
            
            # Step 2: TOTP Validate (MPIN)
            totp_validate_response = self.client.totp_validate(mpin=mpin)
            
            logger.info(f"TOTP Validate response: {totp_validate_response}")
            
            if not totp_validate_response or 'data' not in totp_validate_response:
                error_msg = totp_validate_response.get('message', 'TOTP Validate failed') if isinstance(totp_validate_response, dict) else 'TOTP Validate failed'
                return {
                    'success': False,
                    'message': error_msg,
                    'error': totp_validate_response
                }
            
            # Use the validate response as the final login response
            login_response = totp_validate_response
            
            if login_response and 'data' in login_response:
                data = login_response['data']
                
                # Update profile with session tokens
                self.profile.access_token = data.get('access_token')
                self.profile.refresh_token = data.get('refresh_token')
                self.profile.session_token = data.get('session_token')
                self.profile.session_status = 'active'
                
                # Set token expiry (typically 1 day)
                expires_in = data.get('expires_in', 86400)
                self.profile.token_expiry = timezone.now() + timedelta(seconds=expires_in)
                self.profile.last_login_at = timezone.now()
                
                # Update account information if available
                if 'account_info' in data:
                    account_info = data['account_info']
                    self.profile.account_balance = account_info.get('account_balance', 0)
                    self.profile.available_margin = account_info.get('available_margin', 0)
                    self.profile.used_margin = account_info.get('used_margin', 0)
                
                self.profile.save()
                
                # Update user status
                self.profile.user.is_kotak_linked = True
                self.profile.user.save()
                
                return {
                    'success': True,
                    'message': 'Login successful',
                    'data': {
                        'session_status': 'active',
                        'token_expiry': self.profile.token_expiry,
                        'account_balance': self.profile.account_balance,
                        'available_margin': self.profile.available_margin,
                    }
                }
            else:
                error_msg = login_response.get('message', 'Login failed') if isinstance(login_response, dict) else 'Login failed'
                return {
                    'success': False,
                    'message': error_msg,
                    'error': login_response
                }
                
        except Exception as e:
            logger.error(f"TOTP verification error: {e}")
            return {
                'success': False,
                'message': 'Failed to verify TOTP and login',
                'error': str(e)
            }
    
    def logout(self):
        """Logout from Kotak Neo API and clear session."""
        try:
            if self.client and self.profile.session_token:
                try:
                    self.client.logout()
                except Exception as e:
                    logger.warning(f"Error during API logout: {e}")
            
            # Clear session data
            self.profile.clear_session()
            
            # Update user status
            self.profile.user.is_kotak_linked = False
            self.profile.user.save()
            
            return {
                'success': True,
                'message': 'Logout successful'
            }
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            # Still clear local session even if API call fails
            self.profile.clear_session()
            return {
                'success': True,
                'message': 'Local session cleared'
            }
    
    def refresh_session(self):
        """Refresh the access token using refresh token."""
        try:
            if not self.profile.refresh_token:
                return {
                    'success': False,
                    'message': 'No refresh token available'
                }
            
            # Use Neo API client to refresh token
            refresh_response = self.client.refresh_token(
                refresh_token=self.profile.refresh_token
            )
            
            if refresh_response and 'data' in refresh_response:
                data = refresh_response['data']
                
                self.profile.access_token = data.get('access_token')
                self.profile.refresh_token = data.get('refresh_token')
                
                expires_in = data.get('expires_in', 86400)
                self.profile.token_expiry = timezone.now() + timedelta(seconds=expires_in)
                self.profile.session_status = 'active'
                self.profile.save()
                
                return {
                    'success': True,
                    'message': 'Session refreshed successfully',
                    'data': {
                        'token_expiry': self.profile.token_expiry,
                    }
                }
            else:
                # If refresh fails, mark session as expired
                self.profile.session_status = 'expired'
                self.profile.save()
                
                return {
                    'success': False,
                    'message': 'Session refresh failed',
                    'error': refresh_response
                }
                
        except Exception as e:
            logger.error(f"Session refresh error: {e}")
            self.profile.session_status = 'expired'
            self.profile.save()
            return {
                'success': False,
                'message': 'Failed to refresh session',
                'error': str(e)
            }
    
    def validate_session(self):
        """Validate current session and refresh if needed."""
        try:
            if not self.profile.is_session_valid():
                if self.profile.refresh_token:
                    return self.refresh_session()
                else:
                    return {
                        'success': False,
                        'message': 'Session expired and no refresh token available'
                    }
            
            return {
                'success': True,
                'message': 'Session is valid',
                'data': {
                    'session_status': self.profile.session_status,
                    'token_expiry': self.profile.token_expiry,
                }
            }
            
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return {
                'success': False,
                'message': 'Session validation failed',
                'error': str(e)
            }
    
    def get_client(self):
        """Get authenticated Neo API client."""
        if not self.profile.is_session_valid():
            validation = self.validate_session()
            if not validation['success']:
                raise Exception("Session is not valid. Please login again.")
        
        # Update client with current access token
        if self.client and self.profile.access_token:
            self.client.set_access_token(self.profile.access_token)
        
        return self.client
