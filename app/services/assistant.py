from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from app.ai.graph import build_graph
from app.core.metrics import ai_retrieval_empty_total, ai_suggestions_total
from app.models.user import User


@dataclass(frozen=True)
class StreamEvent:
    name: str
    data: Any


@dataclass
class AssistantRun:
    intent: str = "unknown"
    sources: list = field(default_factory=list)
    suggestion: dict | None = None
    answer_parts: list[str] = field(default_factory=list)
    retrieval_empty: bool = False

    @property
    def answer_text(self) -> str:
        return "".join(self.answer_parts)


class AssistantService:
    async def stream_answer(
        self,
        question: str,
        user: User,
        history: list[dict[str, str]],
        run: AssistantRun,
    ) -> AsyncIterator[StreamEvent]:
        """Yields `sources`, optional `suggestion`, `token` events. Caller adds `done`/`error`."""
        sources_sent = False
        suggestion_sent = False
        tokens_sent = False
        initial = {
            "question": question,
            "user_id": str(user.id),
            "user_role": user.role.value,
            "history": history,
        }
        async for event in build_graph().astream_events(initial, version="v2"):
            kind = event["event"]
            node = event.get("metadata", {}).get("langgraph_node")
            output = event.get("data", {}).get("output")
            name = event.get("name")

            if kind == "on_chain_end" and name == "router" and isinstance(output, dict):
                run.intent = output.get("intent") or run.intent

            if kind == "on_chain_end" and isinstance(output, dict):
                if "sources_payload" in output and not sources_sent:
                    sources_sent = True
                    payload = output.get("sources_payload") or []
                    run.sources = payload
                    if run.intent == "knowledge" and not payload:
                        run.retrieval_empty = True
                        ai_retrieval_empty_total.inc()
                    yield StreamEvent("sources", payload)
                if output.get("suggestion") and not suggestion_sent:
                    suggestion_sent = True
                    run.suggestion = output["suggestion"]
                    ai_suggestions_total.inc()
                    yield StreamEvent("suggestion", output["suggestion"])

            if kind == "on_chat_model_stream" and node == "generate":
                chunk = event["data"]["chunk"].content
                if chunk:
                    tokens_sent = True
                    run.answer_parts.append(chunk)
                    if not sources_sent:
                        sources_sent = True
                        run.sources = []
                        yield StreamEvent("sources", [])
                    yield StreamEvent("token", {"text": chunk})

            if kind == "on_chain_end" and name == "generate":
                if isinstance(output, dict) and output.get("answer") and not tokens_sent:
                    if not sources_sent:
                        sources_sent = True
                        run.sources = output.get("sources_payload") or []
                        yield StreamEvent("sources", run.sources)
                    run.answer_parts.append(output["answer"])
                    yield StreamEvent("token", {"text": output["answer"]})

            if kind == "on_chain_end" and name == "safety_check":
                if isinstance(output, dict):
                    if output.get("intent"):
                        run.intent = output["intent"]
                    if output.get("answer"):
                        if not sources_sent:
                            sources_sent = True
                            yield StreamEvent("sources", [])
                        run.answer_parts.append(output["answer"])
                        yield StreamEvent("token", {"text": output["answer"]})

            if kind == "on_chain_end" and name in {"fallback", "clarify", "refuse"}:
                if isinstance(output, dict) and output.get("answer"):
                    if not sources_sent:
                        sources_sent = True
                        payload = output.get("sources_payload") or []
                        run.sources = payload
                        yield StreamEvent("sources", payload)
                    run.answer_parts.append(output["answer"])
                    yield StreamEvent("token", {"text": output["answer"]})
