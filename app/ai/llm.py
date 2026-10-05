from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.core.config import CHAT_MODEL, LLM_TIMEOUT_SECONDS, OPENAI_API_KEY


@lru_cache
def get_chat_model() -> ChatOpenAI:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return ChatOpenAI(
        model=CHAT_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0.2,
        timeout=LLM_TIMEOUT_SECONDS,
        max_retries=2,
        streaming=True,
    )
