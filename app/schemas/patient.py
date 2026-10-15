import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ---------- Base / shared fields ----------

class PatientBase(BaseModel):
    user_id: uuid.UUID


# ---------- Create (input, e.g. POST /patients) ----------

class PatientCreate(PatientBase):
    pass


# ---------- Update (input, e.g. PATCH /patients/{id}) ----------
# No mutable fields yet — a patient record only links to a user_id,
# and reassigning that isn't a normal operation. Kept as an empty
# model so the shape exists for future fields (e.g. medical notes)
# without breaking route signatures that expect PatientUpdate.

class PatientUpdate(BaseModel):
    pass


# ---------- Read (output, e.g. GET /patients/{id}) ----------

class PatientRead(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime