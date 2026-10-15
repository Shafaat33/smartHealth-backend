from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.constants import PROVIDER_URL
from app.core.deps import get_current_user, require_role
from app.core.exceptions import EmailAlreadyExists, ProviderNotFound
from app.db.session import get_db
from app.models.enums import Specialty, UserRole
from app.models.user import User
from app.schemas.provider import ProviderCreate, ProviderRead
from app.services.provider import ProviderService

router = APIRouter(prefix=PROVIDER_URL, tags=["providers"])


@router.post("", response_model=ProviderRead, status_code=status.HTTP_201_CREATED)
def create_provider(
    payload: ProviderCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.front_desk)),
):
    try:
        return ProviderService(db).create(payload)
    except EmailAlreadyExists as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("/me", response_model=ProviderRead)
def get_my_provider(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return ProviderService(db).get_me(current_user)
    except ProviderNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[ProviderRead])
def list_providers(
    specialty: Specialty | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return ProviderService(db).list(specialty=specialty)


@router.get("/{provider_id}", response_model=ProviderRead)
def get_provider(
    provider_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        return ProviderService(db).get_by_id(provider_id)
    except ProviderNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
