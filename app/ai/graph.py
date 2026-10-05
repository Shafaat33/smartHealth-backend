import asyncio
from functools import lru_cache
from typing import Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.ai.llm import get_chat_model
from app.ai.prompts import NO_CONTEXT_REPLY, SYSTEM_PROMPT, format_context
from app.services.retrieval import RetrievalService, RetrievedChunk


class AssistantState(TypedDict, total=False):
    question: str
    chunks: list[RetrievedChunk]
    answer: str


async def retrieve(state: AssistantState) -> AssistantState:
    chunks = await asyncio.to_thread(RetrievalService().search, state["question"])
    return {"chunks": chunks}


def route_after_retrieve(state: AssistantState) -> Literal["generate", "fallback"]:
    return "generate" if state["chunks"] else "fallback"


async def generate(state: AssistantState) -> AssistantState:
    messages = [
        SystemMessage(SYSTEM_PROMPT.format(context=format_context(state["chunks"]))),
        HumanMessage(state["question"]),
    ]
    response = await get_chat_model().ainvoke(messages)
    return {"answer": response.content}


async def fallback(state: AssistantState) -> AssistantState:
    return {"answer": NO_CONTEXT_REPLY}


@lru_cache
def build_graph():
    graph = StateGraph(AssistantState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_node("fallback", fallback)
    graph.add_edge(START, "retrieve")
    graph.add_conditional_edges("retrieve", route_after_retrieve)
    graph.add_edge("generate", END)
    graph.add_edge("fallback", END)
    return graph.compile()
