from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.patient import Patient


class PatientRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, patient: Patient) -> Patient:
        self.db.add(patient)
        return patient

    def get_by_id(self, patient_id: UUID) -> Patient | None:
        return self.db.get(Patient, patient_id)

    def get_by_user_id(self, user_id: UUID) -> Patient | None:
        return self.db.scalar(select(Patient).where(Patient.user_id == user_id))

    def list(self) -> list[Patient]:
        return list(self.db.scalars(select(Patient).order_by(Patient.created_at)).all())
