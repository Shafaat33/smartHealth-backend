import logging

from app.celery_app import celery_app
from app.db.base import SessionLocal
from app.schemas.event import AppointmentEvent
from app.services.analytics import AnalyticsService

logger = logging.getLogger(__name__)


@celery_app.task(name="record_analytics")
def record_analytics(payload: dict) -> str:
    event = AppointmentEvent.model_validate(payload)
    db = SessionLocal()
    try:
        AnalyticsService(db).record(event)
        logger.info(
            "recorded analytics %s for appointment %s",
            event.event_type.value,
            event.appointment_id,
        )
        return event.event_type.value
    finally:
        db.close()
