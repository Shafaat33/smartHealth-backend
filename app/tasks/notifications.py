import logging

from app.celery_app import celery_app
from app.db.base import SessionLocal
from app.schemas.event import AppointmentEvent
from app.services.notification import NotificationService

logger = logging.getLogger(__name__)


@celery_app.task(name="send_notification")
def send_notification(payload: dict) -> str:
    event = AppointmentEvent.model_validate(payload)
    db = SessionLocal()
    try:
        NotificationService(db).deliver(event)
        logger.info(
            "delivered %s for appointment %s",
            event.event_type.value,
            event.appointment_id,
        )
        return event.event_type.value
    finally:
        db.close()
