from uuid import UUID

from temporalio import activity

from app.db.base import SessionLocal
from app.services.appointment import AppointmentService


@activity.defn
async def release_slot_if_pending(appointment_id: str) -> str:
    db = SessionLocal()
    try:
        AppointmentService(db).release_if_pending(UUID(appointment_id))
        return appointment_id
    finally:
        db.close()
