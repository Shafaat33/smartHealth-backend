import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AssistantChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: uuid.UUID | None = None


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    created_at: datetime


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    intent: str | None
    latency_ms: int | None
    sources: list[Any] | None
    suggestion: dict[str, Any] | None
    error: str | None
    created_at: datetime
