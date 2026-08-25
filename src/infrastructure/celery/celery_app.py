from celery import Celery

from src.settings import settings

celery_app = Celery(
    "transaction_service",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
    include=["src.infrastructure.celery.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
