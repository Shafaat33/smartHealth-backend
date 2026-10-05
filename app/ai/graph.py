import asyncio
from functools import lru_cache
from typing import Literal, TypedDict
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.ai.llm import get_chat_model
from app.ai.prompts import (
    CLARIFY_PROMPT,
    NO_CONTEXT_REPLY,
    OUT_OF_SCOPE_REPLY,
    SYSTEM_PROMPT,
    TOOLS_SYSTEM_PROMPT,
    format_context,
)
from app.ai.router import classify_question, clamp_date_range
from app.ai.safety import EMERGENCY_REPLY, is_emergency
from app.ai.schemas import AssistantIntent
from app.ai.tools import find_care_context, list_my_appointments
from app.models.enums import Specialty
from app.services.retrieval import RetrievalService, RetrievedChunk


class AssistantState(TypedDict, total=False):
    question: str
    user_id: str
    user_role: str
    intent: AssistantIntent
    specialty: str | None
    date_from: str | None
    date_to: str | None
    search_query: str
    chunks: list[RetrievedChunk]
    tool_context: str
    answer: str
    suggestion: dict | None
    sources_payload: list[dict]


async def safety_check(state: AssistantState) -> AssistantState:
    if is_emergency(state["question"]):
        return {
            "intent": "emergency",
            "answer": EMERGENCY_REPLY,
            "sources_payload": [],
        }
    return {}


def route_after_safety(state: AssistantState) -> Literal["router", "finish"]:
    return "finish" if state.get("intent") == "emergency" else "router"


async def router(state: AssistantState) -> AssistantState:
    result = await classify_question(state["question"])
    start, end = clamp_date_range(result.date_from, result.date_to)
    specialty = result.specialty.value if result.specialty else None
    if result.intent == "find_care" and specialty is None:
        specialty = Specialty.family_medicine.value
    return {
        "intent": result.intent,
        "specialty": specialty,
        "date_from": start.isoformat(),
        "date_to": end.isoformat(),
        "search_query": result.search_query or state["question"],
    }


def route_by_intent(state: AssistantState) -> str:
    intent = state.get("intent", "knowledge")
    return {
        "knowledge": "retrieve",
        "my_appointments": "fetch_appointments",
        "find_care": "fetch_care",
        "unclear": "clarify",
        "out_of_scope": "refuse",
    }.get(intent, "retrieve")


async def retrieve(state: AssistantState) -> AssistantState:
    query = state.get("search_query") or state["question"]
    chunks = await asyncio.to_thread(RetrievalService().search, query)
    return {
        "chunks": chunks,
        "sources_payload": [
            {"n": n, "source": c.source, "page": c.page}
            for n, c in enumerate(chunks, start=1)
        ],
    }


def route_after_retrieve(state: AssistantState) -> Literal["generate", "fallback"]:
    return "generate" if state.get("chunks") else "fallback"


async def fetch_appointments(state: AssistantState) -> AssistantState:
    from datetime import date

    date_from = date.fromisoformat(state["date_from"]) if state.get("date_from") else None
    date_to = date.fromisoformat(state["date_to"]) if state.get("date_to") else None
    tool_context = await asyncio.to_thread(
        list_my_appointments, UUID(state["user_id"]), date_from, date_to
    )
    return {"tool_context": tool_context, "chunks": [], "sources_payload": []}


async def fetch_care(state: AssistantState) -> AssistantState:
    from datetime import date

    query = state.get("search_query") or state["question"]
    chunks = await asyncio.to_thread(RetrievalService().search, query)
    specialty = Specialty(state["specialty"]) if state.get("specialty") else Specialty.family_medicine
    date_from = date.fromisoformat(state["date_from"]) if state.get("date_from") else None
    date_to = date.fromisoformat(state["date_to"]) if state.get("date_to") else None
    tool_context, suggestion = await asyncio.to_thread(
        find_care_context, UUID(state["user_id"]), specialty, date_from, date_to
    )
    return {
        "chunks": chunks,
        "tool_context": tool_context,
        "suggestion": suggestion,
        "sources_payload": [
            {"n": n, "source": c.source, "page": c.page}
            for n, c in enumerate(chunks, start=1)
        ],
    }


async def generate_stream_node(state: AssistantState) -> AssistantState:
    if state.get("tool_context"):
        system = TOOLS_SYSTEM_PROMPT.format(
            tool_context=state["tool_context"],
            pdf_context=format_context(state.get("chunks") or []),
        )
    else:
        system = SYSTEM_PROMPT.format(context=format_context(state["chunks"]))
    messages = [SystemMessage(content=system), HumanMessage(content=state["question"])]
    parts: list[str] = []
    async for chunk in get_chat_model().astream(messages):
        text = chunk.content if isinstance(chunk.content, str) else str(chunk.content or "")
        if text:
            parts.append(text)
    return {"answer": "".join(parts)}


async def clarify(state: AssistantState) -> AssistantState:
    messages = [
        SystemMessage(content=CLARIFY_PROMPT),
        HumanMessage(content=state["question"]),
    ]
    response = await get_chat_model().ainvoke(messages)
    content = response.content if isinstance(response.content, str) else str(response.content)
    return {"answer": content, "sources_payload": []}


async def fallback(state: AssistantState) -> AssistantState:
    return {"answer": NO_CONTEXT_REPLY, "sources_payload": []}


async def refuse(state: AssistantState) -> AssistantState:
    return {"answer": OUT_OF_SCOPE_REPLY, "sources_payload": []}


async def finish(state: AssistantState) -> AssistantState:
    return {}


@lru_cache
def build_graph():
    graph = StateGraph(AssistantState)
    graph.add_node("safety_check", safety_check)
    graph.add_node("router", router)
    graph.add_node("retrieve", retrieve)
    graph.add_node("fetch_appointments", fetch_appointments)
    graph.add_node("fetch_care", fetch_care)
    graph.add_node("generate", generate_stream_node)
    graph.add_node("fallback", fallback)
    graph.add_node("clarify", clarify)
    graph.add_node("refuse", refuse)
    graph.add_node("finish", finish)

    graph.add_edge(START, "safety_check")
    graph.add_conditional_edges("safety_check", route_after_safety, {"router": "router", "finish": "finish"})
    graph.add_conditional_edges("router", route_by_intent)
    graph.add_conditional_edges("retrieve", route_after_retrieve, {"generate": "generate", "fallback": "fallback"})
    graph.add_edge("fetch_appointments", "generate")
    graph.add_edge("fetch_care", "generate")
    graph.add_edge("generate", END)
    graph.add_edge("fallback", END)
    graph.add_edge("clarify", END)
    graph.add_edge("refuse", END)
    graph.add_edge("finish", END)
    return graph.compile()
