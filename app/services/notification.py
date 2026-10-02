import logging

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.kafka import publish_appointment_event
from app.models.appointment import Appointment
from app.models.enums import AppointmentEventType
from app.models.notification import Notification
from app.models.user import User
from app.repositories.notification import NotificationRepository
from app.repositories.patient import PatientRepository
from app.repositories.provider import ProviderRepository
from app.schemas.event import AppointmentEvent, appointment_event
from app.services.analytics import AnalyticsService

logger = logging.getLogger(__name__)

_BODIES = {
    AppointmentEventType.booked: "Your appointment was booked.",
    AppointmentEventType.confirmed: "Your appointment was confirmed.",
    AppointmentEventType.rescheduled: "Your appointment was rescheduled.",
    AppointmentEventType.canceled: "Your appointment was canceled.",
    AppointmentEventType.completed: "Your appointment was completed.",
}


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.notifications = NotificationRepository(db)
        self.patients = PatientRepository(db)
        self.providers = ProviderRepository(db)

    def list_for_user(self, current_user: User) -> list[Notification]:
        return self.notifications.list_by_user_id(current_user.id)

    def record(self, appointment: Appointment, event_type: AppointmentEventType) -> None:
        event = appointment_event(appointment, event_type)
        logger.info("appointment event %s", event.model_dump(mode="json"))
        try:
            publish_appointment_event(event)
        except Exception:
            logger.exception(
                "failed to publish %s for appointment %s",
                event_type.value,
                appointment.id,
            )
        try:
            self.deliver(event)
            AnalyticsService(self.db).record(event)
        except Exception:
            logger.exception(
                "failed to persist %s for appointment %s",
                event_type.value,
                appointment.id,
            )

    def deliver(self, event: AppointmentEvent) -> None:
        body = _BODIES[event.event_type]
        for user_id in self._recipient_user_ids(event.patient_id, event.provider_id):
            if self.notifications.get_by_user_appointment_event(
                user_id,
                event.appointment_id,
                event.event_type,
            ):
                continue
            self.notifications.add(
                Notification(
                    user_id=user_id,
                    appointment_id=event.appointment_id,
                    event_type=event.event_type.value,
                    body=body,
                )
            )
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()

    def _recipient_user_ids(self, patient_id: UUID, provider_id: UUID) -> list[UUID]:
        recipients = []
        patient = self.patients.get_by_id(patient_id)
        if patient is not None:
            recipients.append(patient.user_id)
        provider = self.providers.get_by_id(provider_id)
        if provider is not None:
            recipients.append(provider.user_id)
        return recipients
