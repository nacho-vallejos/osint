"""
Celery Application Configuration
Configures Celery with Redis as broker and result backend for async OSINT scanning tasks.
"""
from celery import Celery
from kombu import Exchange, Queue
import os

# Redis connection URL
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery application
celery_app = Celery(
    "osint_platform",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.scan_tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task tracking
    task_track_started=True,
    task_send_sent_event=True,
    
    # Result backend
    result_extended=True,
    result_expires=3600,  # Results expire after 1 hour
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Task routing
    task_default_queue="osint_scans",
    task_queues=(
        Queue(
            "osint_scans",
            Exchange("osint_scans"),
            routing_key="osint.scan",
        ),
        Queue(
            "osint_priority",
            Exchange("osint_priority"),
            routing_key="osint.priority",
            queue_arguments={"x-max-priority": 10},
        ),
    ),
    
    # Task execution
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit
    
    # Retry policy
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Task routes (optional: different queues for different collectors)
celery_app.conf.task_routes = {
    "app.tasks.scan_tasks.perform_osint_scan": {"queue": "osint_scans"},
}

if __name__ == "__main__":
    celery_app.start()
