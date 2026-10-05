import enum
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SqlEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User


class AiMessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class AiConversation(TimestampMixin, Base):
    __tablename__ = "ai_conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)

    user: Mapped["User"] = relationship()
    messages: Mapped[list["AiMessage"]] = relationship(back_populates="conversation")


class AiMessage(TimestampMixin, Base):
    __tablename__ = "ai_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_conversations.id"), index=True
    )
    role: Mapped[AiMessageRole] = mapped_column(SqlEnum(AiMessageRole, name="ai_message_role"))
    content: Mapped[str] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(32), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sources: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    suggestion: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    conversation: Mapped["AiConversation"] = relationship(back_populates="messages")
