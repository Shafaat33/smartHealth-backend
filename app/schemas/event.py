import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.models.appointment import Appointment
from app.models.enums import AppointmentEventType, AppointmentStatus


class AppointmentEvent(BaseModel):
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: AppointmentEventType
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    appointment_id: uuid.UUID
    patient_id: uuid.UUID
    provider_id: uuid.UUID
    appointment_time: datetime
    status: AppointmentStatus


def appointment_event(
    appointment: Appointment,
    event_type: AppointmentEventType,
) -> AppointmentEvent:
    return AppointmentEvent(
        event_type=event_type,
        appointment_id=appointment.id,
        patient_id=appointment.patient_id,
        provider_id=appointment.provider_id,
        appointment_time=appointment.appointment_time,
        status=AppointmentStatus(appointment.status),
    )
