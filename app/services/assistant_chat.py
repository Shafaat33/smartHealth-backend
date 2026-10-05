from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import ASSISTANT_HISTORY_TURNS
from app.core.exceptions import ConversationNotFound, Forbidden
from app.models.assistant_chat import AiConversation, AiMessage, AiMessageRole
from app.repositories.assistant_chat import AssistantChatRepository


class AssistantChatService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AssistantChatRepository(db)

    def get_conversation_for_user(self, conversation_id: UUID, user_id: UUID) -> AiConversation:
        conversation = self.repo.get_conversation(conversation_id)
        if conversation is None:
            raise ConversationNotFound()
        if conversation.user_id != user_id:
            raise Forbidden()
        return conversation

    def ensure_conversation(
        self, user_id: UUID, conversation_id: UUID | None, first_message: str
    ) -> AiConversation:
        if conversation_id is not None:
            return self.get_conversation_for_user(conversation_id, user_id)
        title = first_message.strip()[:200] or None
        return self.repo.create_conversation(user_id, title=title)

    def list_conversations(self, user_id: UUID) -> list[AiConversation]:
        return self.repo.list_conversations(user_id)

    def list_messages(self, conversation_id: UUID, user_id: UUID) -> list[AiMessage]:
        self.get_conversation_for_user(conversation_id, user_id)
        return self.repo.list_messages(conversation_id)

    def history_for_llm(self, conversation_id: UUID) -> list[dict[str, str]]:
        limit = ASSISTANT_HISTORY_TURNS * 2
        messages = self.repo.recent_messages(conversation_id, limit=limit)
        return [{"role": m.role.value, "content": m.content} for m in messages]

    def record_user_message(self, conversation_id: UUID, content: str) -> AiMessage:
        return self.repo.add_message(conversation_id, AiMessageRole.user, content)

    def record_assistant_message(
        self,
        conversation_id: UUID,
        content: str,
        *,
        intent: str | None,
        latency_ms: int,
        sources: list | None,
        suggestion: dict | None,
        error: str | None = None,
    ) -> AiMessage:
        return self.repo.add_message(
            conversation_id,
            AiMessageRole.assistant,
            content,
            intent=intent,
            latency_ms=latency_ms,
            sources=sources,
            suggestion=suggestion,
            error=error,
        )
