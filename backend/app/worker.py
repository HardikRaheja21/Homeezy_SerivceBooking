from celery import Celery
import os
from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "homeezy_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.services.notifications.tasks",
        "app.ai.tasks",
        "app.services.storage.tasks"
    ]
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600, # 1 hour max
    worker_prefetch_multiplier=1,
    task_routes={
        'app.services.notifications.tasks.*': {'queue': 'notifications'},
        'app.ai.tasks.*': {'queue': 'ai'},
        'app.services.storage.tasks.*': {'queue': 'uploads'},
    }
)

# Schedule for periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Example: 'sync-analytics': { 'task': 'app.services.analytics.tasks.aggregate', 'schedule': 3600 }
}
