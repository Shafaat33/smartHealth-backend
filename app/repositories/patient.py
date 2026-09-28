from sqlalchemy.orm import Session

from app.models.patient import Patient


class PatientRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, patient: Patient) -> Patient:
        self.db.add(patient)
        return patient
