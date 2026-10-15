import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AppointmentEventType


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    appointment_id: uuid.UUID
    event_type: AppointmentEventType
    body: str
    created_at: datetime
