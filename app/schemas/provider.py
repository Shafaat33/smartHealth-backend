import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProviderCreate(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=8, max_length=72)


class ProviderUpdate(BaseModel):
    pass


class ProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    created_at: datetime
