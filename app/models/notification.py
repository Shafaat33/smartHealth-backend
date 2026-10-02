import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .appointment import Appointment
    from .user import User


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    appointment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("appointments.id"))
    event_type: Mapped[str] = mapped_column(String)
    body: Mapped[str]

    user: Mapped["User"] = relationship()
    appointment: Mapped["Appointment"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "appointment_id",
            "event_type",
            name="uq_notification_user_event",
        ),
    )
