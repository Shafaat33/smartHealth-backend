from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assistant_chat import AiConversation, AiMessage, AiMessageRole


class AssistantChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_conversation(self, user_id: UUID, title: str | None = None) -> AiConversation:
        conversation = AiConversation(user_id=user_id, title=title)
        self.db.add(conversation)
        self.db.flush()
        return conversation

    def get_conversation(self, conversation_id: UUID) -> AiConversation | None:
        return self.db.get(AiConversation, conversation_id)

    def list_conversations(self, user_id: UUID) -> list[AiConversation]:
        return list(
            self.db.scalars(
                select(AiConversation)
                .where(AiConversation.user_id == user_id)
                .order_by(AiConversation.created_at.desc())
            ).all()
        )

    def list_messages(self, conversation_id: UUID) -> list[AiMessage]:
        return list(
            self.db.scalars(
                select(AiMessage)
                .where(AiMessage.conversation_id == conversation_id)
                .order_by(AiMessage.created_at)
            ).all()
        )

    def recent_messages(self, conversation_id: UUID, limit: int) -> list[AiMessage]:
        rows = list(
            self.db.scalars(
                select(AiMessage)
                .where(AiMessage.conversation_id == conversation_id)
                .order_by(AiMessage.created_at.desc())
                .limit(limit)
            ).all()
        )
        rows.reverse()
        return rows

    def add_message(
        self,
        conversation_id: UUID,
        role: AiMessageRole,
        content: str,
        *,
        intent: str | None = None,
        latency_ms: int | None = None,
        sources: list | None = None,
        suggestion: dict | None = None,
        error: str | None = None,
    ) -> AiMessage:
        message = AiMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            intent=intent,
            latency_ms=latency_ms,
            sources=sources,
            suggestion=suggestion,
            error=error,
        )
        self.db.add(message)
        self.db.flush()
        return message
