import uuid
from datetime import date

from sqlalchemy import Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AnalyticsDaily(Base):
    __tablename__ = "analytics_daily"

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    booked: Mapped[int] = mapped_column(default=0, server_default="0")
    completed: Mapped[int] = mapped_column(default=0, server_default="0")
    canceled: Mapped[int] = mapped_column(default=0, server_default="0")


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
