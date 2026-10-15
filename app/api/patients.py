from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.constants import PATIENT_URL
from app.core.deps import get_current_user, require_role
from app.core.exceptions import Forbidden, PatientNotFound
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.patient import PatientRead
from app.services.patient import PatientService

router = APIRouter(prefix=PATIENT_URL, tags=["patients"])


@router.get("/me", response_model=PatientRead)
def get_my_patient(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return PatientService(db).get_me(current_user)
    except PatientNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[PatientRead])
def list_patients(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.front_desk)),
):
    return PatientService(db).list()


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return PatientService(db).get_by_id(current_user, patient_id)
    except PatientNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Forbidden as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
