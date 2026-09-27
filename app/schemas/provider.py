import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ---------- Base / shared fields ----------

class ProviderBase(BaseModel):
    user_id: uuid.UUID


# ---------- Create (input, e.g. POST /providers) ----------

class ProviderCreate(ProviderBase):
    pass


# ---------- Update (input, e.g. PATCH /providers/{id}) ----------
# Same reasoning as PatientUpdate: nothing mutable yet besides
# user_id, which shouldn't be reassigned via PATCH. Kept as an
# empty model as a placeholder for future fields (e.g. specialty,
# license_number).

class ProviderUpdate(BaseModel):
    pass


# ---------- Read (output, e.g. GET /providers/{id}) ----------

class ProviderRead(ProviderBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime