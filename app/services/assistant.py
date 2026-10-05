from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from app.ai.graph import build_graph


@dataclass(frozen=True)
class StreamEvent:
    name: str
    data: Any


class AssistantService:
    async def stream_answer(self, question: str) -> AsyncIterator[StreamEvent]:
        """Yields `sources` once, then `token` events. The caller adds `done`/`error`."""
        sources_sent = False
        async for event in build_graph().astream_events({"question": question}, version="v2"):
            kind = event["event"]
            node = event.get("metadata", {}).get("langgraph_node")
            output = event.get("data", {}).get("output")

            if (
                kind == "on_chain_end"
                and event["name"] == "retrieve"
                and isinstance(output, dict)
                and "chunks" in output
                and not sources_sent
            ):
                sources_sent = True
                yield StreamEvent(
                    "sources",
                    [
                        {"n": n, "source": c.source, "page": c.page}
                        for n, c in enumerate(output["chunks"], start=1)
                    ],
                )
            elif kind == "on_chat_model_stream" and node == "generate":
                text = event["data"]["chunk"].content
                if text:
                    yield StreamEvent("token", {"text": text})
            elif (
                kind == "on_chain_end"
                and event["name"] == "fallback"
                and isinstance(output, dict)
                and "answer" in output
            ):
                yield StreamEvent("token", {"text": output["answer"]})
