"""
Accounts Serializers
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile, LoginHistory


class UserSerializer(serializers.ModelSerializer):
    """User serializer for basic user info."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'phone_number', 'is_kotak_linked', 'created_at']
        read_only_fields = ['id', 'created_at', 'is_kotak_linked']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 
                  'first_name', 'last_name', 'phone_number']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile with Kotak credentials."""
    
    # Write-only fields for sensitive data
    mpin = serializers.CharField(write_only=True, required=False)
    totp_secret = serializers.CharField(write_only=True, required=False)
    
    # Read-only fields
    session_status_display = serializers.CharField(
        source='get_session_status_display', 
        read_only=True
    )
    is_session_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'consumer_key', 'consumer_secret', 'mobile_number', 'ucc',
            'mpin', 'totp_secret', 'session_status', 'session_status_display',
            'is_session_valid', 'token_expiry', 'last_login_at',
            'account_balance', 'available_margin', 'used_margin',
            'max_loss_percentage', 'max_position_size_percentage',
            'enable_margin_check', 'enable_auto_logout', 'auto_logout_minutes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'session_status', 'token_expiry', 'last_login_at',
            'account_balance', 'available_margin', 'used_margin',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'consumer_key': {'write_only': True},
            'consumer_secret': {'write_only': True},
        }
    
    def get_is_session_valid(self, obj):
        return obj.is_session_valid()


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    mpin = serializers.CharField(write_only=True, required=False)
    totp_secret = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = UserProfile
        fields = [
            'consumer_key', 'consumer_secret', 'mobile_number', 'ucc',
            'mpin', 'totp_secret', 'max_loss_percentage',
            'max_position_size_percentage', 'enable_margin_check',
            'enable_auto_logout', 'auto_logout_minutes'
        ]
    
    def update(self, instance, validated_data):
        # Handle encrypted fields
        if 'mpin' in validated_data:
            instance.mpin = validated_data.pop('mpin')
        if 'totp_secret' in validated_data:
            instance.totp_secret = validated_data.pop('totp_secret')
        
        return super().update(instance, validated_data)


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        user = authenticate(
            username=attrs['username'],
            password=attrs['password']
        )
        
        if not user:
            raise serializers.ValidationError(
                'Invalid username or password.',
                code='authorization'
            )
        
        if not user.is_active:
            raise serializers.ValidationError(
                'User account is disabled.',
                code='authorization'
            )
        
        attrs['user'] = user
        return attrs


class KotakLoginSerializer(serializers.Serializer):
    """Serializer for Kotak Neo API login."""
    consumer_key = serializers.CharField(required=True)
    consumer_secret = serializers.CharField(required=True, write_only=True)
    mobile_number = serializers.CharField(required=True)
    ucc = serializers.CharField(required=True)
    mpin = serializers.CharField(required=True, write_only=True)
    totp_secret = serializers.CharField(required=True, write_only=True)
    save_credentials = serializers.BooleanField(default=True)


class TOTPVerifySerializer(serializers.Serializer):
    """Serializer for TOTP verification."""
    otp = serializers.CharField(required=True, max_length=6, min_length=6)


class MPINSerializer(serializers.Serializer):
    """Serializer for MPIN validation."""
    mpin = serializers.CharField(required=True, max_length=4, min_length=4)


class SessionStatusSerializer(serializers.ModelSerializer):
    """Serializer for session status."""
    
    class Meta:
        model = UserProfile
        fields = ['session_status', 'token_expiry', 'last_login_at', 
                  'account_balance', 'available_margin', 'used_margin']


class LoginHistorySerializer(serializers.ModelSerializer):
    """Serializer for login history."""
    
    class Meta:
        model = LoginHistory
        fields = ['id', 'ip_address', 'status', 'message', 'created_at']
        read_only_fields = fields


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, 
        write_only=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password": "New password fields didn't match."}
            )
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value


class DashboardSerializer(serializers.Serializer):
    """Serializer for dashboard data."""
    user = UserSerializer()
    profile = UserProfileSerializer()
    open_positions_count = serializers.IntegerField()
    pending_orders_count = serializers.IntegerField()
    today_pnl = serializers.DecimalField(max_digits=15, decimal_places=2)
    today_trades_count = serializers.IntegerField()
