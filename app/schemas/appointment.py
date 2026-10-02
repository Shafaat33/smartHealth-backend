import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AppointmentStatus


class AppointmentAction(str, enum.Enum):
    confirm = "confirm"
    complete = "complete"
    canceled = "canceled"


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
    action: AppointmentAction


class AppointmentReschedule(BaseModel):
    appointment_time: datetime


# ---------- Read (output, e.g. GET /appointments/{id}) ----------

class AppointmentRead(AppointmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    status: AppointmentStatus
    patient_name: str
    provider_name: str
    