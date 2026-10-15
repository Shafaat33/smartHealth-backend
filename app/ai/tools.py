from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from app.ai.router import clamp_date_range
from app.core.config import ASSISTANT_MAX_APPOINTMENTS, CLINIC_TIMEZONE
from app.db.base import SessionLocal
from app.models.enums import AppointmentStatus, UserRole
from app.models.user import User
from app.repositories.provider import ProviderRepository
from app.repositories.user import UserRepository
from app.services.appointment import AppointmentService
from app.services.availability import FreeSlot, free_slots_for_providers


def _load_user(user_id: UUID) -> User:
    with SessionLocal() as db:
        user = UserRepository(db).get_by_id(user_id)
        if user is None:
            raise RuntimeError("User not found")
        return user


def list_my_appointments(user_id: UUID, date_from: date | None, date_to: date | None) -> str:
    user = _load_user(user_id)
    start, end = clamp_date_range(date_from, date_to)
    tz = ZoneInfo(CLINIC_TIMEZONE)
    start_utc = datetime.combine(start, time.min, tzinfo=tz).astimezone(ZoneInfo("UTC"))
    end_utc = datetime.combine(end + timedelta(days=1), time.min, tzinfo=tz).astimezone(
        ZoneInfo("UTC")
    )

    with SessionLocal() as db:
        appointments = AppointmentService(db).list(user)

    upcoming = [
        a
        for a in appointments
        if start_utc <= a.appointment_time < end_utc
        and AppointmentStatus(a.status) not in {AppointmentStatus.canceled}
    ]
    upcoming.sort(key=lambda a: a.appointment_time)
    upcoming = upcoming[:ASSISTANT_MAX_APPOINTMENTS]

    if not upcoming:
        return f"No appointments found between {start.isoformat()} and {end.isoformat()}."

    lines = []
    for a in upcoming:
        local = a.appointment_time.astimezone(tz).strftime("%a %d %b, %H:%M")
        lines.append(
            f"- {local} with {a.provider_name} (status: {a.status.value})"
        )
    return "Your appointments:\n" + "\n".join(lines)


def find_providers_text(specialty) -> tuple[list, str]:
    with SessionLocal() as db:
        providers = ProviderRepository(db).list(specialty=specialty)
    if not providers:
        return [], f"No providers found for specialty {specialty.value}."
    lines = [f"- {p.name} (id={p.id}, specialty={p.specialty.value})" for p in providers]
    return providers, "Providers:\n" + "\n".join(lines)


def find_care_context(
    user_id: UUID,
    specialty,
    date_from: date | None,
    date_to: date | None,
) -> tuple[str, dict | None]:
    providers, provider_text = find_providers_text(specialty)
    start, end = clamp_date_range(date_from, date_to)

    suggestion: dict | None = None
    slot_lines: list[str] = []
    if providers:
        with SessionLocal() as db:
            slots: list[FreeSlot] = free_slots_for_providers(db, providers, start, end)
        for slot in slots:
            slot_lines.append(
                f"- {slot.label_local} with {slot.provider_name} ({slot.specialty})"
            )
        if slots:
            first = slots[0]
            user = _load_user(user_id)
            if user.role == UserRole.patient:
                suggestion = {
                    "type": "book",
                    "provider_id": str(first.provider_id),
                    "provider_name": first.provider_name,
                    "specialty": first.specialty,
                    "appointment_time": first.appointment_time.isoformat(),
                }

    slots_text = (
        "Available slots:\n" + "\n".join(slot_lines)
        if slot_lines
        else f"No free slots found between {start.isoformat()} and {end.isoformat()}."
    )
    return provider_text + "\n\n" + slots_text, suggestion
