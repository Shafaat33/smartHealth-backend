from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import Forbidden, PatientNotFound
from app.models.enums import UserRole
from app.models.patient import Patient
from app.models.user import User
from app.repositories.patient import PatientRepository


class PatientService:
    def __init__(self, db: Session):
        self.patients = PatientRepository(db)

    def get_me(self, current_user: User) -> Patient:
        patient = self.patients.get_by_user_id(current_user.id)
        if patient is None:
            raise PatientNotFound()
        return patient

    def get_by_id(self, current_user: User, patient_id: UUID) -> Patient:
        patient = self.patients.get_by_id(patient_id)
        if patient is None:
            raise PatientNotFound()

        is_owner = patient.user_id == current_user.id
        is_front_desk = current_user.role == UserRole.front_desk
        if not is_owner and not is_front_desk:
            raise Forbidden()

        return patient

    def list(self) -> list[Patient]:
        return self.patients.list()
