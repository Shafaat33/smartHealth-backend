from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import AppointmentEventType
from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, notification: Notification) -> Notification:
        self.db.add(notification)
        return notification

    def get_by_user_appointment_event(
        self,
        user_id: UUID,
        appointment_id: UUID,
        event_type: AppointmentEventType,
    ) -> Notification | None:
        return self.db.scalar(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.appointment_id == appointment_id,
                Notification.event_type == event_type.value,
            )
        )

    def list_by_user_id(self, user_id: UUID) -> list[Notification]:
        return list(
            self.db.scalars(
                select(Notification)
                .where(Notification.user_id == user_id)
                .order_by(Notification.created_at.desc())
            ).all()
        )
