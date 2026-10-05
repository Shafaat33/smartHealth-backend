from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import (
    ASSISTANT_MAX_SLOTS,
    CLINIC_CLOSE,
    CLINIC_DAYS,
    CLINIC_OPEN,
    CLINIC_TIMEZONE,
    SLOT_MINUTES,
)
from app.models.provider import Provider
from app.repositories.appointment import AppointmentRepository


@dataclass(frozen=True)
class FreeSlot:
    provider_id: UUID
    provider_name: str
    specialty: str
    appointment_time: datetime
    label_local: str


def _clinic_weekdays() -> set[int]:
    return {int(part.strip()) for part in CLINIC_DAYS.split(",") if part.strip()}


def _parse_hhmm(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def _slot_starts(day: date, tz: ZoneInfo) -> list[datetime]:
    if day.weekday() not in _clinic_weekdays():
        return []
    open_time = _parse_hhmm(CLINIC_OPEN)
    close_time = _parse_hhmm(CLINIC_CLOSE)
    start_local = datetime.combine(day, open_time, tzinfo=tz)
    end_local = datetime.combine(day, close_time, tzinfo=tz)
    slots: list[datetime] = []
    cursor = start_local
    step = timedelta(minutes=SLOT_MINUTES)
    last_start = end_local - step
    while cursor <= last_start:
        slots.append(cursor.astimezone(ZoneInfo("UTC")))
        cursor += step
    return slots


def free_slots_for_providers(
    db: Session,
    providers: list[Provider],
    range_start: date,
    range_end: date,
) -> list[FreeSlot]:
    if not providers:
        return []
    tz = ZoneInfo(CLINIC_TIMEZONE)
    now_utc = datetime.now(ZoneInfo("UTC"))
    range_end_exclusive = range_end + timedelta(days=1)
    utc_start = datetime.combine(range_start, time.min, tzinfo=tz).astimezone(ZoneInfo("UTC"))
    utc_end = datetime.combine(range_end_exclusive, time.min, tzinfo=tz).astimezone(ZoneInfo("UTC"))

    provider_ids = [p.id for p in providers]
    blocked = AppointmentRepository(db).list_active_times_by_providers(
        provider_ids, utc_start, utc_end
    )

    results: list[FreeSlot] = []
    day = range_start
    while day <= range_end:
        for provider in providers:
            for slot_utc in _slot_starts(day, tz):
                if slot_utc <= now_utc:
                    continue
                if (provider.id, slot_utc) in blocked:
                    continue
                local = slot_utc.astimezone(tz)
                results.append(
                    FreeSlot(
                        provider_id=provider.id,
                        provider_name=provider.name,
                        specialty=provider.specialty.value,
                        appointment_time=slot_utc,
                        label_local=local.strftime("%a %d %b, %H:%M"),
                    )
                )
                if len(results) >= ASSISTANT_MAX_SLOTS:
                    return results
        day += timedelta(days=1)
    return results
