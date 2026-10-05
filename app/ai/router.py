from datetime import date, datetime, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.history import format_history_for_router, history_to_messages
from app.ai.llm import get_chat_model
from app.ai.schemas import RouterOutput
from app.ai.tracing import assistant_span
from app.core.config import ASSISTANT_MAX_RANGE_DAYS, CLINIC_TIMEZONE


def _today_clinic() -> date:
    return datetime.now(ZoneInfo(CLINIC_TIMEZONE)).date()


def clamp_date_range(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    today = _today_clinic()
    start = date_from or today
    end = date_to or (start + timedelta(days=7))
    if start < today:
        start = today
    if end < start:
        end = start
    max_end = today + timedelta(days=ASSISTANT_MAX_RANGE_DAYS)
    if end > max_end:
        end = max_end
    return start, end


@lru_cache
def _router_chain():
    return get_chat_model().with_structured_output(RouterOutput)


async def classify_question(
    question: str,
    history: list[dict[str, str]] | None = None,
) -> RouterOutput:
    today = _today_clinic()
    hist_text = format_history_for_router(history or [])
    system = f"""You route patient messages for SmartHealth clinic assistant.
Today is {today.isoformat()} (clinic timezone {CLINIC_TIMEZONE}).

Recent conversation:
{hist_text}

Choose intent:
- knowledge: clinic info, specialties, test prep, booking FAQ, appointment steps (no live data)
- my_appointments: user asks about their own upcoming/past visits, "my appointments"
- find_care: pick a specialty and/or ask who is available / book / symptoms needing a doctor
- unclear: too vague to act (missing symptom or goal)
- out_of_scope: not healthcare/clinic (coding, weather, jokes, unrelated)

For find_care set specialty to the best matching enum when possible.
Set date_from/date_to when user mentions a day or week (inclusive, clinic dates).
search_query must stand alone for document search (rewrite with symptoms/topics)."""

    messages = [SystemMessage(content=system)]
    messages.extend(history_to_messages(history or []))
    messages.append(HumanMessage(content=question))
    with assistant_span("assistant.router"):
        result = await _router_chain().ainvoke(messages)
    if isinstance(result, RouterOutput):
        return result
    return RouterOutput.model_validate(result)
