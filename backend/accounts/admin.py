"""
Accounts Admin Configuration
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, LoginHistory, APILog


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Kotak Profile'
    
    readonly_fields = [
        'session_status', 'token_expiry', 'last_login_at',
        'account_balance', 'available_margin', 'used_margin',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Kotak Credentials', {
            'fields': ('consumer_key', 'mobile_number', 'ucc'),
            'description': 'Kotak Neo API credentials (secrets are encrypted)'
        }),
        ('Session', {
            'fields': ('session_status', 'token_expiry', 'last_login_at'),
        }),
        ('Account Balance', {
            'fields': ('account_balance', 'available_margin', 'used_margin'),
        }),
        ('Risk Management', {
            'fields': (
                'max_loss_percentage', 'max_position_size_percentage',
                'enable_margin_check', 'enable_auto_logout', 'auto_logout_minutes'
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin."""
    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'is_kotak_linked', 'is_active', 'date_joined'
    ]
    list_filter = ['is_kotak_linked', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Trading Info', {'fields': ('phone_number', 'is_kotak_linked')}),
    )
    
    inlines = [UserProfileInline]


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """Admin for Login History."""
    list_display = ['user', 'ip_address', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['user', 'ip_address', 'user_agent', 'status', 'message', 'created_at']
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(APILog)
class APILogAdmin(admin.ModelAdmin):
    """Admin for API Logs."""
    list_display = ['endpoint', 'method', 'status_code', 'user', 'created_at']
    list_filter = ['method', 'status_code', 'created_at']
    search_fields = ['endpoint', 'user__username']
    readonly_fields = [
        'user', 'endpoint', 'method', 'request_data',
        'response_data', 'status_code', 'duration_ms', 'created_at'
    ]
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
