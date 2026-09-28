import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import AppointmentStatus


# ---------- Base / shared fields ----------

class AppointmentBase(BaseModel):
    appointment_time: datetime
    patient_id: uuid.UUID
    provider_id: uuid.UUID


# ---------- Create (input, e.g. POST /appointments) ----------

class AppointmentCreate(AppointmentBase):
    pass


# ---------- Update (input, e.g. PATCH /appointments/{id}) ----------

class AppointmentUpdate(BaseModel):
    appointment_time: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    patient_id: Optional[uuid.UUID] = None
    provider_id: Optional[uuid.UUID] = None


# ---------- Read (output, e.g. GET /appointments/{id}) ----------

class AppointmentRead(AppointmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    status: AppointmentStatus
    