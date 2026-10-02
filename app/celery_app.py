from celery import Celery

from app.core.config import REDIS_URL

celery_app = Celery(
    "smarthealth",
    broker=REDIS_URL or "redis://localhost:6379/0",
    backend=REDIS_URL or "redis://localhost:6379/0",
    include=["app.tasks.notifications"],
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
