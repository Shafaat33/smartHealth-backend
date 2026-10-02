import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .enums import AppointmentStatus

if TYPE_CHECKING:
    from .patient import Patient
    from .provider import Provider


class Appointment(TimestampMixin, Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[AppointmentStatus] = mapped_column(
        SqlEnum(AppointmentStatus, name="appointment_status"),
        default=AppointmentStatus.pending,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"))
    provider_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("providers.id"))

    patient: Mapped["Patient"] = relationship(back_populates="appointments")
    provider: Mapped["Provider"] = relationship(back_populates="appointments")

    @property
    def patient_name(self) -> str:
        if self.patient is None or self.patient.user is None:
            return ""
        return self.patient.user.name

    @property
    def provider_name(self) -> str:
        if self.provider is None or self.provider.user is None:
            return ""
        return self.provider.user.name

    __table_args__ = (
        Index(
            "uq_provider_slot",
            "provider_id",
            "appointment_time",
            unique=True,
            postgresql_where=text("status NOT IN ('complete', 'canceled')"),
        ),
    )
