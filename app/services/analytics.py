from datetime import timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import AppointmentEventType
from app.repositories.analytics import AnalyticsRepository
from app.repositories.patient import PatientRepository
from app.schemas.analytics import AnalyticsRead, BookedOverTime
from app.schemas.event import AppointmentEvent

_COUNTABLE = {
    AppointmentEventType.booked: "booked",
    AppointmentEventType.completed: "completed",
    AppointmentEventType.canceled: "canceled",
}


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.analytics = AnalyticsRepository(db)
        self.patients = PatientRepository(db)

    def record(self, event: AppointmentEvent) -> None:
        field = _COUNTABLE.get(event.event_type)
        if field is None:
            return
        if self.analytics.get_event(event.event_id) is not None:
            return

        day = event.occurred_at
        if day.tzinfo is None:
            day = day.replace(tzinfo=timezone.utc)
        day = day.astimezone(timezone.utc).date()

        self.analytics.add_event(event.event_id)
        try:
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            return

        self.analytics.increment_daily(day, field)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()

    def snapshot(self) -> AnalyticsRead:
        booked, completed, canceled = self.analytics.totals()
        rate = (canceled / booked) if booked else 0.0
        return AnalyticsRead(
            total_patients=self.patients.count(),
            completed_visits=completed,
            cancellation_rate=rate,
            booked_over_time=[
                BookedOverTime(date=row.day, booked=row.booked)
                for row in self.analytics.list_daily()
            ],
        )
