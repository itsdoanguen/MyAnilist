import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MyAnilist.settings')

app = Celery('MyAnilist')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django app configs
app.autodiscover_tasks()

# Celery Beat Schedule - Automated tasks
app.conf.beat_schedule = {
    # Schedule notifications for followed anime every 6 hours
    'schedule-anime-notifications': {
        'task': 'src.tasks.anime_notification_tasks.schedule_notifications_task',
        'schedule': 21600.0,  # 6 hours in seconds
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not executed
        }
    },
    
    # Send pending notifications every 15 minutes
    'send-pending-notifications': {
        'task': 'src.tasks.anime_notification_tasks.send_notifications_task',
        'schedule': 900.0,  # 15 minutes in seconds
        'options': {
            'expires': 600,  # Task expires after 10 minutes if not executed
        }
    },
    
    # Cleanup old notifications daily at 2:00 AM
    'cleanup-old-notifications': {
        'task': 'src.tasks.anime_notification_tasks.cleanup_notifications_task',
        'schedule': crontab(hour=2, minute=0),
        'options': {
            'expires': 7200,  # Task expires after 2 hours if not executed
        }
    },
}

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Ho_Chi_Minh',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # Hard time limit: 1 hour
    task_soft_time_limit=3000,  # Soft time limit: 50 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery is working"""
    print(f'Request: {self.request!r}')
