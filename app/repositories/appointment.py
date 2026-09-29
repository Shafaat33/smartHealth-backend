from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment


class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, appointment: Appointment) -> Appointment:
        self.db.add(appointment)
        return appointment

    def get_by_id(self, appointment_id: UUID) -> Appointment | None:
        return self.db.get(Appointment, appointment_id)

    def list_all(self) -> list[Appointment]:
        return list(
            self.db.scalars(
                select(Appointment).order_by(Appointment.appointment_time)
            ).all()
        )

    def list_by_patient_id(self, patient_id: UUID) -> list[Appointment]:
        return list(
            self.db.scalars(
                select(Appointment)
                .where(Appointment.patient_id == patient_id)
                .order_by(Appointment.appointment_time)
            ).all()
        )

    def list_by_provider_id(self, provider_id: UUID) -> list[Appointment]:
        return list(
            self.db.scalars(
                select(Appointment)
                .where(Appointment.provider_id == provider_id)
                .order_by(Appointment.appointment_time)
            ).all()
        )
