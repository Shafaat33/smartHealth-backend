from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.ai.graph import build_graph
from app.models.user import User


@dataclass(frozen=True)
class StreamEvent:
    name: str
    data: Any


class AssistantService:
    async def stream_answer(self, question: str, user: User) -> AsyncIterator[StreamEvent]:
        """Yields `sources`, optional `suggestion`, `token` events. Caller adds `done`/`error`."""
        sources_sent = False
        suggestion_sent = False
        tokens_sent = False
        initial = {
            "question": question,
            "user_id": str(user.id),
            "user_role": user.role.value,
        }
        async for event in build_graph().astream_events(initial, version="v2"):
            kind = event["event"]
            node = event.get("metadata", {}).get("langgraph_node")
            output = event.get("data", {}).get("output")
            name = event.get("name")

            if kind == "on_chain_end" and isinstance(output, dict):
                if "sources_payload" in output and not sources_sent:
                    sources_sent = True
                    yield StreamEvent("sources", output.get("sources_payload") or [])
                if output.get("suggestion") and not suggestion_sent:
                    suggestion_sent = True
                    yield StreamEvent("suggestion", output["suggestion"])

            if kind == "on_chat_model_stream" and node == "generate":
                chunk = event["data"]["chunk"].content
                if chunk:
                    tokens_sent = True
                    if not sources_sent:
                        sources_sent = True
                        yield StreamEvent("sources", [])
                    yield StreamEvent("token", {"text": chunk})

            if kind == "on_chain_end" and name == "generate":
                if isinstance(output, dict) and output.get("answer") and not tokens_sent:
                    if not sources_sent:
                        sources_sent = True
                        yield StreamEvent("sources", output.get("sources_payload") or [])
                    yield StreamEvent("token", {"text": output["answer"]})

            if kind == "on_chain_end" and name == "safety_check":
                if isinstance(output, dict) and output.get("answer"):
                    if not sources_sent:
                        sources_sent = True
                        yield StreamEvent("sources", [])
                    yield StreamEvent("token", {"text": output["answer"]})

            if kind == "on_chain_end" and name in {"fallback", "clarify", "refuse"}:
                if isinstance(output, dict) and output.get("answer"):
                    if not sources_sent:
                        sources_sent = True
                        yield StreamEvent("sources", output.get("sources_payload") or [])
                    yield StreamEvent("token", {"text": output["answer"]})
