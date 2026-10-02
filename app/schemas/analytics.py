from datetime import date

from pydantic import BaseModel


class BookedOverTime(BaseModel):
    date: date
    booked: int


class AnalyticsRead(BaseModel):
    total_patients: int
    completed_visits: int
    cancellation_rate: float
    booked_over_time: list[BookedOverTime]
