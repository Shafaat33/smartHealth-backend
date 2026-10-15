import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Specialty


class ProviderCreate(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=8, max_length=72)
    specialty: Specialty
    bio: str | None = Field(default=None, max_length=1000)


class ProviderUpdate(BaseModel):
    pass


class ProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    specialty: Specialty
    bio: str | None
    created_at: datetime
