from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.constants import APPOINTMENT_URL
from app.core.deps import get_current_user, require_role
from app.core.exceptions import (
    AppointmentNotFound,
    AppointmentTimeInPast,
    BookingHoldExpired,
    Forbidden,
    InvalidAppointmentTransition,
    PatientNotFound,
    ProviderNotFound,
    SchedulingUnavailable,
    SlotTaken,
)
from app.core.temporal import signal_booking, start_booking_hold
from app.db.session import get_db
from app.models.enums import AppointmentEventType, UserRole
from app.models.user import User
from app.schemas.appointment import AppointmentAction, AppointmentCreate, AppointmentRead, AppointmentUpdate
from app.services.appointment import AppointmentService

router = APIRouter(prefix=APPOINTMENT_URL, tags=["appointments"])


@router.post("", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.patient)),
):
    service = AppointmentService(db)
    try:
        appointment = service.create(current_user, payload)
    except PatientNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ProviderNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except AppointmentTimeInPast as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SlotTaken as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    try:
        await start_booking_hold(appointment.id)
    except Exception as exc:
        service.release_if_pending(appointment.id, notify=False)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(SchedulingUnavailable()),
        ) from exc

    service.notifications.record(appointment, AppointmentEventType.booked)
    return appointment


@router.get("", response_model=list[AppointmentRead])
def list_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AppointmentService(db).list(current_user)


@router.get("/{appointment_id}", response_model=AppointmentRead)
def get_appointment(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return AppointmentService(db).get_by_id(current_user, appointment_id)
    except AppointmentNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Forbidden as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.patch("/{appointment_id}", response_model=AppointmentRead)
async def update_appointment(
    appointment_id: UUID,
    payload: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AppointmentService(db)
    try:
        appointment, skip_signal = service.prepare_action(
            current_user,
            appointment_id,
            payload.action,
        )
    except AppointmentNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Forbidden as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except InvalidAppointmentTransition as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if skip_signal:
        return appointment

    try:
        await signal_booking(appointment_id, payload.action.value)
    except BookingHoldExpired as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(SchedulingUnavailable()),
        ) from exc

    db.refresh(appointment)
    if payload.action == AppointmentAction.confirm:
        service.notifications.record(appointment, AppointmentEventType.confirmed)
    return appointment
