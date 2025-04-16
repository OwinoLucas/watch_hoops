import os

from celery import Celery
from celery.signals import setup_logging
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')

app = Celery('watch_hoops')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure task routing
task_routes = {
    # Analytics tasks
    'analytics.tasks.*': {'queue': 'analytics'},
    
    # Real-time tasks should go to a dedicated queue for faster processing
    'analytics.tasks.process_realtime_game_data': {'queue': 'realtime'},
    'analytics.tasks.update_analytics_after_game': {'queue': 'realtime'},
    
    # Prediction tasks
    'analytics.tasks.generate_game_predictions': {'queue': 'predictions'},
    'analytics.tasks.generate_player_predictions': {'queue': 'predictions'},
    
    # Maintenance tasks
    'analytics.tasks.cleanup_old_predictions': {'queue': 'maintenance'},
    'analytics.tasks.consolidate_analytics_data': {'queue': 'maintenance'},
    'analytics.tasks.validate_analytics_integrity': {'queue': 'maintenance'},
}

app.conf.task_routes = task_routes

# Configure error handling
app.conf.task_annotations = {
    '*': {
        'on_failure': lambda self, exc, task_id, args, kwargs, einfo: {
            self.retry(countdown=60 * 5, max_retries=3)  # Retry failed tasks after 5 minutes, max 3 times
        }
    }
}

# Configure task serialization
app.conf.accept_content = ['json']
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'

# Configure message routing
app.conf.task_default_queue = 'default'
app.conf.task_queues = {
    'default': {},
    'analytics': {},
    'realtime': {'routing_key': 'realtime.#'},
    'predictions': {'routing_key': 'predictions.#'},
    'maintenance': {'routing_key': 'maintenance.#'},
}

# Configure task execution settings
app.conf.task_acks_late = True  # Tasks are acknowledged after the task is executed
app.conf.worker_prefetch_multiplier = 1  # Prefetch only one task at a time
app.conf.task_time_limit = 3600  # 1 hour time limit per task
app.conf.task_soft_time_limit = 3000  # Soft limit of 50 minutes

# Configure result backend
app.conf.result_backend = settings.CELERY_RESULT_BACKEND
app.conf.result_expires = 60 * 60 * 24 * 7  # Results expire after 1 week

# Set up scheduled tasks from our tasks.py file
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Import here to avoid circular imports
    from analytics.tasks import (
        update_player_analytics, 
        update_team_analytics, 
        update_team_performance_trends,
        generate_game_predictions,
        generate_player_predictions,
        cleanup_old_predictions,
        consolidate_analytics_data,
        validate_analytics_integrity
    )
    
    from celery.schedules import crontab
    
    # Daily tasks
    sender.add_periodic_task(
        crontab(hour=4, minute=0),  # 4:00 AM every day
        update_player_analytics.s(),
        name='daily_player_analytics_update',
    )
    
    sender.add_periodic_task(
        crontab(hour=4, minute=30),  # 4:30 AM every day
        update_team_analytics.s(),
        name='daily_team_analytics_update',
    )
    
    sender.add_periodic_task(
        crontab(hour=5, minute=0),  # 5:00 AM every day
        update_team_performance_trends.s(),
        name='daily_team_performance_trends_update',
    )
    
    # Game prediction tasks
    sender.add_periodic_task(
        crontab(hour=6, minute=0),  # 6:00 AM every day
        generate_game_predictions.s(days_ahead=7),
        name='daily_game_predictions_update',
    )
    
    sender.add_periodic_task(
        crontab(hour=7, minute=0),  # 7:00 AM every day
        generate_player_predictions.s(days_ahead=3),
        name='daily_player_predictions_update',
    )
    
    # Maintenance tasks
    sender.add_periodic_task(
        crontab(hour=2, minute=0, day_of_week=1),  # 2:00 AM every Monday
        cleanup_old_predictions.s(days=30),
        name='weekly_old_predictions_cleanup',
    )
    
    sender.add_periodic_task(
        crontab(hour=3, minute=0, day_of_week=1),  # 3:00 AM every Monday
        consolidate_analytics_data.s(days=90),
        name='weekly_analytics_data_consolidation',
    )
    
    sender.add_periodic_task(
        crontab(hour=1, minute=0, day_of_week='*/2'),  # 1:00 AM every other day
        validate_analytics_integrity.s(),
        name='biweekly_analytics_integrity_validation',
    )

# Set up custom logging
@setup_logging.connect
def config_loggers(loglevel=None, **kwargs):
    import logging.config
    from django.conf import settings
    
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
            'file': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': 'logs/celery.log',
                'formatter': 'verbose',
            },
        },
        'loggers': {
            'celery': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': True,
            },
            'analytics.tasks': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': True,
            },
        },
    })

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

