"""
Celery Configuration
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trading_project.settings')

# Create Celery app
app = Celery('trading_project')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from installed apps
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    # Refresh Kotak sessions every 30 minutes
    'refresh-kotak-sessions': {
        'task': 'accounts.tasks.refresh_kotak_sessions',
        'schedule': 1800.0,  # 30 minutes
    },
    # Sync scrip master data daily
    'sync-scrip-master': {
        'task': 'market_data.tasks.sync_scrip_master',
        'schedule': crontab(hour=6, minute=0),  # 6:00 AM daily
    },
    # Update quotes every 5 seconds during market hours
    'update-quotes': {
        'task': 'market_data.tasks.update_quotes',
        'schedule': 5.0,
    },
    # Sync order book every 10 seconds
    'sync-order-book': {
        'task': 'trading.tasks.sync_order_book',
        'schedule': 10.0,
    },
    # Calculate P&L every minute
    'calculate-pnl': {
        'task': 'trading.tasks.calculate_pnl',
        'schedule': 60.0,
    },
}

app.conf.timezone = 'Asia/Kolkata'
