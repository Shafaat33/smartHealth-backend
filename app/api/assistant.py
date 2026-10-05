import json
import logging
import time
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.constants import ASSISTANT_URL
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.assistant import AssistantChatRequest
from app.services.assistant import AssistantService, StreamEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix=ASSISTANT_URL, tags=["assistant"])


def _sse(event: StreamEvent) -> str:
    return f"event: {event.name}\ndata: {json.dumps(event.data)}\n\n"


@router.post("/chat")
async def chat(
    payload: AssistantChatRequest,
    current_user: User = Depends(get_current_user),
):
    started = time.perf_counter()
    events = AssistantService().stream_answer(payload.message.strip(), current_user)

    # Pull the first event (sources) before committing to a 200 so retrieval failures become a 503.
    try:
        first = await anext(events)
    except Exception as exc:
        logger.exception("assistant unavailable for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Assistant unavailable",
        ) from exc

    async def body() -> AsyncIterator[str]:
        yield _sse(first)
        try:
            async for event in events:
                yield _sse(event)
        except Exception:
            logger.exception("assistant stream failed for user %s", current_user.id)
            yield _sse(StreamEvent("error", {"detail": "The assistant stopped unexpectedly. Please try again."}))
            return
        latency_ms = round((time.perf_counter() - started) * 1000)
        logger.info("assistant answered user=%s latency_ms=%d", current_user.id, latency_ms)
        yield _sse(StreamEvent("done", {"latency_ms": latency_ms}))

    return StreamingResponse(
        body(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
