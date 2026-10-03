from celery import Celery
from celery.signals import worker_ready
from prometheus_client import start_http_server

from app.core.config import CELERY_METRICS_PORT, REDIS_URL

celery_app = Celery(
    "smarthealth",
    broker=REDIS_URL or "redis://localhost:6379/0",
    backend=REDIS_URL or "redis://localhost:6379/0",
    include=["app.tasks.notifications", "app.tasks.analytics", "app.tasks.ingestion"],
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@worker_ready.connect
def _start_metrics(**_kwargs) -> None:
    start_http_server(CELERY_METRICS_PORT)
