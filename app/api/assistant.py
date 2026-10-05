import json
import logging
import time
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.constants import ASSISTANT_URL
from app.core.deps import get_current_user
from app.core.exceptions import ConversationNotFound, Forbidden
from app.core.metrics import ai_llm_errors_total, ai_questions_total, ai_response_seconds
from app.db.session import get_db
from app.models.user import User
from app.schemas.assistant import AssistantChatRequest, ConversationRead, MessageRead
from app.services.assistant import AssistantRun, AssistantService, StreamEvent
from app.services.assistant_chat import AssistantChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix=ASSISTANT_URL, tags=["assistant"])


def _sse(event: StreamEvent) -> str:
    return f"event: {event.name}\ndata: {json.dumps(event.data)}\n\n"


@router.get("/conversations", response_model=list[ConversationRead])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AssistantChatService(db).list_conversations(current_user.id)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageRead])
def list_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return AssistantChatService(db).list_messages(conversation_id, current_user.id)
    except ConversationNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Forbidden as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/chat")
async def chat(
    payload: AssistantChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    started = time.perf_counter()
    chat_store = AssistantChatService(db)
    message = payload.message.strip()
    run = AssistantRun()

    try:
        conversation = chat_store.ensure_conversation(
            current_user.id, payload.conversation_id, message
        )
        history = chat_store.history_for_llm(conversation.id)
        chat_store.record_user_message(conversation.id, message)
        db.commit()
    except ConversationNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Forbidden as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    events = AssistantService().stream_answer(message, current_user, history, run)

    try:
        first = await anext(events)
    except Exception as exc:
        logger.exception("assistant unavailable for user %s", current_user.id)
        ai_llm_errors_total.labels(stage="unavailable").inc()
        ai_questions_total.labels(intent=run.intent, status="unavailable").inc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Assistant unavailable",
        ) from exc

    async def body() -> AsyncIterator[str]:
        stream_error: str | None = None
        yield _sse(first)
        try:
            async for event in events:
                yield _sse(event)
        except Exception:
            logger.exception("assistant stream failed for user %s", current_user.id)
            stream_error = "The assistant stopped unexpectedly. Please try again."
            ai_llm_errors_total.labels(stage="stream").inc()
            yield _sse(StreamEvent("error", {"detail": stream_error}))
        latency_ms = round((time.perf_counter() - started) * 1000)
        status_label = "error" if stream_error else "ok"
        ai_questions_total.labels(intent=run.intent, status=status_label).inc()
        ai_response_seconds.labels(intent=run.intent).observe(latency_ms / 1000)

        assistant_message = chat_store.record_assistant_message(
            conversation.id,
            run.answer_text or stream_error or "",
            intent=run.intent,
            latency_ms=latency_ms,
            sources=run.sources or None,
            suggestion=run.suggestion,
            error=stream_error,
        )
        db.commit()
        logger.info(
            "assistant answered user=%s conversation=%s intent=%s latency_ms=%d",
            current_user.id,
            conversation.id,
            run.intent,
            latency_ms,
        )
        yield _sse(
            StreamEvent(
                "done",
                {
                    "latency_ms": latency_ms,
                    "conversation_id": str(conversation.id),
                    "message_id": str(assistant_message.id),
                },
            )
        )

    return StreamingResponse(
        body(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
