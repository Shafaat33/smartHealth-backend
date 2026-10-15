from uuid import UUID

from temporalio import activity
from temporalio.exceptions import ApplicationError

from app.core.exceptions import InvalidAppointmentTransition
from app.db.base import SessionLocal
from app.models.enums import AppointmentStatus
from app.services.appointment import AppointmentService


@activity.defn
async def release_slot_if_pending(appointment_id: str) -> str:
    db = SessionLocal()
    try:
        AppointmentService(db).release_if_pending(UUID(appointment_id))
        return appointment_id
    finally:
        db.close()


@activity.defn
async def apply_appointment_status(appointment_id: str, new_status: str) -> str:
    db = SessionLocal()
    try:
        AppointmentService(db).apply_status(
            UUID(appointment_id),
            AppointmentStatus(new_status),
        )
        return new_status
    except InvalidAppointmentTransition as exc:
        raise ApplicationError(str(exc), non_retryable=True) from exc
    finally:
        db.close()
