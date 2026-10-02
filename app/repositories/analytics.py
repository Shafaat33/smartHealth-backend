from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.analytics import AnalyticsDaily, AnalyticsEvent


class AnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_event(self, event_id: UUID) -> AnalyticsEvent | None:
        return self.db.get(AnalyticsEvent, event_id)

    def add_event(self, event_id: UUID) -> AnalyticsEvent:
        row = AnalyticsEvent(event_id=event_id)
        self.db.add(row)
        return row

    def increment_daily(self, day: date, field: str) -> None:
        values = {"day": day, "booked": 0, "completed": 0, "canceled": 0, field: 1}
        stmt = insert(AnalyticsDaily).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[AnalyticsDaily.day],
            set_={field: getattr(AnalyticsDaily, field) + 1},
        )
        self.db.execute(stmt)

    def list_daily(self) -> list[AnalyticsDaily]:
        return list(
            self.db.scalars(select(AnalyticsDaily).order_by(AnalyticsDaily.day)).all()
        )

    def totals(self) -> tuple[int, int, int]:
        row = self.db.execute(
            select(
                func.coalesce(func.sum(AnalyticsDaily.booked), 0),
                func.coalesce(func.sum(AnalyticsDaily.completed), 0),
                func.coalesce(func.sum(AnalyticsDaily.canceled), 0),
            )
        ).one()
        return int(row[0]), int(row[1]), int(row[2])
