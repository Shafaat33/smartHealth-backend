from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    AppointmentNotFound,
    AppointmentTimeInPast,
    Forbidden,
    InvalidAppointmentTransition,
    PatientNotFound,
    ProviderNotFound,
    SlotTaken,
)
from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus, UserRole
from app.models.user import User
from app.repositories.appointment import AppointmentRepository
from app.repositories.patient import PatientRepository
from app.repositories.provider import ProviderRepository
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate

ALLOWED_STATUS_TRANSITIONS = {
    AppointmentStatus.pending: {AppointmentStatus.complete, AppointmentStatus.canceled},
    AppointmentStatus.complete: set(),
    AppointmentStatus.canceled: set(),
}


class AppointmentService:
    def __init__(self, db: Session):
        self.db = db
        self.appointments = AppointmentRepository(db)
        self.patients = PatientRepository(db)
        self.providers = ProviderRepository(db)

    def create(self, current_user: User, payload: AppointmentCreate) -> Appointment:
        patient = self.patients.get_by_user_id(current_user.id)
        if patient is None:
            raise PatientNotFound()

        provider = self.providers.get_by_id(payload.provider_id)
        if provider is None:
            raise ProviderNotFound()

        appointment_time = payload.appointment_time
        if appointment_time.tzinfo is None:
            appointment_time = appointment_time.replace(tzinfo=timezone.utc)
        if appointment_time <= datetime.now(timezone.utc):
            raise AppointmentTimeInPast()

        existing = self.appointments.get_active_by_provider_and_time(
            provider.id,
            appointment_time,
        )
        if existing is not None:
            raise SlotTaken()

        appointment = Appointment(
            appointment_time=appointment_time,
            provider_id=provider.id,
            patient_id=patient.id,
            status=AppointmentStatus.pending,
        )
        self.appointments.add(appointment)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise SlotTaken() from None
        self.db.refresh(appointment)
        return appointment

    def release_if_pending(self, appointment_id: UUID) -> None:
        appointment = self.appointments.get_by_id(appointment_id)
        if appointment is None:
            return
        if AppointmentStatus(appointment.status) != AppointmentStatus.pending:
            return
        appointment.status = AppointmentStatus.canceled
        self.db.commit()

    def list(self, current_user: User) -> list[Appointment]:
        if current_user.role == UserRole.front_desk:
            return self.appointments.list_all()

        if current_user.role == UserRole.patient:
            patient = self.patients.get_by_user_id(current_user.id)
            if patient is None:
                return []
            return self.appointments.list_by_patient_id(patient.id)

        provider = self.providers.get_by_user_id(current_user.id)
        if provider is None:
            return []
        return self.appointments.list_by_provider_id(provider.id)

    def get_by_id(self, current_user: User, appointment_id: UUID) -> Appointment:
        appointment = self.appointments.get_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFound()

        if current_user.role == UserRole.front_desk:
            return appointment

        if current_user.role == UserRole.patient:
            patient = self.patients.get_by_user_id(current_user.id)
            if patient is None or patient.id != appointment.patient_id:
                raise Forbidden()
            return appointment

        provider = self.providers.get_by_user_id(current_user.id)
        if provider is None or provider.id != appointment.provider_id:
            raise Forbidden()
        return appointment

    def update_status(
        self,
        current_user: User,
        appointment_id: UUID,
        payload: AppointmentUpdate,
    ) -> Appointment:
        appointment = self.appointments.get_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFound()

        if current_user.role == UserRole.front_desk:
            allowed = True
        elif current_user.role == UserRole.provider:
            provider = self.providers.get_by_user_id(current_user.id)
            allowed = provider is not None and provider.id == appointment.provider_id
        else:
            allowed = False

        if not allowed:
            raise Forbidden()

        current_status = AppointmentStatus(appointment.status)
        new_status = AppointmentStatus(payload.status)
        if current_status == new_status:
            return appointment

        if new_status not in ALLOWED_STATUS_TRANSITIONS[current_status]:
            raise InvalidAppointmentTransition(current_status.value, new_status.value)

        appointment.status = new_status
        self.db.commit()
        self.db.refresh(appointment)
        return appointment
