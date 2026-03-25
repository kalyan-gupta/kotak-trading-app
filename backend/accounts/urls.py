"""
Accounts URL Configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # User Profile
    path('profile/', views.user_profile_view, name='profile'),
    path('profile/update/', views.update_profile_view, name='profile-update'),
    
    # Kotak Neo API Authentication
    path('kotak/login/', views.kotak_login_view, name='kotak-login'),
    path('kotak/verify-totp/', views.verify_totp_view, name='verify-totp'),
    path('kotak/logout/', views.kotak_logout_view, name='kotak-logout'),
    path('kotak/session-status/', views.session_status_view, name='session-status'),
    path('kotak/refresh-session/', views.refresh_session_view, name='refresh-session'),
    
    # Security
    path('change-password/', views.change_password_view, name='change-password'),
    path('login-history/', views.login_history_view, name='login-history'),
    
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
