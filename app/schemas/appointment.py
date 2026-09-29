import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AppointmentStatus


# ---------- Base / shared fields ----------

class AppointmentBase(BaseModel):
    appointment_time: datetime
    patient_id: uuid.UUID
    provider_id: uuid.UUID


# ---------- Create (input, e.g. POST /appointments) ----------
# patient_id is not accepted from the client. The service uses the
# logged-in user's patient profile so a patient cannot book as someone else.

class AppointmentCreate(BaseModel):
    appointment_time: datetime
    provider_id: uuid.UUID


# ---------- Update (input, e.g. PATCH /appointments/{id}) ----------

class AppointmentUpdate(BaseModel):
    status: AppointmentStatus


# ---------- Read (output, e.g. GET /appointments/{id}) ----------

class AppointmentRead(AppointmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    status: AppointmentStatus
    