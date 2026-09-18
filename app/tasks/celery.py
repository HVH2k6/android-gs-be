"""
Celery configuration and tasks
"""
from celery import Celery
from app.config import settings

# Initialize Celery
celery = Celery(
    "gs_android_learning",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3000,  # 50 minutes soft limit
)

# Auto-discover tasks
celery.autodiscover_tasks(["app.tasks"])
