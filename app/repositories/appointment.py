from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus
from app.models.patient import Patient
from app.models.provider import Provider

_WITH_NAMES = (
    joinedload(Appointment.patient).joinedload(Patient.user),
    joinedload(Appointment.provider).joinedload(Provider.user),
)


class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, appointment: Appointment) -> Appointment:
        self.db.add(appointment)
        return appointment

    def get_by_id(self, appointment_id: UUID) -> Appointment | None:
        return self.db.scalar(
            select(Appointment)
            .options(*_WITH_NAMES)
            .where(Appointment.id == appointment_id)
        )

    def get_active_by_provider_and_time(
        self,
        provider_id: UUID,
        appointment_time: datetime,
    ) -> Appointment | None:
        return self.db.scalar(
            select(Appointment).where(
                Appointment.provider_id == provider_id,
                Appointment.appointment_time == appointment_time,
                Appointment.status.notin_(
                    [AppointmentStatus.complete, AppointmentStatus.canceled]
                ),
            )
        )

    def list_all(self) -> list[Appointment]:
        return list(
            self.db.scalars(
                select(Appointment)
                .options(*_WITH_NAMES)
                .order_by(Appointment.appointment_time)
            ).unique()
            .all()
        )

    def list_by_patient_id(self, patient_id: UUID) -> list[Appointment]:
        return list(
            self.db.scalars(
                select(Appointment)
                .options(*_WITH_NAMES)
                .where(Appointment.patient_id == patient_id)
                .order_by(Appointment.appointment_time)
            ).unique()
            .all()
        )

    def list_by_provider_id(self, provider_id: UUID) -> list[Appointment]:
        return list(
            self.db.scalars(
                select(Appointment)
                .options(*_WITH_NAMES)
                .where(Appointment.provider_id == provider_id)
                .order_by(Appointment.appointment_time)
            ).unique()
            .all()
        )
