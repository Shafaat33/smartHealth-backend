from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import Specialty

AssistantIntent = Literal[
    "knowledge",
    "my_appointments",
    "find_care",
    "unclear",
    "out_of_scope",
    "emergency",
]


class RouterOutput(BaseModel):
    intent: Literal["knowledge", "my_appointments", "find_care", "unclear", "out_of_scope"]
    specialty: Specialty | None = None
    date_from: date | None = Field(
        default=None,
        description="Start date (clinic timezone) for appointments or availability",
    )
    date_to: date | None = Field(
        default=None,
        description="End date inclusive (clinic timezone)",
    )
    search_query: str = Field(
        description="Standalone question for document search; include symptoms or topic",
    )
